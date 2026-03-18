import json
from typing import Any, Dict, Tuple

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

        import google.generativeai as genai  # pylint: disable=import-error

        if not self.settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY is required in non-mock mode")

        genai.configure(api_key=self.settings.gemini_api_key)
        self._model = genai.GenerativeModel("gemini-2.5-flash-lite")

    def analyze(self, temp: Any, humidity: Any, light: str, soil_summary: str):
        with open(self.image_path, "rb") as image_file:
            image = image_file.read()

        prompt_text = self.PROMPT.format(temp=temp, humidity=humidity, light=light, soil=soil_summary)
        content = [prompt_text, {"mime_type": "image/jpeg", "data": image}]

        try:
            response = self._model.generate_content(content, request_options={"timeout": 30})
            response_text = response.text.strip()
            self.log.debug("Gemini", response_text)
            response_md = f"```json\n{response_text}\n```"
            parsed = json.loads(response_text.replace("```json", "").replace("```", "").strip())
            return parsed, prompt_text, response_md
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self.log.error("Gemini", f"API error: {exc}")
            return DEFAULT_AI_RESULT.copy(), prompt_text, f"```\nError: {exc}\n```"


class MockAIService(BaseAIService):
    def analyze(self, temp: Any, humidity: Any, light: str, soil_summary: str):
        prompt_text = self.PROMPT.format(temp=temp, humidity=humidity, light=light, soil=soil_summary)

        soil_is_dry = "DRY" in str(soil_summary).upper()
        high_temp = float(temp) > 30

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
        return result, prompt_text, response_md


def create_ai_service(is_mock: bool, settings: Settings, image_path: str, logger) -> BaseAIService:
    if is_mock:
        return MockAIService(settings=settings, image_path=image_path, logger=logger)
    return RealAIService(settings=settings, image_path=image_path, logger=logger)
