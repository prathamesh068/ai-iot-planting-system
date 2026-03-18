import datetime

from backend.config import Settings
from backend.factories import build_services
from backend.services.actuator_service import ActuatorController


class SmartPlantSystem:
    def __init__(self, args, settings: Settings, logger):
        self.args = args
        self.settings = settings
        self.log = logger

        services = build_services(args=args, settings=settings, logger=logger)
        self.gpio = services["gpio"]
        self.sensors = services["sensors"]
        self.camera = services["camera"]
        self.storage = services["storage"]
        self.ai = services["ai"]

        self.actuators = ActuatorController(self.gpio, pump_duration=args.pump_duration)

    def run(self) -> None:
        self.log.section("Smart Plant System - Cycle Start")

        self.gpio.fan_off()
        self.gpio.pump_off()

        self.log.info("Camera", "Capturing image")
        if not self.camera.capture():
            self.log.error("Camera", "Failed to capture valid image. Aborting cycle.")
            return
        self.log.success("Camera", f"Image saved to {self.settings.image_path}")

        self.log.info("Sensors", "Reading sensors")
        temp_readings, hum_readings = self.sensors.read_dht()
        valid_temps = [t for t in temp_readings if t is not None]
        valid_hums = [h for h in hum_readings if h is not None]
        temp = round(sum(valid_temps) / len(valid_temps), 1) if valid_temps else None
        hum = round(sum(valid_hums) / len(valid_hums), 1) if valid_hums else None
        if temp is None or hum is None:
            self.log.warning("Sensors", "DHT read failed, using default values")
            temp = 25.0
            hum = 50.0

        light = self.sensors.read_light()
        soil_summary, soil_majority, soil_readings = self.sensors.read_soil()
        soil_wetness_pct = round(soil_readings.count("WET") / len(soil_readings) * 100, 1) if soil_readings else None

        self.log.info("Sensors", f"Temp={temp}C Hum={hum}% Light={light} Soil={soil_summary} Wetness={soil_wetness_pct}%")

        self.log.info("Storage", "Uploading image")
        image_url = self.storage.upload_image(self.settings.image_path)
        self.log.success("Storage", f"Uploaded image URL: {image_url}")

        self.log.info("AI", "Sending data for analysis")
        ai_result, prompt_md, response_md = self.ai.analyze(temp, hum, light, soil_summary)

        plant_data = ai_result.get("plant", {}) if isinstance(ai_result, dict) else {}
        disease_data = ai_result.get("disease", {}) if isinstance(ai_result, dict) else {}
        plant_name = plant_data.get("name", "Unknown") if isinstance(plant_data, dict) else str(plant_data)
        disease_name = disease_data.get("name", "Unknown") if isinstance(disease_data, dict) else str(disease_data)
        disease_confidence = (
            disease_data.get("confidence", 0.0) if isinstance(disease_data, dict) else 0.0
        )

        self.log.success(
            "AI",
            f"Plant={plant_name} Disease={disease_name} Confidence={disease_confidence}",
        )

        actions = self.actuators.apply(ai_result, temp, soil_majority)
        self.log.info("Actuators", f"Actions applied: {actions}")

        timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
        payload = {
            "timestamp": timestamp,
            "temp": temp,
            "hum": hum,
            "temp_readings": temp_readings,
            "hum_readings": hum_readings,
            "light": light,
            "soil_summary": soil_summary,
            "soil_majority": soil_majority,
            "soil_readings": soil_readings,
            "soil_wetness_pct": soil_wetness_pct,
            "image_url": image_url,
            "ai_result": ai_result,
            "actions": actions,
            "prompt_md": prompt_md,
            "response_md": response_md,
        }

        self.log.info("Supabase", "Writing cycle to relational tables")
        self.storage.log_cycle(payload)
        self.log.success("Supabase", "Cycle logged successfully")
        self.log.debug("Supabase", str(payload))
