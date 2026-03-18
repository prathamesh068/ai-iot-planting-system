import time
from typing import List, Optional, Tuple

from backend.contracts import BaseSensors
from backend.services.gpio_service import BaseGPIOManager


class BaseSensorManager(BaseSensors):
    def __init__(self, dht_pins: List[int], ldr_pin: int, soil_pins: List[int], gpio: BaseGPIOManager, logger):
        self.dht_pins = dht_pins
        self.ldr_pin = ldr_pin
        self.soil_pins = soil_pins
        self.gpio = gpio
        self.log = logger

    def read_dht(self, max_retries: int = 5, retry_delay: float = 2.0) -> Tuple[List[Optional[float]], List[Optional[float]]]:
        raise NotImplementedError

    def read_light(self) -> str:
        raise NotImplementedError

    def read_soil(self) -> Tuple[str, str, List[str]]:
        raise NotImplementedError


class RealSensorManager(BaseSensorManager):
    def __init__(self, dht_pins: List[int], ldr_pin: int, soil_pins: List[int], gpio: BaseGPIOManager, logger):
        super().__init__(dht_pins, ldr_pin, soil_pins, gpio, logger)

        import board  # pylint: disable=import-error
        import adafruit_dht  # pylint: disable=import-error

        self._dhts = []
        for pin in self.dht_pins:
            try:
                board_pin = getattr(board, f"D{pin}")
            except AttributeError as exc:
                raise ValueError(f"Invalid DHT pin: BCM {pin}") from exc
            self._dhts.append(adafruit_dht.DHT11(board_pin))

    def _read_single_dht(self, dht_obj, max_retries: int, retry_delay: float) -> Tuple[Optional[float], Optional[float]]:
        for attempt in range(1, max_retries + 1):
            try:
                temp = dht_obj.temperature
                hum = dht_obj.humidity
                if temp is not None and hum is not None:
                    self.log.success("DHT11", f"Read OK: Temp={temp}C Humidity={hum}%")
                    return temp, hum
                raise RuntimeError("Sensor returned None values")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self.log.warning("DHT11", f"Attempt {attempt}/{max_retries} failed: {exc}")
                try:
                    dht_obj.exit()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
                if attempt < max_retries:
                    self.log.debug("DHT11", f"Retrying in {retry_delay}s")
                    time.sleep(retry_delay)
        self.log.error("DHT11", f"All {max_retries} read attempts failed")
        return None, None

    def read_dht(self, max_retries: int = 5, retry_delay: float = 2.0) -> Tuple[List[Optional[float]], List[Optional[float]]]:
        all_temps: List[Optional[float]] = []
        all_hums: List[Optional[float]] = []
        for dht_obj in self._dhts:
            t, h = self._read_single_dht(dht_obj, max_retries, retry_delay)
            all_temps.append(t)
            all_hums.append(h)
        return all_temps, all_hums

    def read_light(self) -> str:
        return "DARK" if self.gpio.read_pin(self.ldr_pin) == 1 else "BRIGHT"

    def read_soil(self) -> Tuple[str, str, List[str]]:
        readings = ["DRY" if self.gpio.read_pin(pin) == 1 else "WET" for pin in self.soil_pins]
        total = len(readings)
        dry_count = readings.count("DRY")
        wet_count = readings.count("WET")
        majority = "DRY" if dry_count >= wet_count else "WET"
        majority_count = dry_count if majority == "DRY" else wet_count
        summary = f"{majority_count}/{total} {majority}"
        return summary, majority, readings


class MockSensorManager(BaseSensorManager):
    def __init__(self, dht_pins: List[int], ldr_pin: int, soil_pins: List[int], gpio: BaseGPIOManager, logger):
        super().__init__(dht_pins, ldr_pin, soil_pins, gpio, logger)

    def read_dht(self, max_retries: int = 5, retry_delay: float = 2.0) -> Tuple[List[Optional[float]], List[Optional[float]]]:
        _ = (max_retries, retry_delay)
        n = max(1, len(self.dht_pins))
        temps: List[Optional[float]] = [round(25.5 + i * 0.5, 1) for i in range(n)]
        hums: List[Optional[float]] = [round(58.0 + i * 1.0, 1) for i in range(n)]
        return temps, hums

    def read_light(self) -> str:
        return "BRIGHT"

    def read_soil(self) -> Tuple[str, str, List[str]]:
        total = max(1, len(self.soil_pins))
        dry_count = (total // 2) + 1
        readings = ["DRY"] * dry_count + ["WET"] * (total - dry_count)
        summary = f"{dry_count}/{total} DRY"
        return summary, "DRY", readings


def create_sensor_manager(is_mock: bool, dht_pins: List[int], ldr_pin: int, soil_pins: List[int], gpio: BaseGPIOManager, logger) -> BaseSensorManager:
    if not is_mock:
        try:
            import board  # noqa: F401  # pylint: disable=import-error
            import adafruit_dht  # noqa: F401  # pylint: disable=import-error
        except ImportError:
            logger.warning("Sensors", "adafruit_dht/board not available on this platform, falling back to mock sensors")
            is_mock = True
    if is_mock:
        return MockSensorManager(dht_pins=dht_pins, ldr_pin=ldr_pin, soil_pins=soil_pins, gpio=gpio, logger=logger)
    return RealSensorManager(dht_pins=dht_pins, ldr_pin=ldr_pin, soil_pins=soil_pins, gpio=gpio, logger=logger)
