# CP3 evidence

-----------------------------------
## 1. END-TO-END SLICE RUNNING
-----------------------------------

Evidence: React `frontend/src/App.tsx` calls `frontend/src/api.ts`, then FastAPI `POST /api/ai/scenes/parse`. `AIService` calls the provider, Pydantic and policy validate, `/api/scenes/confirm` stores a server-issued draft in PostgreSQL, and `/api/simulation/resident-arrival` runs automation through `DeviceService`. React reloads `/api/devices` and `/api/activity` after acknowledgement.

Current verification: the React → FastAPI no-key fallback, PostgreSQL device reads, build, migrations and stubbed full workflow pass. A real provider call cannot be certified on this host because `AI_API_KEY` and `AI_MODEL` are absent.

-----------------------------------
## 2. SIMULATION CLEARLY IDENTIFIED
-----------------------------------

**Simulated:** AC, lights, curtains, lock, TV, sensor/arrival event, and prototype scanner/camera feed.

**Real:** React code and HTTP requests, FastAPI, PostgreSQL, Pydantic validation, policy logic, automation orchestration and audit persistence. The provider HTTP implementation is real, but a live call is unverified without credentials.

**Seeded:** device catalogue, historical behaviour, energy examples, fleet data, developer metrics and provider few-shot examples. Few-shot examples support a real LLM and are not phrase matching or training data.

-----------------------------------
## 3. COMPONENTS INTEGRATED
-----------------------------------

React calls FastAPI; FastAPI calls `AIService`; `AIService` calls `AIProvider`; scene confirmation calls PostgreSQL; automation calls `DeviceService`; `DeviceService` calls `MockDeviceAdapter`; acknowledged state returns to React through `/api/devices`. Automated integration test: `backend/tests/test_scene_flow.py::test_api_parse_confirm_execute`.

-----------------------------------
## 4. COHERENT ARCHITECTURE
-----------------------------------

See `docs/ARCHITECTURE.md`. AI is separated from execution so model output cannot directly control devices. A server-issued persisted draft prevents a fabricated client proposal from being confirmed.

-----------------------------------
## 5. AI SOLVES GENUINE PROBLEM
-----------------------------------

Residents should not need rule syntax or manually configure every device. The LLM translates natural language into a constrained, reviewable automation proposal.

-----------------------------------
## 6. AI INTEGRATED INTO WORKFLOW
-----------------------------------

The output is not a chatbot answer: structured actions become a persisted scene only after deterministic validation and explicit resident confirmation, then the automation engine can execute it on a matching simulated event.

-----------------------------------
## 7. DATA / LIMITATIONS / FALLBACK
-----------------------------------

Data sent: request, supported device catalogue/actions, trigger/condition, role and few-shot examples. Limitations: known devices/actions only, one arrival trigger/condition, ambiguous language, provider dependency, prototype role context and simulated IoT. Fallback: a visible service-unavailable/clarification state points to the approved manual builder. The builder remains implemented in the untouched prototype, not yet ported into React.

-----------------------------------
## 8. CLEAR PATH TO COMPLETION
-----------------------------------

Today: `DeviceService → MockDeviceAdapter`. Future: `DeviceService → MQTTDeviceAdapter → Real IoT Gateway`.

Today: prototype role context. Future: authenticated identity provider and server-derived permissions.

Today: seeded energy history. Future: live telemetry.
