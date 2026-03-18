import os
import time
from typing import Any, List, Sequence

from backend.config import SCOPES, Settings
from backend.contracts import BaseGoogleServices


class BaseGoogleService(BaseGoogleServices):
    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.log = logger

    def upload_image(self, path: str) -> str:
        raise NotImplementedError

    def log_to_sheet(self, row: Sequence[Any]) -> None:
        raise NotImplementedError


class RealGoogleService(BaseGoogleService):
    def __init__(self, settings: Settings, logger):
        super().__init__(settings, logger)

        from google.auth.transport.requests import Request  # pylint: disable=import-error
        from google.oauth2.credentials import Credentials  # pylint: disable=import-error
        from google_auth_oauthlib.flow import InstalledAppFlow  # pylint: disable=import-error
        from googleapiclient.discovery import build  # pylint: disable=import-error

        creds = None
        if os.path.exists(self.settings.token_path):
            creds = Credentials.from_authorized_user_file(self.settings.token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.settings.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

            with open(self.settings.token_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())

        self._drive = build("drive", "v3", credentials=creds)
        self._sheets = build("sheets", "v4", credentials=creds)

    def upload_image(self, path: str) -> str:
        from googleapiclient.http import MediaFileUpload  # pylint: disable=import-error

        metadata = {"name": f"plant_{int(time.time())}.jpg"}
        if self.settings.drive_folder_id:
            metadata["parents"] = [self.settings.drive_folder_id]

        media = MediaFileUpload(path, mimetype="image/jpeg")
        file = self._drive.files().create(body=metadata, media_body=media, fields="id").execute()
        return f"https://drive.google.com/file/d/{file['id']}/view"

    def log_to_sheet(self, row: Sequence[Any]) -> None:
        body = {"values": [list(row)]}
        self._sheets.spreadsheets().values().append(
            spreadsheetId=self.settings.spreadsheet_id,
            range="plant_readings!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()


class MockGoogleService(BaseGoogleService):
    def __init__(self, settings: Settings, logger):
        super().__init__(settings, logger)
        self.rows: List[Sequence[Any]] = []

    def upload_image(self, path: str) -> str:
        _ = path
        mock_url = f"https://mock.local/drive/plant_{int(time.time())}.jpg"
        self.log.info("MockDrive", f"Returning mock image URL: {mock_url}")
        return mock_url

    def log_to_sheet(self, row: Sequence[Any]) -> None:
        self.rows.append(list(row))
        self.log.info("MockSheets", f"Captured row in memory ({len(self.rows)} total)")


def create_google_service(is_mock: bool, settings: Settings, logger) -> BaseGoogleService:
    if is_mock:
        return MockGoogleService(settings=settings, logger=logger)
    return RealGoogleService(settings=settings, logger=logger)
