import json
import httpx
from pydantic import ValidationError
from app.core.config import get_settings
from app.schemas.scene import SceneProposal


class AIService:
    """OpenAI-compatible parser. It only produces a proposal; it has no device access."""

    def parse_scene_request(self, request: str, devices: list[dict], role: str) -> SceneProposal:
        settings = get_settings()
        if not settings.ai_api_key or not settings.ai_model:
            return SceneProposal(scene_name="Manual scene required", trigger={"type": "resident_arrives"}, conditions=[], actions=[], status="service_unavailable", explanation="AI parsing is unavailable because no AI provider is configured.")
        schema = SceneProposal.model_json_schema()
        system = (
            "You convert a resident request into a LIVLINK scene proposal. Return only JSON matching the supplied schema. "
            "Use only the supplied devices and their supported action names: ac=set_temperature (16-32), "
            "light/curtain=set_level (0-100), light/tv=turn_on or turn_off, lock=lock. "
            "Trigger only resident_arrives; condition only time_after HH:MM. Never use unlock. "
            "If unclear or unsupported, return status needs_clarification or unsupported with actions []."
        )
        payload = {"model": settings.ai_model, "messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps({"request": request, "resident_role": role, "supported_devices": devices})}], "response_format": {"type": "json_schema", "json_schema": {"name": "livlink_scene", "strict": True, "schema": schema}}}
        try:
            response = httpx.post(f"{settings.ai_base_url.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {settings.ai_api_key}"}, json=payload, timeout=20)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return SceneProposal.model_validate_json(content)
        except (httpx.HTTPError, KeyError, TypeError, json.JSONDecodeError, ValidationError):
            return SceneProposal(scene_name="Manual scene required", trigger={"type": "resident_arrives"}, conditions=[], actions=[], status="service_unavailable", explanation="LIVLINK could not safely validate an AI response. Use the visual scene builder instead.")
