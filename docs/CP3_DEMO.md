# CP3 offline demo sequence

1. Start PostgreSQL, FastAPI on port 8000 and React on port 5173. No external AI key or MQTT broker is required.
2. Open Resident **Home**. Show the Intelligence panel with energy, maintenance and automation cards.
3. Explain: seeded telemetry enters an in-process simulated event stream; the backend persists it and runs deterministic analysis.
4. Show the event-stream status indicator and `/api/mqtt/status` event count. Clarify that the endpoint name is retained for compatibility; transport is `in_process_simulation`.
5. Dismiss an insight and refresh to show that the status persists in PostgreSQL.
6. Accept **Welcome Home**. Show the saved scene and explain that the suggestion passed schema, device/action and policy validation before persistence.
7. Open **Scenes** and enter “Make my room comfortable for studying.” Show the seeded matcher proposal, review it, then confirm it.
8. Try an unsupported request. Show the honest clarification and manual builder.
9. Simulate resident arrival and show `Requested → Acknowledged` from mock devices.
10. State: “The frontend, backend, validation, deterministic analytics, persistence and automation are real. Device telemetry, sensors and hardware acknowledgements are simulated. No external AI model or physical hardware is connected.”
