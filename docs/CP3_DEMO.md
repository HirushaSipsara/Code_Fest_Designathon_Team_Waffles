# CP3 demo and acceptance sequence

1. Set `AI_API_KEY` and `AI_MODEL` in `backend/.env`; set `AI_BASE_URL` only for a non-default OpenAI-compatible endpoint. Show that names are configured without revealing values.
2. Run PostgreSQL and `alembic upgrade head`; show revision `0002_scene_drafts`.
3. Run FastAPI visibly at port 8000 and React at port 5173.
4. Open React **Scenes** and enter: “When I get home after 8 PM, turn the bedroom light to 35% and cool the bedroom to 23°C.”
5. Click **Create**. In Network show `POST /api/ai/scenes/parse`. In the API terminal show: AI request received; Provider request started; Provider response received; Schema validation passed; Policy validation passed.
6. Review WHEN/IF/THEN, explanation and validation checks. No device changed yet.
7. Click **Confirm & Save**. Show the scene under **Saved scenes**, refresh, and show it remains.
8. Use **SIMULATION / DEMO ONLY — Simulate Resident Arrival** at a matching time. Show `Requested → Acknowledged`, then Devices and Activity.
9. Verify PostgreSQL: `SELECT id,name,trigger,conditions,actions FROM scenes;` and `SELECT message,created_at FROM activity_events ORDER BY id DESC LIMIT 20;`.
10. Enter “Order me pizza.” Expect unsupported/clarification and manual-builder fallback.
11. State: “The AI provider request, backend validation, automation logic and PostgreSQL persistence are real. The physical device layer and sensor event are simulated because no hardware is available.”

Without a key/model, step 5 must show `service_unavailable` with reason `AI provider is not configured`; do not claim the provider portion passed.
