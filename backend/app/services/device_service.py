import time
from sqlalchemy.orm import Session
from app.models.entities import Device
from app.schemas.scene import CommandResult, SceneAction


def supported_devices(db: Session) -> list[dict]:
    return [{"id": d.id, "name": d.name, "kind": d.kind, "room": d.room, "state": d.state} for d in db.query(Device).all()]


def validate_action(db: Session, action: SceneAction) -> str | None:
    device = db.get(Device, action.device_id)
    if not device:
        return f"Unknown LIVLINK device: {action.device_id}."
    requirements = {
        "set_temperature": ("ac", lambda v: isinstance(v, int) and 16 <= v <= 32),
        "set_level": (("light", "curtain"), lambda v: isinstance(v, int) and 0 <= v <= 100),
        "turn_on": (("light", "tv"), lambda v: v is None),
        "turn_off": (("light", "tv"), lambda v: v is None),
        "lock": ("lock", lambda v: v is None),
    }
    required = requirements.get(action.action)
    if not required:
        return f"Unsupported scene action: {action.action}."
    kinds, value_ok = required
    if not isinstance(kinds, tuple):
        kinds = (kinds,)
    if device.kind not in kinds:
        return f"{action.action} is not supported by {device.name}."
    if not value_ok(action.value):
        return f"Invalid value for {action.action}."
    return None


def execute_simulated(db: Session, action: SceneAction) -> CommandResult:
    """The only device adapter in this hackathon build. It intentionally models acknowledgement."""
    error = validate_action(db, action)
    if error:
        return CommandResult(device_id=action.device_id, action=action.action, status="failed", detail=error)
    device = db.get(Device, action.device_id)
    time.sleep(0.12)  # explicit simulated device latency
    state = dict(device.state)
    if action.action == "set_temperature":
        state.update(on=True, temperature=action.value)
    elif action.action == "set_level":
        state.update(on=(action.value or 0) > 0, level=action.value)
    elif action.action == "turn_on":
        state["on"] = True
    elif action.action == "turn_off":
        state["on"] = False
    elif action.action == "lock":
        state["locked"] = True
    device.state = state
    db.add(device)
    db.commit()
    return CommandResult(device_id=device.id, action=action.action, status="acknowledged", detail="Simulated device acknowledged command")
