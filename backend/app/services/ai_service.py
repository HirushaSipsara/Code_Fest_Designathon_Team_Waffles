import json
import logging
import httpx
from pydantic import ValidationError
from app.ai.provider import AIProvider, OpenAICompatibleProvider
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

class AIService:
    """Provider-agnostic intent parser. It has no device access."""

    def __init__(self, provider: AIProvider | None = None):
        self.provider = provider or OpenAICompatibleProvider()

    def parse_scene_request(self, request: str, devices: list[dict], role: str) -> SceneProposal:
        logger.info("AI request received")
        settings = get_settings()
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
