# CP3 audit — 2026-09-16

This is a source-and-runtime audit, not a completion certificate. The React app is running at `http://127.0.0.1:5173/`, and the browser visibly loaded backend device state and the no-key AI fallback. No AI key/model exists on this host, so a live provider request has **not** been demonstrated.

| Stage | Classification | Trace / verification |
|---|---|---|
| Frontend NL input | REAL | `frontend/src/App.tsx` `Scenes`; observed in the running React page. |
| Frontend API request | REAL for no-key path | `frontend/src/api.ts` posts `/api/ai/scenes/parse`; browser received backend reason `AI provider is not configured`. |
| FastAPI route | REAL | `backend/app/api/routes/scenes.py` `parse_scene`. |
| AI provider abstraction | REAL code | `AIService → AIProvider → OpenAICompatibleProvider`. |
| AI provider request | NOT VERIFIED LIVE | Compatible `/chat/completions` request exists; host has no `AI_API_KEY`/`AI_MODEL`. |
| AI output parsing | REAL under stub; NOT VERIFIED LIVE | `SceneProposal.model_validate_json`; provider parsing and invalid-output tests pass. |
| Pydantic validation | REAL | strict `extra=forbid`; invalid condition/extra fields tested. |
| Policy validation | REAL | device/action/range and resident policy tested. Role is prototype context, not authenticated. |
| Scene persistence | REAL under integration test | Server-issued `scene_drafts`, confirmed `scenes`, `GET /api/scenes`; PostgreSQL live path migrated. |
| Confirmation flow | REAL under stub; NOT VERIFIED with live provider | Fabricated frontend proposal is rejected; confirmed server draft is stored. |
| Automation engine | REAL deterministic code | Loads scenes, matches arrival/time, calls `DeviceService`; tested at `20:00`. |
| Arrival event | SIMULATED | `POST /api/simulation/resident-arrival`; no physical sensor. |
| Device layer | SIMULATED, clean boundary | `DeviceService → DeviceAdapter → MockDeviceAdapter`; PostgreSQL state. |
| Acknowledgement | SIMULATED, explicit lifecycle | API returns `transitions: [requested, acknowledged/failed]`; React renders it. |
| Frontend device update | REAL | Browser observed devices from `/api/devices`; React reloads after arrival acknowledgement. |
| Audit log | REAL | PostgreSQL `activity_events`; `/api/activity`; command audit test passes. |
| PostgreSQL | REAL/live | Alembic revision `0002_scene_drafts` and 9 seeded devices verified in the running container. Automated tests intentionally isolate with SQLite. |
| Complete prototype frontend | REAL | React renders the full untouched `livlink-prototype.html`; Resident, Visitor, Operator, Developer and all original screens/interactions were exercised in the running browser. |
| Manual builder fallback | REAL browser simulation | The original tap/keyboard/drag scene builder is present in React because the complete prototype is rendered; saving a scene card was exercised in the running browser. It remains a browser simulation, not durable backend persistence. |
| React build | PASS using local compatible dependencies | `npm run build` passes with React 18.3.1/Vite 6.4.3 from an existing local toolchain. Fresh npm install remains blocked by a Fortinet-issued TLS chain whose CA is absent. |

The old static prototype still contains `NL_MAP`; it is **not** the CP3 AI execution path. Automated tests prove the full application path using a stub provider, as is appropriate for tests. The A–P acceptance test remains incomplete until a provider key/model is configured and the live call is observed.
