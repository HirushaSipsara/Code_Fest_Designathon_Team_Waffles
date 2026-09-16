import json
import logging
import httpx
from pydantic import ValidationError
from app.ai.provider import AIProvider, GeminiProvider, OpenAICompatibleProvider
from app.ai.seed_context import FEW_SHOT_EXAMPLES, SUPPORTED_ACTIONS, SUPPORTED_CONDITION, SUPPORTED_TRIGGER
from app.core.config import get_settings
from app.schemas.scene import SceneProposal

logger = logging.getLogger("uvicorn.error")

def unavailable(reason: str) -> SceneProposal:
    return SceneProposal(scene_name="Manual scene required", trigger={"type": "resident_arrives"}, conditions=[], actions=[], status="service_unavailable", explanation="Use the visual scene builder instead.", reason=reason)

def strict_provider_schema(schema: dict) -> dict:
    """OpenAI strict JSON schemas require every object property to be required; nullable fields remain nullable."""
    def visit(node):
        if isinstance(node, dict):
            if node.get("type") == "object" and "properties" in node:
                node["required"] = list(node["properties"])
            for value in node.values(): visit(value)
        elif isinstance(node, list):
            for value in node: visit(value)
    visit(schema)
    return schema


# ---------------------------------------------------------------------------
# Seeded NL Engine — keyword matching, no LLM
# ---------------------------------------------------------------------------

SEEDED_SCENES: list[dict] = [
    {
        "keywords": ["comfortable", "study", "studying", "focus", "concentrate", "work from home"],
        "scene_name": "Study Mode",
        "actions": [
            {"device_id": "ac", "action": "set_temperature", "value": 24},
            {"device_id": "light", "action": "turn_on", "value": None},
            {"device_id": "curtain", "action": "set_level", "value": 80},
        ],
        "explanation": "AC set to a comfortable 24°C, lights on, and curtains mostly open for natural light — ideal for focused work.",
    },
    {
        "keywords": ["movie", "cinema", "watch", "film", "netflix", "streaming"],
        "scene_name": "Movie Night",
        "actions": [
            {"device_id": "tv", "action": "turn_on", "value": None},
            {"device_id": "light", "action": "set_level", "value": 20},
            {"device_id": "curtain", "action": "set_level", "value": 0},
        ],
        "explanation": "TV on, lights dimmed to 20% for ambiance, and curtains closed to reduce glare.",
    },
    {
        "keywords": ["sleep", "bedtime", "night", "good night", "rest", "nap"],
        "scene_name": "Goodnight",
        "actions": [
            {"device_id": "light", "action": "turn_off", "value": None},
            {"device_id": "blight", "action": "turn_off", "value": None},
            {"device_id": "bac", "action": "set_temperature", "value": 23},
            {"device_id": "bcurtain", "action": "set_level", "value": 0},
            {"device_id": "lock", "action": "lock", "value": None},
        ],
        "explanation": "All lights off, bedroom AC at a cool 23°C, curtains closed, and front door locked for a safe night.",
    },
    {
        "keywords": ["leaving", "going out", "away", "bye", "out", "leave"],
        "scene_name": "Away Mode",
        "actions": [
            {"device_id": "light", "action": "turn_off", "value": None},
            {"device_id": "blight", "action": "turn_off", "value": None},
            {"device_id": "ac", "action": "turn_off", "value": None},
            {"device_id": "tv", "action": "turn_off", "value": None},
            {"device_id": "curtain", "action": "set_level", "value": 0},
            {"device_id": "lock", "action": "lock", "value": None},
        ],
        "explanation": "Everything off, curtains closed, and door locked. Your home is secured while you're away.",
    },
    {
        "keywords": ["morning", "wake up", "sunrise", "waking"],
        "scene_name": "Good Morning",
        "actions": [
            {"device_id": "curtain", "action": "set_level", "value": 100},
            {"device_id": "bcurtain", "action": "set_level", "value": 100},
            {"device_id": "light", "action": "set_level", "value": 80},
            {"device_id": "ac", "action": "turn_off", "value": None},
        ],
        "explanation": "Curtains open for natural sunlight, lights at 80%, and AC off to start the day fresh.",
    },
    {
        "keywords": ["cooking", "kitchen", "cook", "baking"],
        "scene_name": "Kitchen Active",
        "actions": [
            {"device_id": "klight", "action": "turn_on", "value": None},
        ],
        "explanation": "Kitchen counter light turned on for safe food preparation.",
    },
    {
        "keywords": ["romantic", "dinner", "date", "candle", "intimate"],
        "scene_name": "Romantic Evening",
        "actions": [
            {"device_id": "light", "action": "set_level", "value": 30},
            {"device_id": "curtain", "action": "set_level", "value": 0},
            {"device_id": "ac", "action": "set_temperature", "value": 24},
        ],
        "explanation": "Lights dimmed to 30% for a warm glow, curtains closed for privacy, and AC at a comfortable temperature.",
    },
    {
        "keywords": ["cool", "hot", "warm", "cold", "temperature"],
        "scene_name": "Climate Adjust",
        "actions": [
            {"device_id": "ac", "action": "set_temperature", "value": 24},
        ],
        "explanation": "Air conditioner adjusted to a comfortable 24°C.",
    },
    {
        "keywords": ["bright", "reading", "read", "book"],
        "scene_name": "Reading Mode",
        "actions": [
            {"device_id": "light", "action": "set_level", "value": 100},
            {"device_id": "blight", "action": "turn_on", "value": None},
        ],
        "explanation": "All lights at full brightness for comfortable reading.",
    },
    {
        "keywords": ["dark", "dim", "low light", "cozy"],
        "scene_name": "Ambient Mode",
        "actions": [
            {"device_id": "light", "action": "set_level", "value": 10},
            {"device_id": "blight", "action": "set_level", "value": 10},
        ],
        "explanation": "Lights dimmed to 10% for a cozy, low-light atmosphere.",
    },
    {
        "keywords": ["secure", "lock", "safety", "safe"],
        "scene_name": "Security Mode",
        "actions": [
            {"device_id": "lock", "action": "lock", "value": None},
            {"device_id": "curtain", "action": "set_level", "value": 0},
        ],
        "explanation": "Front door locked and curtains closed for maximum security.",
    },
    {
        "keywords": ["party", "guests", "friends", "celebration", "entertain"],
        "scene_name": "Party Mode",
        "actions": [
            {"device_id": "light", "action": "turn_on", "value": None},
            {"device_id": "ac", "action": "set_temperature", "value": 23},
            {"device_id": "tv", "action": "turn_on", "value": None},
        ],
        "explanation": "Lights on, AC at 23°C to keep everyone comfortable, and TV on for entertainment.",
    },
    {
        "keywords": ["energy", "eco", "saving", "save", "efficient", "green"],
        "scene_name": "Energy Saver",
        "actions": [
            {"device_id": "ac", "action": "set_temperature", "value": 26},
            {"device_id": "light", "action": "set_level", "value": 40},
        ],
        "explanation": "AC set to an efficient 26°C and lights at 40% to reduce energy consumption.",
    },
    {
        "keywords": ["welcome", "arrive", "home", "coming home", "i'm home"],
        "scene_name": "Welcome Home",
        "actions": [
            {"device_id": "light", "action": "turn_on", "value": None},
            {"device_id": "ac", "action": "set_temperature", "value": 24},
            {"device_id": "curtain", "action": "set_level", "value": 50},
        ],
        "explanation": "Lights on, AC at a comfortable 24°C, and curtains halfway — welcome home!",
    },
    {
        "keywords": ["relax", "chill", "unwind", "lazy"],
        "scene_name": "Relaxation Mode",
        "actions": [
            {"device_id": "light", "action": "set_level", "value": 40},
            {"device_id": "ac", "action": "set_temperature", "value": 24},
            {"device_id": "curtain", "action": "set_level", "value": 30},
            {"device_id": "tv", "action": "turn_on", "value": None},
        ],
        "explanation": "Lights at a relaxing 40%, AC at 24°C, curtains mostly closed, and TV on to unwind.",
    },
]


def _match_seeded_scene(request_text: str) -> SceneProposal | None:
    """Find the best matching seeded scene for the given request text."""
    request_lower = request_text.lower()

    best_match = None
    best_score = 0

    for scene in SEEDED_SCENES:
        score = sum(1 for kw in scene["keywords"] if kw in request_lower)
        if score > best_score:
            best_score = score
            best_match = scene

    if not best_match:
        return None

    return SceneProposal(
        scene_name=best_match["scene_name"],
        trigger={"type": "resident_arrives"},
        conditions=[{"type": "time_after", "value": "18:00"}],
        actions=best_match["actions"],
        status="ready",
        explanation=best_match["explanation"],
    )


class AIService:
    """Provider-agnostic intent parser. It has no device access."""

    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider or self._default_provider()

    @staticmethod
    def _default_provider() -> AIProvider:
        return OpenAICompatibleProvider() if get_settings().ai_provider == "openai" else GeminiProvider()

    def parse_scene_request(self, request: str, devices: list[dict], role: str) -> SceneProposal:
        logger.info("AI request received")
        settings = get_settings()

        # --- Seeded mode: keyword matching, no LLM ---
        if settings.ai_use_seeded:
            logger.info("Using seeded NL engine (no LLM)")
            result = _match_seeded_scene(request)
            if result:
                logger.info("Seeded match found: %s", result.scene_name)
                return result
            return SceneProposal(
                scene_name="Manual scene required",
                trigger={"type": "resident_arrives"},
                conditions=[],
                actions=[],
                status="needs_clarification",
                explanation="I didn't quite understand that. Try describing a mood (e.g. \"cozy\"), activity (e.g. \"studying\"), or time of day (e.g. \"bedtime\").",
            )

        # --- LLM mode (production path, requires API key) ---
        if not settings.ai_api_key or not settings.ai_model:
            return unavailable("AI provider is not configured")
        schema = strict_provider_schema(SceneProposal.model_json_schema())
        catalogue = [{"id": d["id"], "name": d["name"], "kind": d["kind"], "room": d["room"], "actions": SUPPORTED_ACTIONS[d["kind"]]} for d in devices if d["kind"] in SUPPORTED_ACTIONS]
        system = (
            "Convert a LIVLINK resident request into JSON matching the supplied strict schema. "
            "Only use supplied device IDs/actions. AC temperature 16-32; light/curtain level 0-100. "
            "Trigger only resident_arrives; condition only time_after HH:MM. No unlock, visitor access, arbitrary actions or invented devices. "
            "If no arrival trigger or clear time, or ambiguous room, return needs_clarification with empty actions. "
            "If outside these capabilities return unsupported with empty actions. Give a concise user-facing explanation, never private reasoning."
        )
        context = {"request": request, "role": role, "allowed_actions": SUPPORTED_ACTIONS, "supported_trigger": SUPPORTED_TRIGGER, "supported_condition": SUPPORTED_CONDITION, "devices": catalogue, "examples": FEW_SHOT_EXAMPLES}
        try:
            logger.info("Provider request started")
            content = self.provider.parse_scene(model=settings.ai_model, key=settings.ai_api_key, base_url=settings.ai_base_url, messages=[{"role": "system", "content": system}, {"role": "user", "content": json.dumps(context)}], schema=schema)
            logger.info("Provider response received")
            result = SceneProposal.model_validate_json(content)
            logger.info("Schema validation passed")
            return result
        except ValidationError:
            logger.warning("Schema validation failed")
            return unavailable("AI returned invalid structured data")
        except (httpx.HTTPError, KeyError, TypeError, ValueError):
            logger.warning("Provider request or response failed")
            return unavailable("AI service is unavailable")
