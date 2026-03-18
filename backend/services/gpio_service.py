import atexit
from typing import Dict, List

from backend.contracts import BaseGPIO


class BaseGPIOManager(BaseGPIO):
    def __init__(self, ldr_pin: int, soil_pins: List[int], fan_pin: int, pump_pin: int, logger):
        self.ldr_pin = ldr_pin
        self.soil_pins = soil_pins
        self.fan_pin = fan_pin
        self.pump_pin = pump_pin
        self.log = logger

    def fan_on(self) -> None:
        raise NotImplementedError

    def fan_off(self) -> None:
        raise NotImplementedError

    def pump_on(self) -> None:
        raise NotImplementedError

    def pump_off(self) -> None:
        raise NotImplementedError

    def cleanup(self) -> None:
        raise NotImplementedError

    def read_pin(self, pin: int) -> int:
        raise NotImplementedError


class RealGPIOManager(BaseGPIOManager):
    def __init__(self, ldr_pin: int, soil_pins: List[int], fan_pin: int, pump_pin: int, logger):
        super().__init__(ldr_pin, soil_pins, fan_pin, pump_pin, logger)

        import RPi.GPIO as GPIO  # pylint: disable=import-error

        self._gpio = GPIO
        self._gpio.setmode(self._gpio.BCM)

        self._gpio.setup(self.ldr_pin, self._gpio.IN)
        for pin in self.soil_pins:
            self._gpio.setup(pin, self._gpio.IN)

        self._gpio.setup(self.fan_pin, self._gpio.OUT)
        self._gpio.setup(self.pump_pin, self._gpio.OUT)

        self._gpio.output(self.fan_pin, self._gpio.LOW)
        self._gpio.output(self.pump_pin, self._gpio.LOW)

        atexit.register(self.cleanup)

    def fan_on(self) -> None:
        self._gpio.output(self.fan_pin, self._gpio.HIGH)

    def fan_off(self) -> None:
        self._gpio.output(self.fan_pin, self._gpio.LOW)

    def pump_on(self) -> None:
        self._gpio.output(self.pump_pin, self._gpio.HIGH)

    def pump_off(self) -> None:
        self._gpio.output(self.pump_pin, self._gpio.LOW)

    def cleanup(self) -> None:
        self._gpio.output(self.fan_pin, self._gpio.HIGH)
        self._gpio.output(self.pump_pin, self._gpio.HIGH)
        self._gpio.cleanup()

    def read_pin(self, pin: int) -> int:
        return int(self._gpio.input(pin))


class MockGPIOManager(BaseGPIOManager):
    def __init__(self, ldr_pin: int, soil_pins: List[int], fan_pin: int, pump_pin: int, logger):
        super().__init__(ldr_pin, soil_pins, fan_pin, pump_pin, logger)
        self.pin_values: Dict[int, int] = {pin: 0 for pin in soil_pins}
        self.pin_values[self.ldr_pin] = 0
        self.outputs: Dict[int, int] = {self.fan_pin: 0, self.pump_pin: 0}

    def fan_on(self) -> None:
        self.outputs[self.fan_pin] = 1
        self.log.debug("MockGPIO", "fan_on()")

    def fan_off(self) -> None:
        self.outputs[self.fan_pin] = 0
        self.log.debug("MockGPIO", "fan_off()")

    def pump_on(self) -> None:
        self.outputs[self.pump_pin] = 1
        self.log.debug("MockGPIO", "pump_on()")

    def pump_off(self) -> None:
        self.outputs[self.pump_pin] = 0
        self.log.debug("MockGPIO", "pump_off()")

    def cleanup(self) -> None:
        self.outputs[self.fan_pin] = 0
        self.outputs[self.pump_pin] = 0

    def read_pin(self, pin: int) -> int:
        return int(self.pin_values.get(pin, 0))


def create_gpio_manager(is_mock: bool, ldr_pin: int, soil_pins: List[int], fan_pin: int, pump_pin: int, logger) -> BaseGPIOManager:
    if is_mock:
        return MockGPIOManager(ldr_pin=ldr_pin, soil_pins=soil_pins, fan_pin=fan_pin, pump_pin=pump_pin, logger=logger)
    return RealGPIOManager(ldr_pin=ldr_pin, soil_pins=soil_pins, fan_pin=fan_pin, pump_pin=pump_pin, logger=logger)
