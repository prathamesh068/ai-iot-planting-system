import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    image_path: str
    gemini_api_key: str
    supabase_url: str
    supabase_service_role_key: str
    supabase_storage_bucket: str
    mock: bool


def _to_bool(value: Optional[str]) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings(mock_override: Optional[bool] = None) -> Settings:
    load_dotenv()
    env_mock = _to_bool(os.environ.get("MOCK"))
    mock_value = mock_override if mock_override is not None else env_mock

    return Settings(
        image_path=os.environ.get("IMAGE_PATH", "plant.jpg"),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
        supabase_url=os.environ.get("SUPABASE_URL", ""),
        supabase_service_role_key=os.environ.get("SUPABASE_SERVICE_ROLE_KEY", ""),
        supabase_storage_bucket=os.environ.get("SUPABASE_STORAGE_BUCKET", "plant-images"),
        mock=mock_value,
    )
