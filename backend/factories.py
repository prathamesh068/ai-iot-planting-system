from backend.config import Settings
from backend.services.ai_service import create_ai_service
from backend.services.camera_service import create_camera_service
from backend.services.gpio_service import create_gpio_manager
from backend.services.google_service import create_google_service
from backend.services.sensor_service import create_sensor_manager


def build_services(args, settings: Settings, logger):
    is_mock = bool(settings.mock)

    gpio = create_gpio_manager(
        is_mock=is_mock,
        ldr_pin=args.ldr_pin,
        soil_pins=args.soil_pins,
        fan_pin=args.fan_pin,
        pump_pin=args.pump_pin,
        logger=logger,
    )

    sensors = create_sensor_manager(
        is_mock=is_mock,
        dht_pin=args.dht_pin,
        ldr_pin=args.ldr_pin,
        soil_pins=args.soil_pins,
        gpio=gpio,
        logger=logger,
    )

    camera = create_camera_service(is_mock=is_mock, image_path=settings.image_path, logger=logger)
    google = create_google_service(is_mock=is_mock, settings=settings, logger=logger)
    ai = create_ai_service(is_mock=is_mock, settings=settings, image_path=settings.image_path, logger=logger)

    return {
        "gpio": gpio,
        "sensors": sensors,
        "camera": camera,
        "google": google,
        "ai": ai,
    }
