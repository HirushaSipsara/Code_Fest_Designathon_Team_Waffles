import os
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_livlink.db")
os.environ.pop("AI_API_KEY", None)
os.environ.pop("AI_MODEL", None)

import pytest
from app.db.session import engine
from app.models.entities import Base

@pytest.fixture(autouse=True)
def database_schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)
