import asyncio
import datetime
from typing import Any, Awaitable, Callable, Optional

from supabase import acreate_client
from supabase.lib.client_options import AsyncClientOptions


REALTIME_TIMEOUT_SECONDS = 30


def _cancel_join_timeout(channel, logger) -> None:
    join_push = getattr(channel, "join_push", None)
    if join_push is None:
        return

    try:
        join_push.destroy()
    except Exception as exc:  # pylint: disable=broad-except
        logger.debug("Realtime", f"Failed to cancel join timeout task: {exc}")


class FrequentCycleRunner:
    def __init__(
        self,
        system,
        logger,
        on_state_change: Callable[[str, bool], Awaitable[None]],
    ):
        self.system = system
        self.log = logger
        self._cycle_lock = asyncio.Lock()
        self._task: Optional[asyncio.Task[None]] = None
        self._on_state_change = on_state_change

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.is_running:
            self.log.info(
                "Command",
                "Reading cycle already running",
            )
            return

        self._task = asyncio.create_task(self._run_cycle())
        await self._on_state_change("running", True)
        self.log.success("Command", "Reading cycle started")

    async def shutdown(self) -> None:
        if self._task and not self._task.done():
            await self._task

    async def _execute_cycle(self) -> None:
        async with self._cycle_lock:
            try:
                await asyncio.to_thread(self.system.run)
            except Exception as exc:  # pylint: disable=broad-except
                self.log.error("Command", f"Cycle execution failed: {exc}")

    async def _run_cycle(self) -> None:
        try:
            self.log.info("Command", "Executing smart plant cycle")
            await self._execute_cycle()
        finally:
            self._task = None
            await self._on_state_change("live", False)


async def listen_for_control_commands(system, settings, logger, channel_name: str) -> None:
    max_retries = 10
    retry_count = 0
    base_retry_delay = 2

    while retry_count < max_retries:
        try:
            await _listen_with_reconnect(system, settings, logger, channel_name)
            retry_count = 0  # Reset on success
        except KeyboardInterrupt:
            logger.info("Realtime", "Command listener stopped by user")
            break
        except Exception as exc:  # pylint: disable=broad-except
            retry_count += 1
            if retry_count >= max_retries:
                logger.error("Realtime", f"Max retries ({max_retries}) exceeded. Giving up.")
                break

            backoff = min(base_retry_delay * (1.5 ** (retry_count - 1)), 60)
            logger.warning(
                "Realtime",
                f"Listener connection failed (retry {retry_count}/{max_retries}, waiting {backoff:.0f}s): {exc}",
            )
            await asyncio.sleep(backoff)


async def _listen_with_reconnect(system, settings, logger, channel_name: str) -> None:
    client = await acreate_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=AsyncClientOptions(
            realtime={
                "auto_reconnect": True,
                "max_retries": 10,
                "initial_backoff": 2.0,
                "timeout": REALTIME_TIMEOUT_SECONDS,
            }
        ),
    )
    ready = asyncio.Event()
    channel_error: Optional[str] = None
    has_subscribed = False

    channel = client.channel(channel_name)

    async def broadcast_device_state(status: str, is_running: bool) -> None:
        try:
            await channel.send_broadcast(
                event="device_heartbeat",
                data={
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "status": status,
                    "is_running": is_running,
                },
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Realtime", f"Device state broadcast failed: {exc}")

    runner = FrequentCycleRunner(system, logger, on_state_change=broadcast_device_state)

    def on_start_reading(payload: dict[str, Any]) -> None:
        _ = payload
        logger.info("Realtime", "Received start_reading command")
        asyncio.create_task(runner.start())

    def on_subscribe(status: Any, err: Optional[Exception]) -> None:
        nonlocal channel_error, has_subscribed
        status_value = getattr(status, "value", str(status))
        logger.info("Realtime", f"Channel subscription status: {status_value}")

        if status_value == "SUBSCRIBED":
            has_subscribed = True
            _cancel_join_timeout(channel, logger)
            ready.set()
            return

        if status_value in {"CHANNEL_ERROR", "TIMED_OUT", "CLOSED"}:
            msg = str(err) if err else f"Channel subscription failed: {status_value}"
            if has_subscribed:
                logger.warning(
                    "Realtime",
                    f"Channel status changed after subscribe: {status_value}. Waiting for client auto-reconnect.",
                )
                return
            logger.error("Realtime", msg)
            channel_error = msg
            ready.set()

    channel.on_broadcast("start_reading", on_start_reading)
    await channel.subscribe(on_subscribe)

    await ready.wait()
    if channel_error:
        raise RuntimeError(channel_error)

    logger.success("Realtime", f"Listening on channel '{channel_name}' for control commands")
    await broadcast_device_state("live", False)

    async def send_heartbeat_loop() -> None:
        while True:
            await broadcast_device_state("running" if runner.is_running else "live", runner.is_running)
            await asyncio.sleep(20)

    heartbeat_task = asyncio.create_task(send_heartbeat_loop())

    wait_forever = asyncio.Event()
    try:
        await wait_forever.wait()
    finally:
        heartbeat_task.cancel()
        try:
            await asyncio.gather(heartbeat_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass
        await runner.shutdown()
        try:
            await client.remove_channel(channel)
        except Exception as exc:  # pylint: disable=broad-except
            logger.debug("Realtime", f"Channel cleanup failed: {exc}")
