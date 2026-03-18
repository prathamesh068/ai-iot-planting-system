import time
from typing import List, Optional, Tuple

from backend.contracts import BaseSensors
from backend.services.gpio_service import BaseGPIOManager


class BaseSensorManager(BaseSensors):
    def __init__(self, dht_pin: int, ldr_pin: int, soil_pins: List[int], gpio: BaseGPIOManager, logger):
        self.dht_pin = dht_pin
        self.ldr_pin = ldr_pin
        self.soil_pins = soil_pins
        self.gpio = gpio
        self.log = logger

    def read_dht(self, max_retries: int = 5, retry_delay: float = 2.0):
        raise NotImplementedError

    def read_light(self) -> str:
        raise NotImplementedError

    def read_soil(self) -> Tuple[str, str]:
        raise NotImplementedError


class RealSensorManager(BaseSensorManager):
    def __init__(self, dht_pin: int, ldr_pin: int, soil_pins: List[int], gpio: BaseGPIOManager, logger):
        super().__init__(dht_pin, ldr_pin, soil_pins, gpio, logger)

        import board  # pylint: disable=import-error
        import adafruit_dht  # pylint: disable=import-error

        try:
            board_pin = getattr(board, f"D{self.dht_pin}")
        except AttributeError as exc:
            raise ValueError(f"Invalid DHT pin: BCM {self.dht_pin}") from exc

        self._dht = adafruit_dht.DHT11(board_pin)

    def read_dht(self, max_retries: int = 5, retry_delay: float = 2.0):
        for attempt in range(1, max_retries + 1):
            try:
                temp = self._dht.temperature
                hum = self._dht.humidity
                if temp is not None and hum is not None:
                    self.log.success("DHT11", f"Read OK: Temp={temp}C Humidity={hum}%")
                    return temp, hum
                raise RuntimeError("Sensor returned None values")
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self.log.warning("DHT11", f"Attempt {attempt}/{max_retries} failed: {exc}")
                try:
                    self._dht.exit()
                except Exception:  # pylint: disable=broad-exception-caught
                    pass
                if attempt < max_retries:
                    self.log.debug("DHT11", f"Retrying in {retry_delay}s")
                    time.sleep(retry_delay)

        self.log.error("DHT11", f"All {max_retries} read attempts failed")
        return None, None

    def read_light(self) -> str:
        return "DARK" if self.gpio.read_pin(self.ldr_pin) == 1 else "BRIGHT"

    def read_soil(self) -> Tuple[str, str]:
        readings = ["DRY" if self.gpio.read_pin(pin) == 1 else "WET" for pin in self.soil_pins]
        total = len(readings)
        dry_count = readings.count("DRY")
        wet_count = readings.count("WET")
        majority = "DRY" if dry_count >= wet_count else "WET"
        majority_count = dry_count if majority == "DRY" else wet_count
        summary = f"{majority_count}/{total} {majority}"
        return summary, majority


class MockSensorManager(BaseSensorManager):
    def __init__(self, dht_pin: int, ldr_pin: int, soil_pins: List[int], gpio: BaseGPIOManager, logger):
        super().__init__(dht_pin, ldr_pin, soil_pins, gpio, logger)

    def read_dht(self, max_retries: int = 5, retry_delay: float = 2.0):
        _ = (max_retries, retry_delay)
        return 26.5, 58.0

    def read_light(self) -> str:
        return "BRIGHT"

    def read_soil(self) -> Tuple[str, str]:
        total = max(1, len(self.soil_pins))
        dry_count = (total // 2) + 1
        summary = f"{dry_count}/{total} DRY"
        return summary, "DRY"


def create_sensor_manager(is_mock: bool, dht_pin: int, ldr_pin: int, soil_pins: List[int], gpio: BaseGPIOManager, logger) -> BaseSensorManager:
    if is_mock:
        return MockSensorManager(dht_pin=dht_pin, ldr_pin=ldr_pin, soil_pins=soil_pins, gpio=gpio, logger=logger)
    return RealSensorManager(dht_pin=dht_pin, ldr_pin=ldr_pin, soil_pins=soil_pins, gpio=gpio, logger=logger)
