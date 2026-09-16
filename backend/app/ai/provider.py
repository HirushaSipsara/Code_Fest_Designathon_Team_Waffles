"""Provider boundary with no device, database, or policy access."""
from typing import Protocol
import httpx

class AIProvider(Protocol):
    def parse_scene(self, *, model: str, key: str, base_url: str, messages: list[dict], schema: dict) -> str: ...

class OpenAICompatibleProvider:
    def parse_scene(self, *, model: str, key: str, base_url: str, messages: list[dict], schema: dict) -> str:
        response = httpx.post(f"{base_url.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {key}"}, json={"model": model, "messages": messages, "response_format": {"type": "json_schema", "json_schema": {"name": "livlink_scene", "strict": True, "schema": schema}}}, timeout=25)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
