# LIVLINK CP3 implementation

The approved `livlink-prototype.html` remains untouched and is now rendered in full by the React/Vite entry point. This preserves every original persona, screen, control and browser-simulated interaction instead of maintaining a reduced duplicate frontend. React adds the CP3 backend connection only at the existing natural-language scene composer; the rest of the approved prototype continues to run exactly from the source HTML.

See [docs/CP3_DEMO.md](docs/CP3_DEMO.md) for the short demonstration and [docs/FRONTEND_ANALYSIS.md](docs/FRONTEND_ANALYSIS.md) for the prototype inventory.

## Run the CP3 slice

1. Start PostgreSQL: `docker compose up -d postgres`
2. Create a Python virtual environment and install: `python -m venv .venv`, then `.\.venv\Scripts\python -m pip install -r backend\requirements.txt`.
3. Copy `backend/.env.example` to `backend/.env`. Set `AI_API_KEY` and `AI_MODEL` to use a genuine OpenAI-compatible parser; leave them blank to demonstrate the honest manual-builder fallback.
4. Apply the database migration: `cd backend; ..\.venv\Scripts\alembic upgrade head`.
5. Start the API: `..\.venv\Scripts\uvicorn app.main:app --reload --port 8000`.
6. In another terminal, copy `frontend/.env.example` to `frontend/.env`, then run `npm --prefix frontend install` and `npm --prefix frontend run dev`.

Run backend tests from the repository root with `set PYTHONPATH=%CD%\backend && python -m pytest backend\tests -q`.

The CP3 database has `devices`, `scene_drafts`, `scenes` and `activity_events`. The device path is explicitly `AutomationEngine → DeviceService → DeviceAdapter → MockDeviceAdapter`; there is no physical hardware.

On the current development host, a fresh npm download is blocked because the registry is re-issued by a Fortinet TLS appliance whose CA is not installed. TLS checks were not disabled. Build verification used the compatible React 18.3.1/Vite 6.4.3 packages already installed locally under `F:\Projects\Jarvis\node_modules` through a gitignored junction.
