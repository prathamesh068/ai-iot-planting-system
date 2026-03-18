import datetime


class Logger:
    """Simple ANSI logger with leveled output."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    _LEVELS = {
        "INFO": ("\033[96m", "INFO   "),
        "SUCCESS": ("\033[92m", "SUCCESS"),
        "WARNING": ("\033[93m", "WARNING"),
        "ERROR": ("\033[91m", "ERROR  "),
        "DEBUG": ("\033[2m", "DEBUG  "),
    }

    def _log(self, level: str, module: str, msg: str) -> None:
        color, label = self._LEVELS[level]
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        prefix = (
            f"{self.DIM}[{ts}]{self.RESET} "
            f"{color}{self.BOLD}[{label}]{self.RESET} "
            f"\033[96m[{module:<12}]{self.RESET}"
        )
        print(f"{prefix} {msg}", flush=True)

    def info(self, module: str, msg: str) -> None:
        self._log("INFO", module, msg)

    def success(self, module: str, msg: str) -> None:
        self._log("SUCCESS", module, msg)

    def warning(self, module: str, msg: str) -> None:
        self._log("WARNING", module, msg)

    def error(self, module: str, msg: str) -> None:
        self._log("ERROR", module, msg)

    def debug(self, module: str, msg: str) -> None:
        self._log("DEBUG", module, msg)

    def section(self, title: str) -> None:
        bar = "=" * (len(title) + 4)
        print(f"\n{self.BOLD}[{bar}]\n[  {title}  ]\n[{bar}]{self.RESET}\n", flush=True)


log = Logger()
