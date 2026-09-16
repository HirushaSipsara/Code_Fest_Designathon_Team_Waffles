# CP3 evidence

## Real

- Complete React frontend and local FastAPI integration
- PostgreSQL persistence for telemetry, insights, scenes, drafts and audit events
- Pydantic schema validation and deterministic device/policy validation
- Energy baseline/anomaly calculation
- Predictive-maintenance weighted risk scoring
- Learned-automation frequency counting
- Scene confirmation and automation engine
- Device abstraction and acknowledgement lifecycle

## Seeded or simulated

- Seven-day energy history, battery decline and arrival/action patterns
- In-process device event stream
- AC, lights, curtains, locks, TV and sensor events
- Resident arrival, visitor scanner and camera feed
- Natural-language intent matching (15 seeded phrase groups; no LLM)

## Verified path

The simulator publishes to the shared in-process bus. The subscriber persists telemetry and invokes deterministic analysis services. React polls the local `/api/insights` and status endpoints, then lets the user dismiss insights or accept a validated automation proposal. Automated tests cover route registration, insight persistence, one-time scene creation, unsafe-action rejection, scene confirmation and simulated command acknowledgement.

## Honest limitations

This demo has no external AI provider, API key, physical hardware or network MQTT broker. It demonstrates a credible end-to-end workflow using deterministic seeded logic. Production paths remain replaceable behind `DeviceAdapter` and the event-bus boundary.
