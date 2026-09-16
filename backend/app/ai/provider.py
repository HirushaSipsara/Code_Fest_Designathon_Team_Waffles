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


def _gemini_schema(schema: dict) -> dict:
    """Gemini's responseSchema is an OpenAPI-3.0-era subset: no $ref/$defs,
    no `const`, no `additionalProperties`, no `default`, and no bare
    `type: "null"` branch — optionality is a `nullable: true` flag on the
    real type instead. Pydantic's model_json_schema() produces every one of
    those for a model with Optional fields and nested sub-models, so inline
    and rewrite them here rather than asking the schema author to know
    Gemini's dialect."""
    defs = schema.get("$defs", {})
    DROP_KEYS = ("$defs", "additionalProperties", "title", "default")

    def resolve(node):
        if isinstance(node, dict):
            if "$ref" in node:
                target = resolve(defs[node["$ref"].rsplit("/", 1)[-1]])
                merged = dict(target)
                merged.update({k: resolve(v) for k, v in node.items() if k != "$ref"})
                return merged
            if "anyOf" in node:
                branches = [resolve(b) for b in node["anyOf"]]
                real = [b for b in branches if b.get("type") != "null"]
                if len(real) == 1 and len(branches) - len(real) >= 1:
                    out = {**real[0], **{k: resolve(v) for k, v in node.items() if k not in ("anyOf", *DROP_KEYS)}}
                    out["nullable"] = True
                    return out
                node = {**node, "anyOf": branches}
            out = {k: resolve(v) for k, v in node.items() if k not in DROP_KEYS}
            if "const" in out:
                out["enum"] = [out.pop("const")]
            return out
        if isinstance(node, list):
            return [resolve(v) for v in node]
        return node

    return resolve(schema)


class GeminiProvider:
    """Google Gemini (generativelanguage.googleapis.com), called directly —
    not through an OpenAI-compatibility shim — so the JSON schema constraint
    Gemini actually understands is the one it receives."""

    def parse_scene(self, *, model: str, key: str, base_url: str, messages: list[dict], schema: dict) -> str:
        system_text = next((m["content"] for m in messages if m["role"] == "system"), "")
        user_text = next((m["content"] for m in messages if m["role"] == "user"), "")
        url = f"{base_url.rstrip('/')}/models/{model}:generateContent"
        body = {
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
            "systemInstruction": {"parts": [{"text": system_text}]},
            "generationConfig": {
                "responseMimeType": "application/json",
                "responseSchema": _gemini_schema(schema),
            },
        }
        response = httpx.post(url, params={"key": key}, json=body, timeout=25)
        response.raise_for_status()
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            reason = (data.get("candidates") or [{}])[0].get("finishReason", "no candidates returned")
            raise ValueError(f"Gemini returned no usable content ({reason})") from exc
