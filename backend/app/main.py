import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.scenes import router
from app.api.routes.insights import router as insights_router
from app.core.config import get_settings
from app.db.seed import seed_devices, seed_telemetry, seed_resident_events, seed_insights
from app.db.session import SessionLocal
from app.models.entities import Base
from app.db.session import engine
from app.mqtt.bus import reset_bus


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Create all tables (including new telemetry/insight tables)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        seed_devices(db)
        seed_telemetry(db)
        seed_resident_events(db)
        seed_insights(db)

    # A queue belongs to one event loop; TestClient and reloads start new lifespans.
    reset_bus()
    # Start subscriber + simulator as background tasks (share in-process bus)
    subscriber_task = asyncio.create_task(_start_mqtt())
    simulator_task = asyncio.create_task(_start_simulator())
    yield
    subscriber_task.cancel()
    simulator_task.cancel()
    for task in (subscriber_task, simulator_task):
        try:
            await task
        except asyncio.CancelledError:
            pass


async def _start_mqtt() -> None:
    """Start the MQTT subscriber; uses in-process bus, no broker needed."""
    from app.mqtt.subscriber import start_subscriber
    settings = get_settings()
    await start_subscriber(settings.mqtt_broker_host, settings.mqtt_broker_port, SessionLocal)


async def _start_simulator() -> None:
    """Start the MQTT simulator; publishes to the same in-process bus."""
    from app.simulator.mqtt_simulator import run_simulator
    await run_simulator()


settings = get_settings()
logging.getLogger("app").setLevel(logging.INFO)
app = FastAPI(title="LIVLINK API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[item.strip() for item in settings.cors_origins.split(",")], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
app.include_router(insights_router, prefix="/api")
