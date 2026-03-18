from backend.cli import log_configuration, parse_args
from backend.config import load_settings
from backend.logger import log
from backend.system import SmartPlantSystem


def main() -> None:
    args = parse_args()
    settings = load_settings(mock_override=args.mock)

    log_configuration(log, args, settings.mock)

    system = SmartPlantSystem(args=args, settings=settings, logger=log)
    system.run()


if __name__ == "__main__":
    main()
