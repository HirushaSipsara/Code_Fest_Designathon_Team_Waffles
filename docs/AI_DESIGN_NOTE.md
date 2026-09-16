# AI design note

## Genuine problem and technique

Natural-language scene creation saves residents from translating an intention into several precise device controls. `AIService` calls the replaceable `AIProvider` interface; the current `OpenAICompatibleProvider` converts the request into a constrained `SceneProposal` JSON object. It receives only the request, supported prototype devices/actions, resident role and a small few-shot set from `backend/app/ai/seed_context.py`.

The output is parsed by Pydantic with `extra=forbid`, then checked deterministically against known device IDs, device/action compatibility, value ranges, and resident policy. The provider cannot call APIs for a device and has no database or device credentials.

## Human control and fallback

The LLM produces a **proposal only**. A server-issued proposal ID is persisted before review; fabricated or modified client proposals cannot be confirmed. A resident reviews its trigger, conditions, actions and short explanation, then explicitly confirms it. Only the automation engine can call `DeviceService`. Unsupported, malformed, ambiguous, unsafe or unavailable AI responses yield a visible status and direct the resident to the existing manual drag-and-drop builder.

## Limitations

- Only source-prototype devices, arrival trigger, `time_after` condition and documented action ranges are supported.
- An LLM can produce invalid, ambiguous or unavailable output; it is never trusted.
- No AI key/model means no parsing, not a fake demo response.
- The device layer is a backend simulator, not physical IoT hardware.
- No LIVLINK-specific model has been trained.
