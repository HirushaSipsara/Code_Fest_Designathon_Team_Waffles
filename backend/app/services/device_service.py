from sqlalchemy.orm import Session
from app.models.entities import Device
from app.schemas.scene import CommandResult, SceneAction
from app.simulator.device_adapter import DeviceAdapter, MockDeviceAdapter


def supported_devices(db: Session) -> list[dict]:
    return [{"id": d.id, "name": d.name, "kind": d.kind, "room": d.room, "state": d.state} for d in db.query(Device).all()]


def validate_action(db: Session, action: SceneAction) -> str | None:
    device = db.get(Device, action.device_id)
    if not device:
        return f"Unknown LIVLINK device: {action.device_id}."
    requirements = {
        "set_temperature": ("ac", lambda v: isinstance(v, int) and 16 <= v <= 32),
        "set_level": (("light", "curtain"), lambda v: isinstance(v, int) and 0 <= v <= 100),
        "turn_on": (("ac", "light", "tv"), lambda v: v is None),
        "turn_off": (("ac", "light", "tv"), lambda v: v is None),
        "lock": ("lock", lambda v: v is None),
        "unlock": ("lock", lambda v: v is None),
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


class DeviceService:
    def __init__(self, adapter: DeviceAdapter | None = None):
        self.adapter = adapter or MockDeviceAdapter()

    def execute(self, db: Session, action: SceneAction) -> CommandResult:
        error = validate_action(db, action)
        if error:
            return CommandResult(device_id=action.device_id, action=action.action, status="failed", detail=error)
        device = db.get(Device, action.device_id)
        try:
            reply = self.adapter.send(action, dict(device.state))
        except Exception:
            return CommandResult(device_id=device.id, action=action.action, status="failed", detail="Simulated device unavailable")
        if not reply.acknowledged:
            return CommandResult(device_id=device.id, action=action.action, status="failed", detail=reply.detail)
        device.state = reply.state
        db.add(device)
        db.commit()
        return CommandResult(device_id=device.id, action=action.action, status="acknowledged", detail=reply.detail)


def execute_simulated(db: Session, action: SceneAction) -> CommandResult:
    """Compatibility entry point; automation uses DeviceService directly."""
    return DeviceService().execute(db, action)
