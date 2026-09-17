# LIVLINK CP3 implementation

The approved `livlink-prototype.html` is rendered in full by the React/Vite entry point. This preserves every original persona, screen, control and browser-simulated interaction instead of maintaining a reduced duplicate frontend. The current source also contains the Intelligence panel placeholder; React connects that panel and the existing natural-language scene composer to the local backend.

## Live demo

Open the deployed demo: [http://3.110.83.150](http://3.110.83.150)

The current EC2 demonstration endpoint uses HTTP. The device layer is simulated for this demo.

See [docs/CP3_DEMO.md](docs/CP3_DEMO.md) for the short demonstration and [docs/FRONTEND_ANALYSIS.md](docs/FRONTEND_ANALYSIS.md) for the prototype inventory.

## Run the CP3 slice

1. Start PostgreSQL: `docker compose up -d postgres`
2. Create a Python virtual environment and install: `python -m venv .venv`, then `.\.venv\Scripts\python -m pip install -r backend\requirements.txt`.
3. Copy `backend/.env.example` to `backend/.env`. The hackathon demo is fully offline: `AI_USE_SEEDED=true` uses the seeded natural-language matcher and deterministic analytics. No external AI key or device broker is required.
4. Apply the database migration: `cd backend; ..\.venv\Scripts\alembic upgrade head`.
5. Start the API: `..\.venv\Scripts\uvicorn app.main:app --reload --port 8000`.
6. In another terminal, copy `frontend/.env.example` to `frontend/.env`, then run `npm --prefix frontend install` and `npm --prefix frontend run dev`.

Run backend tests from the repository root with `set PYTHONPATH=%CD%\backend && python -m pytest backend\tests -q`.

The CP3 database also stores telemetry, resident events and insight cards. Device events use an in-process simulated stream; the command path remains `AutomationEngine → DeviceService → DeviceAdapter → MockDeviceAdapter`. There is no physical hardware, external AI provider or MQTT broker in the demo.

On the current development host, a fresh npm download is blocked because the registry is re-issued by a Fortinet TLS appliance whose CA is not installed. TLS checks were not disabled. Build verification used the compatible React 18.3.1/Vite 6.4.3 packages already installed locally under `F:\Projects\Jarvis\node_modules` through a gitignored junction.
