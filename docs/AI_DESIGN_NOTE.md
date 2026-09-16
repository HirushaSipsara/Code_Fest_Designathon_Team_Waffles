# Intelligence design note

## Offline technique

LIVLINK's hackathon demo does not call an external LLM. Natural-language scene requests are matched against 15 transparent seeded intent groups, then converted into the same strict `SceneProposal` schema used by the scene workflow. Energy intelligence uses a seven-day baseline and deviation threshold; predictive maintenance uses a documented weighted risk score; learned automation counts actions that follow at least three of the last five arrival episodes.

These are deterministic prototype techniques—not a trained model. They demonstrate the product workflow without an API key, network dependency, accuracy claim or hidden fallback.

## Validation and human control

Every generated scene is checked against known device IDs, device/action compatibility, value ranges and resident policy. The resident reviews a proposal before saving it. Insight suggestions are validated through the same scene and policy rules when accepted; an unsafe unlock action is rejected. Only the automation engine can call `DeviceService`.

## Data and simulation

The backend seeds realistic device telemetry, battery decline and arrival/action history. A background simulator publishes events to an in-process `asyncio.Queue`; the subscriber persists them and runs deterministic analyses. No physical hardware or external MQTT broker is connected.

## Limitations

- The natural-language matcher supports only the documented seeded phrases and prototype devices.
- Analytics demonstrate workflows; they do not claim learned accuracy or production prediction quality.
- Device commands and sensor events are simulated.
- Production could replace the event bus and seeded logic behind the existing interfaces without changing the UI workflow.
