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
        self.google = services["google"]
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
        temp, hum = self.sensors.read_dht()
        if temp is None or hum is None:
            self.log.warning("Sensors", "DHT read failed, using default values")
            temp = 25.0
            hum = 50.0

        light = self.sensors.read_light()
        soil_summary, soil_majority = self.sensors.read_soil()

        self.log.info("Sensors", f"Temp={temp}C Hum={hum}% Light={light} Soil={soil_summary}")

        self.log.info("Drive", "Uploading image")
        image_url = self.google.upload_image(self.settings.image_path)
        self.log.success("Drive", f"Uploaded image URL: {image_url}")

        self.log.info("AI", "Sending data for analysis")
        ai_result, prompt_md, response_md = self.ai.analyze(temp, hum, light, soil_summary)
        self.log.success(
            "AI",
            f"Plant={ai_result['plant']} Disease={ai_result['disease']} Confidence={ai_result['confidence']}",
        )

        actions = self.actuators.apply(ai_result, temp, soil_majority)
        self.log.info("Actuators", f"Actions applied: {actions}")

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row = [
            timestamp,
            temp,
            hum,
            light,
            soil_summary,
            image_url,
            ai_result["disease"],
            ai_result["confidence"],
            actions,
            ai_result["plant"],
            prompt_md,
            response_md,
        ]

        self.log.info("Sheets", "Writing row to sheet")
        self.google.log_to_sheet(row)
        self.log.success("Sheets", "Row logged successfully")
        self.log.debug("Sheets", str(row))
