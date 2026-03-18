import asyncio

from backend.cli import log_configuration, parse_args
from backend.command_listener import listen_for_control_commands
from backend.config import load_settings
from backend.logger import log
from backend.system import SmartPlantSystem


def main() -> None:
    args = parse_args()
    settings = load_settings(mock_override=args.mock)

    log_configuration(log, args, settings.mock)

    system = SmartPlantSystem(args=args, settings=settings, logger=log)

    if args.listen_commands:
        if settings.mock:
            log.warning("Realtime", "Command listener requires real Supabase mode. Running one cycle in mock mode.")
            system.run()
            return

        if not settings.supabase_url or not settings.supabase_service_role_key:
            log.warning("Realtime", "Supabase credentials missing. Running one cycle instead of command listener.")
            system.run()
            return

        channel_name = args.command_channel or settings.supabase_command_channel

        try:
            asyncio.run(
                listen_for_control_commands(
                    system=system,
                    settings=settings,
                    logger=log,
                    channel_name=channel_name,
                )
            )
        except KeyboardInterrupt:
            log.info("Realtime", "Command listener stopped by user")
        return

    system.run()


if __name__ == "__main__":
    main()
