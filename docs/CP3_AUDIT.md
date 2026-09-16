# CP3 audit — 2026-09-16

This is a source-and-runtime audit, not a completion certificate. The hackathon configuration is intentionally offline: seeded natural-language matching and deterministic analytics run without an external model or broker.

| Stage | Classification | Trace / verification |
|---|---|---|
| Frontend NL input | REAL | `frontend/src/App.tsx` `Scenes`; observed in the running React page. |
| Frontend API request | REAL/local | `frontend/src/api.ts` calls the local FastAPI scene and insight routes. |
| FastAPI route | REAL | `backend/app/api/routes/scenes.py` `parse_scene`. |
| Natural-language matching | SEEDED / OFFLINE | Fifteen transparent phrase groups create constrained proposals; no LLM call is claimed. |
| Intelligence analytics | REAL deterministic code | Energy deviation, maintenance risk score and arrival-pattern counting operate on seeded plus simulated telemetry. |
| Event transport | SIMULATED | Shared in-process `asyncio.Queue`; no Mosquitto broker is required. |
| Pydantic validation | REAL | strict `extra=forbid`; invalid condition/extra fields tested. |
| Policy validation | REAL | device/action/range and resident policy tested. Role is prototype context, not authenticated. |
| Scene persistence | REAL under integration test | Server-issued `scene_drafts`, confirmed `scenes`, `GET /api/scenes`; PostgreSQL live path migrated. |
| Confirmation flow | REAL | Fabricated frontend proposals are rejected; confirmed server drafts and accepted insight scenes are stored. |
| Automation engine | REAL deterministic code | Loads scenes, matches arrival/time, calls `DeviceService`; tested at `20:00`. |
| Arrival event | SIMULATED | `POST /api/simulation/resident-arrival`; no physical sensor. |
| Device layer | SIMULATED, clean boundary | `DeviceService → DeviceAdapter → MockDeviceAdapter`; PostgreSQL state. |
| Acknowledgement | SIMULATED, explicit lifecycle | API returns `transitions: [requested, acknowledged/failed]`; React renders it. |
| Frontend device update | REAL | Browser observed devices from `/api/devices`; React reloads after arrival acknowledgement. |
| Audit log | REAL | PostgreSQL `activity_events`; `/api/activity`; command audit test passes. |
| PostgreSQL | REAL/live | Alembic revision `0002_scene_drafts` and 9 seeded devices verified in the running container. Automated tests intentionally isolate with SQLite. |
| Complete prototype frontend | REAL | React renders the full `livlink-prototype.html`; Resident, Visitor, Operator, Developer and all original screens/interactions were exercised in the running browser. |
| Manual builder fallback | REAL browser simulation | The original tap/keyboard/drag scene builder is present in React because the complete prototype is rendered; saving a scene card was exercised in the running browser. It remains a browser simulation, not durable backend persistence. |
| React build | PASS using local compatible dependencies | `npm run build` passes with React 18.3.1/Vite 6.4.3 from an existing local toolchain. Fresh npm install remains blocked by a Fortinet-issued TLS chain whose CA is absent. |

The original prototype phrase map is not the backend execution path. The backend seeded matcher, validation, insight pipeline, scene persistence and simulated-device acknowledgement are covered by the automated suite. No provider call is part of the current demo claim.
