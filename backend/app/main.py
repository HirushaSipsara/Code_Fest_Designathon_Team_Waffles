from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.scenes import router
from app.core.config import get_settings
from app.db.seed import seed_devices
from app.db.session import SessionLocal, engine
from app.models.entities import Base


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed_devices(db)
    yield


settings = get_settings()
app = FastAPI(title="LIVLINK API", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[item.strip() for item in settings.cors_origins.split(",")], allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
