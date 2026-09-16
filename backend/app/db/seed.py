from sqlalchemy.orm import Session
from app.models.entities import Device
from app.db.session import SessionLocal

DEVICES = [
    ("ac", "Air Conditioner", "ac", "Living Room", {"on": True, "temperature": 25}),
    ("light", "Ceiling Light", "light", "Living Room", {"on": True, "level": 70}),
    ("tv", "Television", "tv", "Living Room", {"on": False}),
    ("curtain", "Curtains", "curtain", "Living Room", {"on": True, "level": 40}),
    ("lock", "Front Door Lock", "lock", "Living Room", {"locked": True}),
    ("bac", "Air Conditioner", "ac", "Bedroom", {"on": False, "temperature": 24}),
    ("blight", "Bedside Lamp", "light", "Bedroom", {"on": False, "level": 20}),
    ("bcurtain", "Curtains", "curtain", "Bedroom", {"on": True, "level": 0}),
    ("klight", "Counter Light", "light", "Kitchen", {"on": True, "level": 60}),
]


def seed_devices(db: Session) -> None:
    if db.query(Device).count():
        return
    db.add_all(Device(id=id, name=name, kind=kind, room=room, state=state) for id, name, kind, room, state in DEVICES)
    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_devices(session)
    print("LIVLINK prototype device catalogue seeded.")
