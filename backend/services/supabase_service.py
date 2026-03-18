import time
import uuid
from typing import Any, Dict, Mapping

from backend.config import Settings
from backend.contracts import BaseStorageService


class BaseSupabaseService(BaseStorageService):
    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.log = logger

    def upload_image(self, path: str) -> str:
        raise NotImplementedError

    def log_cycle(self, payload: Mapping[str, Any]) -> None:
        raise NotImplementedError


class RealSupabaseService(BaseSupabaseService):
    def __init__(self, settings: Settings, logger):
        super().__init__(settings, logger)

        from supabase import create_client  # pylint: disable=import-error

        if not self.settings.supabase_url:
            raise ValueError("SUPABASE_URL is required in non-mock mode")
        if not self.settings.supabase_service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY is required in non-mock mode")

        self._client = create_client(self.settings.supabase_url, self.settings.supabase_service_role_key)

    def upload_image(self, path: str) -> str:
        file_name = f"plant_{int(time.time())}_{uuid.uuid4().hex[:8]}.jpg"
        with open(path, "rb") as image_file:
            image_bytes = image_file.read()

        bucket = self._client.storage.from_(self.settings.supabase_storage_bucket)
        bucket.upload(
            path=file_name,
            file=image_bytes,
            file_options={"content-type": "image/jpeg", "upsert": "false"},
        )
        return bucket.get_public_url(file_name)

    def log_cycle(self, payload: Mapping[str, Any]) -> None:
        ai_result = payload.get("ai_result", {}) or {}
        recommendation = ai_result.get("recommendation", {}) or {}
        todos = ai_result.get("todos", []) or []
        plant_data = ai_result.get("plant", {}) or {}
        disease_data = ai_result.get("disease", {}) or {}

        plant_name = plant_data.get("name") if isinstance(plant_data, dict) else plant_data
        disease_name = disease_data.get("name") if isinstance(disease_data, dict) else disease_data
        confidence = (
            disease_data.get("confidence")
            if isinstance(disease_data, dict)
            else ai_result.get("confidence")
        )

        cycle_payload = {
            "captured_at": payload.get("timestamp"),
            "image_url": payload.get("image_url"),
        }
        cycle_insert = self._client.table("plant_cycles").insert(cycle_payload).execute()
        if not cycle_insert.data:
            raise RuntimeError("Supabase insert failed for plant_cycles")

        cycle_id = cycle_insert.data[0]["id"]

        self._client.table("sensor_readings").insert(
            {
                "cycle_id": cycle_id,
                "temp_c": payload.get("temp"),
                "humidity_pct": payload.get("hum"),
                "light_state": payload.get("light"),
                "soil_summary": payload.get("soil_summary"),
                "soil_majority": payload.get("soil_majority"),
                "temp_readings": payload.get("temp_readings") or [],
                "hum_readings": payload.get("hum_readings") or [],
                "soil_readings": payload.get("soil_readings") or [],
                "soil_wetness_pct": payload.get("soil_wetness_pct"),
            }
        ).execute()

        self._client.table("ai_analyses").insert(
            {
                "cycle_id": cycle_id,
                "disease": disease_name,
                "plant": plant_name,
                "confidence": confidence,
                "todos": todos,
                "recommendation": recommendation,
                "prompt_markdown": payload.get("prompt_md"),
                "response_markdown": payload.get("response_md"),
            }
        ).execute()

        self._client.table("actuator_actions").insert(
            {
                "cycle_id": cycle_id,
                "actions": payload.get("actions"),
            }
        ).execute()


class MockSupabaseService(BaseSupabaseService):
    def __init__(self, settings: Settings, logger):
        super().__init__(settings, logger)
        self.cycles = []

    def upload_image(self, path: str) -> str:
        _ = path
        mock_url = f"https://mock.local/supabase/plant_{int(time.time())}.jpg"
        self.log.info("MockStorage", f"Returning mock image URL: {mock_url}")
        return mock_url

    def log_cycle(self, payload: Mapping[str, Any]) -> None:
        self.cycles.append(dict(payload))
        self.log.info("MockSupabase", f"Captured cycle in memory ({len(self.cycles)} total)")


def create_supabase_service(is_mock: bool, settings: Settings, logger) -> BaseSupabaseService:
    if not is_mock and settings.supabase_url and settings.supabase_service_role_key:
        return RealSupabaseService(settings=settings, logger=logger)
    if not is_mock:
        logger.warning("Supabase", "SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY not set, falling back to mock storage")
    return MockSupabaseService(settings=settings, logger=logger)
