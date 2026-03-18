import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    image_path: str
    drive_folder_id: str
    spreadsheet_id: str
    gemini_api_key: str
    token_path: str
    credentials_path: str
    mock: bool


SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


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
        drive_folder_id=os.environ.get("DRIVE_FOLDER_ID", ""),
        spreadsheet_id=os.environ.get("SPREADSHEET_ID", ""),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", ""),
        token_path=os.environ.get("TOKEN_PATH", "token.json"),
        credentials_path=os.environ.get("CREDENTIALS_PATH", "credentials.json"),
        mock=mock_value,
    )
