# LIVLINK CP3 implementation

The approved `livlink-prototype.html` remains untouched as the visual product reference. This repository now contains a React/Vite implementation of the CP3 end-to-end AI scene slice and a FastAPI modular-monolith backend.

See [docs/CP3_DEMO.md](docs/CP3_DEMO.md) for the short demonstration and [docs/FRONTEND_ANALYSIS.md](docs/FRONTEND_ANALYSIS.md) for the prototype inventory.

## Run the CP3 slice

1. Start PostgreSQL: `docker compose up -d postgres`
2. Create a Python virtual environment and install: `python -m venv .venv`, then `.\.venv\Scripts\python -m pip install -r backend\requirements.txt`.
3. Copy `backend/.env.example` to `backend/.env`. Set `AI_API_KEY` and `AI_MODEL` to use a genuine OpenAI-compatible parser; leave them blank to demonstrate the honest manual-builder fallback.
4. Apply the database migration: `cd backend; ..\.venv\Scripts\alembic upgrade head`.
5. Start the API: `..\.venv\Scripts\uvicorn app.main:app --reload --port 8000`.
6. In another terminal, copy `frontend/.env.example` to `frontend/.env`, then run `npm --prefix frontend install` and `npm --prefix frontend run dev`.

Run backend tests from the repository root with `set PYTHONPATH=%CD%\backend && python -m pytest backend\tests -q`.

The CP3 database has three tables: `devices`, `scenes` and `activity_events`. The only physical-device substitute is the explicitly simulated `DeviceService` adapter.
