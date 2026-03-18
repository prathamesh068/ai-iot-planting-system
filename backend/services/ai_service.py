import json
from typing import Any, Dict, List

from backend.config import Settings
from backend.contracts import BasePlantAI


DEFAULT_AI_RESULT: Dict[str, Any] = {
    "plant": {
        "name": "No plant detected",
        "confidence": 0.0,
    },
    "disease": {
        "name": "Unknown",
        "confidence": 0.0,
        "reason": "Plant or disease could not be reliably identified.",
    },
    "environment": {
        "temperature": None,
        "humidity": None,
        "light": "unknown",
        "soil": "unknown",
    },
    "todos": [],
    "recommendation": {
        "reduce_temperature": False,
        "water_plant": False,
        "increase_airflow": False,
    },
}

AI_RESULT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["plant", "disease", "environment", "todos"],
    "properties": {
        "plant": {
            "type": "object",
            "required": ["name", "confidence"],
            "properties": {
                "name": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 100},
            },
            "additionalProperties": False,
        },
        "disease": {
            "type": "object",
            "required": ["name", "confidence", "reason"],
            "properties": {
                "name": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 100},
                "reason": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "environment": {
            "type": "object",
            "required": ["temperature", "humidity", "light", "soil"],
            "properties": {
                "temperature": {"type": "number"},
                "humidity": {"type": "number"},
                "light": {"type": "string"},
                "soil": {"type": "string"},
            },
            "additionalProperties": False,
        },
        "todos": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["action", "priority", "reason"],
                "properties": {
                    "action": {"type": "string"},
                    "priority": {"type": "string", "enum": ["HIGH", "MEDIUM", "LOW"]},
                    "reason": {"type": "string"},
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


def _default_ai_result() -> Dict[str, Any]:
    return {
        "plant": DEFAULT_AI_RESULT["plant"].copy(),
        "disease": DEFAULT_AI_RESULT["disease"].copy(),
        "environment": DEFAULT_AI_RESULT["environment"].copy(),
        "todos": [],
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


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_confidence(value: Any, default: float = 0.0) -> float:
    score = _to_float(value, default)
    if score < 0:
        return 0.0
    if score > 100:
        return 100.0
    return score


def _to_optional_float(value: Any) -> Any:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_priority(value: Any) -> str:
    normalized = str(value).strip().upper()
    return normalized if normalized in {"HIGH", "MEDIUM", "LOW"} else "LOW"


def _soil_is_majority_dry(soil_summary: Any) -> bool:
    return "DRY" in str(soil_summary).upper()


def _default_todos(temperature: Any, soil_summary: Any) -> List[Dict[str, str]]:
    todos: List[Dict[str, str]] = []
    if _soil_is_majority_dry(soil_summary):
        todos.append(
            {
                "action": "Irrigate the plant",
                "priority": "HIGH",
                "reason": "Majority soil reading is DRY.",
            }
        )

    temp_value = _to_float(temperature, 0.0)
    if temp_value > 30:
        todos.append(
            {
                "action": "Reduce ambient temperature",
                "priority": "HIGH",
                "reason": "Temperature is above 30C.",
            }
        )
        todos.append(
            {
                "action": "Increase airflow around the plant",
                "priority": "MEDIUM",
                "reason": "Higher temperature increases stress and disease risk.",
            }
        )

    if not todos:
        todos.append(
            {
                "action": "Continue routine monitoring",
                "priority": "LOW",
                "reason": "No immediate intervention is required.",
            }
        )
    return todos


def _derive_recommendation(
    disease_name: str,
    temperature: Any,
    soil_summary: Any,
    todos: List[Dict[str, str]],
) -> Dict[str, bool]:
    temp_value = _to_float(temperature, 0.0)
    disease_detected = disease_name.strip().lower() not in {"", "no disease found", "unknown"}
    todos_text = " ".join(
        f"{item.get('action', '')} {item.get('reason', '')}" for item in todos
    ).lower()

    return {
        "reduce_temperature": temp_value > 30 or "cool" in todos_text or "temperature" in todos_text,
        "water_plant": _soil_is_majority_dry(soil_summary),
        "increase_airflow": disease_detected or temp_value > 30 or "airflow" in todos_text or "fan" in todos_text,
    }


def _normalize_todos(value: Any) -> List[Dict[str, str]]:
    if not isinstance(value, list):
        return []

    todos: List[Dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        action = str(item.get("action", "")).strip()
        reason = str(item.get("reason", "")).strip()
        if not action:
            continue
        todos.append(
            {
                "action": action,
                "priority": _normalize_priority(item.get("priority")),
                "reason": reason or "No reason provided.",
            }
        )
    return todos


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

    plant_raw = raw_dict.get("plant", {})
    if isinstance(plant_raw, dict):
        plant_name = str(plant_raw.get("name", result["plant"]["name"])).strip() or result["plant"]["name"]
        plant_confidence = _to_confidence(plant_raw.get("confidence", result["plant"]["confidence"]))
    else:
        plant_name = str(plant_raw).strip() or result["plant"]["name"]
        plant_confidence = _to_confidence(raw_dict.get("confidence", result["plant"]["confidence"]))

    disease_raw = raw_dict.get("disease", {})
    if isinstance(disease_raw, dict):
        disease_name = str(disease_raw.get("name", result["disease"]["name"])).strip() or result["disease"]["name"]
        disease_confidence = _to_confidence(disease_raw.get("confidence", result["disease"]["confidence"]))
        disease_reason = str(disease_raw.get("reason", result["disease"]["reason"]))
    else:
        disease_name = str(disease_raw).strip() or result["disease"]["name"]
        disease_confidence = _to_confidence(raw_dict.get("confidence", result["disease"]["confidence"]))
        disease_reason = result["disease"]["reason"]

    if plant_name.lower() == "no plant detected":
        disease_name = "Unknown"
        disease_reason = "Plant not detected, disease classification is unknown."

    env_raw = _as_dict(raw_dict.get("environment", {}))
    env_temperature = _to_optional_float(env_raw.get("temperature", raw_dict.get("temperature")))
    env_humidity = _to_optional_float(env_raw.get("humidity", raw_dict.get("humidity")))
    env_light = str(env_raw.get("light", raw_dict.get("light", result["environment"]["light"])))
    env_soil = str(env_raw.get("soil", raw_dict.get("soil", result["environment"]["soil"])))

    todos = _normalize_todos(raw_dict.get("todos", []))
    if not todos:
        todos = _default_todos(env_temperature, env_soil)

    if disease_name.lower() == "no disease found":
        for todo in todos:
            todo_text = f"{todo['action']} {todo['reason']}".lower()
            if todo["priority"] == "HIGH" and any(
                token in todo_text for token in {"disease", "infection", "fung", "rot", "pest"}
            ):
                todo["priority"] = "MEDIUM"

    rec_raw = _as_dict(raw_dict.get("recommendation", {}))
    if rec_raw:
        recommendation = {
            "reduce_temperature": _to_bool(rec_raw.get("reduce_temperature", False)),
            "water_plant": _to_bool(rec_raw.get("water_plant", False)),
            "increase_airflow": _to_bool(rec_raw.get("increase_airflow", False)),
        }
    else:
        recommendation = _derive_recommendation(
            disease_name=disease_name,
            temperature=env_temperature,
            soil_summary=env_soil,
            todos=todos,
        )

    result["plant"] = {
        "name": plant_name,
        "confidence": plant_confidence,
    }
    result["disease"] = {
        "name": disease_name,
        "confidence": disease_confidence,
        "reason": disease_reason,
    }
    result["environment"] = {
        "temperature": env_temperature,
        "humidity": env_humidity,
        "light": env_light,
        "soil": env_soil,
    }
    result["todos"] = todos
    result["recommendation"] = recommendation
    return result


class BaseAIService(BasePlantAI):
    PROMPT = """
You are an agricultural AI in an IoT system.

Sensor Data:
- Temperature: {temp} C
- Humidity: {humidity} %
- Light: {light}
- Soil Moisture: {soil}

Image Analysis Rules:
- First detect plant. If unsure, return "No plant detected"
- Only detect diseases relevant to the identified plant
- If no disease is visible, return "No disease found"
- Always provide a confidence score (0-100) for plant and disease separately

Soil Rules:
- Soil moisture is reported as "X/Total DRY" or "X/Total WET"
- Recommend watering ONLY if the majority soil reading is DRY

Environment Rules:
- Recommend airflow if disease detected OR temperature > 30
- Recommend temperature reduction ONLY if temperature > 30

Response Rules:
- All actions must be structured as TODO items with priority
- Priority levels: HIGH, MEDIUM, LOW
- HIGH -> immediate risk (disease, extreme heat, fully dry soil)
- MEDIUM -> preventive care
- LOW -> general optimization

Output Format (STRICT JSON ONLY):

{{
    "plant": {{
        "name": "<plant_name | No plant detected>",
        "confidence": <0-100>
    }},
    "disease": {{
        "name": "<disease_name | No disease found>",
        "confidence": <0-100>,
        "reason": "<short visual justification>"
    }},
    "environment": {{
        "temperature": {temp},
        "humidity": {humidity},
        "light": "{light}",
        "soil": "{soil}"
    }},
    "todos": [
        {{
            "action": "<what to do>",
            "priority": "HIGH | MEDIUM | LOW",
            "reason": "<why this action is needed>"
        }}
    ]
}}

Behavior Constraints:
- Do NOT hallucinate diseases unrelated to the plant
- If plant is unknown -> disease must be "Unknown"
- If no disease -> no HIGH priority disease actions
- Keep reasons short and technical (no storytelling)
- Do NOT return anything except JSON
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
        with open('image.png', "rb") as image_file:
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

        todos: List[Dict[str, str]] = []
        if soil_is_dry:
            todos.append(
                {
                    "action": "Irrigate the plant",
                    "priority": "HIGH",
                    "reason": "Majority soil reading is DRY.",
                }
            )
        if high_temp:
            todos.append(
                {
                    "action": "Reduce ambient temperature",
                    "priority": "HIGH",
                    "reason": "Temperature is above 30C.",
                }
            )
            todos.append(
                {
                    "action": "Increase airflow around the plant",
                    "priority": "MEDIUM",
                    "reason": "Higher temperature can stress the plant.",
                }
            )
        if not todos:
            todos.append(
                {
                    "action": "Continue routine monitoring",
                    "priority": "LOW",
                    "reason": "No immediate intervention is required.",
                }
            )

        result = {
            "plant": {
                "name": "Healthy plant",
                "confidence": 95.0,
            },
            "disease": {
                "name": "No disease found",
                "confidence": 96.0,
                "reason": "No visible lesions, spotting, or rot detected.",
            },
            "environment": {
                "temperature": _to_optional_float(temp),
                "humidity": _to_optional_float(humidity),
                "light": str(light),
                "soil": str(soil_summary),
            },
            "todos": todos,
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
