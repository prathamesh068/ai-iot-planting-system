import json
from typing import Any, Dict

from backend.config import Settings
from backend.contracts import BasePlantAI


DEFAULT_AI_RESULT: Dict[str, Any] = {
    "disease": "unknown",
    "plant": "Unknown",
    "confidence": 0.0,
    "recommendation": {
        "reduce_temperature": False,
        "water_plant": False,
        "increase_airflow": False,
    },
}

AI_RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["disease", "plant", "confidence", "recommendation"],
    "properties": {
        "disease": {"type": "string"},
        "plant": {"type": "string"},
        "confidence": {"type": "number"},
        "recommendation": {
            "type": "object",
            "required": ["reduce_temperature", "water_plant", "increase_airflow"],
            "properties": {
                "reduce_temperature": {"type": "boolean"},
                "water_plant": {"type": "boolean"},
                "increase_airflow": {"type": "boolean"},
            },
        },
    },
}


def _default_ai_result() -> Dict[str, Any]:
    return {
        "disease": DEFAULT_AI_RESULT["disease"],
        "plant": DEFAULT_AI_RESULT["plant"],
        "confidence": DEFAULT_AI_RESULT["confidence"],
        "recommendation": DEFAULT_AI_RESULT["recommendation"].copy(),
    }


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off", ""}:
            return False
    return bool(value)


def _strip_code_fence(value: str) -> str:
    return value.replace("```json", "").replace("```", "").strip()


def _as_dict(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}

    candidate = _strip_code_fence(value)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _normalize_ai_result(raw_result: Any) -> Dict[str, Any]:
    raw_dict = _as_dict(raw_result)
    result = _default_ai_result()

    if not raw_dict:
        return result

    disease = raw_dict.get("disease", result["disease"])
    plant = raw_dict.get("plant", result["plant"])

    try:
        confidence = float(raw_dict.get("confidence", result["confidence"]))
    except (TypeError, ValueError):
        confidence = float(result["confidence"])

    rec_raw = _as_dict(raw_dict.get("recommendation", {}))
    result["disease"] = str(disease)
    result["plant"] = str(plant)
    result["confidence"] = confidence
    result["recommendation"] = {
        "reduce_temperature": _to_bool(rec_raw.get("reduce_temperature", False)),
        "water_plant": _to_bool(rec_raw.get("water_plant", False)),
        "increase_airflow": _to_bool(rec_raw.get("increase_airflow", False)),
    }
    return result


class BaseAIService(BasePlantAI):
    PROMPT = """
You are an agricultural AI in an IoT system.

Sensor Data:
- Temperature: {temp} C
- Humidity: {humidity} %
- Light: {light}
- Soil Moisture: {soil}

Rules:
- Soil moisture is reported as "X/Total DRY" or "X/Total WET"
- Recommend watering ONLY if the majority soil reading is DRY
- Recommend airflow if disease detected OR temperature > 30
- Reduce temperature ONLY if temperature > 30
- When no disease is found, set disease to No disease found and all flags to false
- When no plant is detected, set plant to No plant detected

Return ONLY valid JSON with fields: disease, plant, confidence, recommendation.
"""

    def __init__(self, settings: Settings, image_path: str, logger):
        self.settings = settings
        self.image_path = image_path
        self.log = logger

    def analyze(self, temp: Any, humidity: Any, light: str, soil_summary: str):
        raise NotImplementedError


class RealAIService(BaseAIService):
    def __init__(self, settings: Settings, image_path: str, logger):
        super().__init__(settings, image_path, logger)

        from google import genai  # pylint: disable=import-error
        from google.genai import types  # pylint: disable=import-error

        if not self.settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required in non-mock mode")

        self._types = types
        self._client = genai.Client(api_key=self.settings.gemini_api_key)
        self._model = "gemini-2.5-flash-lite"

    def analyze(self, temp: Any, humidity: Any, light: str, soil_summary: str):
        with open(self.image_path, "rb") as image_file:
            image = image_file.read()

        prompt_text = self.PROMPT.format(temp=temp, humidity=humidity, light=light, soil=soil_summary)
        content = [
            prompt_text,
            self._types.Part.from_bytes(data=image, mime_type="image/jpeg"),
        ]

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=content,
                config=self._types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_json_schema=AI_RESULT_SCHEMA,
                ),
            )
            response_text = (response.text or "").strip()
            if not response_text:
                raise ValueError("Gemini returned an empty response")
            self.log.debug("Gemini", response_text)
            response_md = f"```json\n{response_text}\n```"
            parsed = _normalize_ai_result(_strip_code_fence(response_text))
            return parsed, prompt_text, response_md
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.log.error("Gemini", f"API error: {exc}")
            return _default_ai_result(), prompt_text, f"```\nError: {exc}\n```"


class MockAIService(BaseAIService):
    def analyze(self, temp: Any, humidity: Any, light: str, soil_summary: str):
        prompt_text = self.PROMPT.format(temp=temp, humidity=humidity, light=light, soil=soil_summary)

        soil_is_dry = "DRY" in str(soil_summary).upper()
        try:
            high_temp = float(temp) > 30
        except (TypeError, ValueError):
            high_temp = False

        result = {
            "disease": "No disease found",
            "plant": "Healthy plant",
            "confidence": 0.93,
            "recommendation": {
                "reduce_temperature": high_temp,
                "water_plant": soil_is_dry,
                "increase_airflow": high_temp,
            },
        }
        response_md = "```json\n" + json.dumps(result, indent=2) + "\n```"
        self.log.info("MockGemini", "Returned deterministic mock analysis")
        return _normalize_ai_result(result), prompt_text, response_md


def create_ai_service(is_mock: bool, settings: Settings, image_path: str, logger) -> BaseAIService:
    if not is_mock and settings.gemini_api_key:
        return RealAIService(settings=settings, image_path=image_path, logger=logger)
    if not is_mock:
        logger.warning("AI", "GEMINI_API_KEY not set, falling back to mock AI")
    return MockAIService(settings=settings, image_path=image_path, logger=logger)
