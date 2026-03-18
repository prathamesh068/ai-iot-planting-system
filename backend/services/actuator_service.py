import json
import time

from backend.services.gpio_service import BaseGPIOManager


class ActuatorController:
    def __init__(self, gpio: BaseGPIOManager, pump_duration: int = 5):
        self.gpio = gpio
        self.pump_duration = pump_duration

    @staticmethod
    def _to_bool(value):
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off", ""}:
                return False
        return bool(value)

    @staticmethod
    def _as_recommendation(ai_result):
        if not isinstance(ai_result, dict):
            return {}

        rec = ai_result.get("recommendation", {})
        if isinstance(rec, dict):
            return rec

        if isinstance(rec, str):
            try:
                parsed = json.loads(rec)
            except json.JSONDecodeError:
                return {}
            if isinstance(parsed, dict):
                return parsed

        return {}

    def apply(self, ai_result, temp, soil_majority):
        actions = []
        rec = self._as_recommendation(ai_result)

        try:
            temp_value = float(temp)
        except (TypeError, ValueError):
            temp_value = 0.0

        if self._to_bool(rec.get("increase_airflow", False)) or temp_value > 30:
            self.gpio.fan_on()
            actions.append("Fan ON")
        else:
            self.gpio.fan_off()

        if self._to_bool(rec.get("water_plant", False)) and str(soil_majority).upper() == "DRY":
            self.gpio.pump_on()
            time.sleep(self.pump_duration)
            self.gpio.pump_off()
            actions.append(f"Watered ({self.pump_duration}s)")

        return ", ".join(actions) if actions else "None"
