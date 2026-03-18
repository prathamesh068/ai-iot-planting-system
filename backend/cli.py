import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI + IoT Smart Plant System",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--dht-pins",
        type=int,
        nargs="+",
        default=[4],
        metavar="PIN",
        help="BCM pin numbers for DHT11 temperature/humidity sensors (multiple supported)",
    )
    parser.add_argument(
        "--ldr-pin",
        type=int,
        default=20,
        help="BCM pin number for LDR light sensor",
    )
    parser.add_argument(
        "--soil-pins",
        type=int,
        nargs="+",
        default=[5, 6, 13, 19, 26, 21],
        metavar="PIN",
        help="BCM pin numbers for soil moisture sensors",
    )
    parser.add_argument(
        "--fan-pin",
        type=int,
        default=27,
        help="BCM pin number for fan relay",
    )
    parser.add_argument(
        "--pump-pin",
        type=int,
        default=17,
        help="BCM pin number for water pump relay",
    )
    parser.add_argument(
        "--pump-duration",
        type=int,
        default=1,
        help="Number of seconds the water pump stays on when watering",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Run using mock services (no hardware, no cloud API calls)",
    )

    return parser.parse_args()


def log_configuration(log, args, is_mock: bool) -> None:
    log.section("AI + IoT Smart Plant System")
    log.info("CONFIG", f"Mode       = {'MOCK' if is_mock else 'REAL'}")
    log.info("CONFIG", f"DHT pins   = {args.dht_pins}")
    log.info("CONFIG", f"LDR pin    = {args.ldr_pin}")
    log.info("CONFIG", f"Soil pins  = {args.soil_pins}")
    log.info("CONFIG", f"Fan pin    = {args.fan_pin}")
    log.info("CONFIG", f"Pump pin   = {args.pump_pin}")
    log.info("CONFIG", f"Pump dur   = {args.pump_duration}s")
