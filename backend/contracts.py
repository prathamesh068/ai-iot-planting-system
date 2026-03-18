from abc import ABC, abstractmethod
from typing import Any, List, Mapping, Optional, Tuple


class BaseGPIO(ABC):
    @abstractmethod
    def fan_on(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def fan_off(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def pump_on(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def pump_off(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def cleanup(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_pin(self, pin: int) -> int:
        raise NotImplementedError


class BaseSensors(ABC):
    @abstractmethod
    def read_dht(self, max_retries: int = 5, retry_delay: float = 2.0) -> Tuple[List[Optional[float]], List[Optional[float]]]:
        raise NotImplementedError

    @abstractmethod
    def read_light(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def read_soil(self) -> Tuple[str, str, List[str]]:
        raise NotImplementedError


class BaseCamera(ABC):
    @abstractmethod
    def capture(self) -> bool:
        raise NotImplementedError


class BaseStorageService(ABC):
    @abstractmethod
    def upload_image(self, path: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def log_cycle(self, payload: Mapping[str, Any]) -> None:
        raise NotImplementedError


class BasePlantAI(ABC):
    @abstractmethod
    def analyze(self, temp: Any, humidity: Any, light: str, soil_summary: str):
        raise NotImplementedError
