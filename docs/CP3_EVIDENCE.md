# CP3 evidence

| Criterion | Implemented evidence | Demonstration | Classification |
|---|---|---|---|
| End-to-end slice running | `frontend/src/App.tsx`, `backend/app/api/routes/scenes.py` | Parse → review → confirm → arrival | REAL, except device layer |
| Simulation identified | visible `SIMULATION / DEMO ONLY` control; `device_service.py`; `SIMULATION.md` | Trigger arrival and inspect acknowledgement | SIMULATED |
| Components integrated | AI, schema, policy, DB, automation, simulator, audit services | inspect activity after arrival | REAL integration |
| Coherent architecture | `ARCHITECTURE.md`, modular backend services | trace REST path | REAL |
| AI solves a problem | `AI_DESIGN_NOTE.md`, `ai_service.py` | submit a supported natural-language request with configured provider | REAL when key/model configured |
| AI in workflow | proposal review and explicit confirmation | show no device changes before confirmation | REAL |
| Data/limitations/fallback | `AI_DESIGN_NOTE.md`, parser statuses, manual-builder message | unset AI key or enter unsupported request | REAL boundary |
| Clear completion path | below | explain adapters and governance | planned |

## Clear path to completion

- **Current hackathon implementation:** backend `DeviceService` simulator. **Next pilot:** a real IoT gateway/MQTT adapter behind the same service.
- **Current AI:** cloud LLM structured parser. **Next pilot:** monitoring, evaluation dataset and provider/model governance.
- **Current auth:** prototype resident role context. **Next pilot:** identity provider and secure token lifecycle.
