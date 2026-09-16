# Questions for owner

| Feature | HTML location | Unclear point | Why it matters | Exact question |
|---|---:|---|---|---|
| Device identifiers | 1179–1196 | The prototype uses short local IDs (`ac`, `light`) while its narrative example mentions a hallway light. | AI must reject unknown IDs rather than map them unsafely. | Which canonical backend device IDs/rooms should production use, and is a hallway light part of the approved inventory? |
| Scene edit/pause | 1544–1563 | Edit and Pause only display toasts. | No safe persistence semantics are inferable. | Should edit/pause persist, disable automation, or remain presentation-only? |
| Visitor credential | 1205–1213, 1853–2051 | QR/token lifetime, cryptography and operator authority are not specified. | P1 needs a secure validation contract. | What is the required pass token format, expiry/time-zone rule, and operator approval policy? |
| Payment actions | 2193–2264 | Payment/membership success is timer-based. | A backend must not assert real financial settlement. | Which provider and payment/receipt lifecycle should LIVLINK support? |
