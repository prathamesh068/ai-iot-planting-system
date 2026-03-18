import time

from backend.services.gpio_service import BaseGPIOManager


class ActuatorController:
    def __init__(self, gpio: BaseGPIOManager, pump_duration: int = 5):
        self.gpio = gpio
        self.pump_duration = pump_duration

    def apply(self, ai_result, temp, soil_majority):
        actions = []
        rec = ai_result.get("recommendation", {})

        if rec.get("increase_airflow", False) or temp > 30:
            self.gpio.fan_on()
            actions.append("Fan ON")
        else:
            self.gpio.fan_off()

        if rec.get("water_plant", False) and soil_majority == "DRY":
            self.gpio.pump_on()
            time.sleep(self.pump_duration)
            self.gpio.pump_off()
            actions.append(f"Watered ({self.pump_duration}s)")

        return ", ".join(actions) if actions else "None"
