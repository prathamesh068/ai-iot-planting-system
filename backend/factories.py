from backend.config import Settings
from backend.services.ai_service import create_ai_service
from backend.services.camera_service import create_camera_service
from backend.services.gpio_service import create_gpio_manager
from backend.services.sensor_service import create_sensor_manager
from backend.services.supabase_service import create_supabase_service


def build_services(args, settings: Settings, logger):
    force_mock = bool(settings.mock)

    gpio = create_gpio_manager(
        is_mock=force_mock,
        ldr_pin=args.ldr_pin,
        soil_pins=args.soil_pins,
        fan_pin=args.fan_pin,
        pump_pin=args.pump_pin,
        logger=logger,
    )

    sensors = create_sensor_manager(
        is_mock=force_mock,
        dht_pins=args.dht_pins,
        ldr_pin=args.ldr_pin,
        soil_pins=args.soil_pins,
        gpio=gpio,
        logger=logger,
    )

    # Camera, Supabase, and AI self-select real/mock based on platform and credentials.
    # force_mock=True only when --mock is explicitly passed (e.g. CI / no hardware at all).
    camera = create_camera_service(is_mock=force_mock, image_path=settings.image_path, logger=logger)
    storage = create_supabase_service(is_mock=force_mock, settings=settings, logger=logger)
    ai = create_ai_service(is_mock=force_mock, settings=settings, image_path=settings.image_path, logger=logger)

    return {
        "gpio": gpio,
        "sensors": sensors,
        "camera": camera,
        "storage": storage,
        "ai": ai,
    }
