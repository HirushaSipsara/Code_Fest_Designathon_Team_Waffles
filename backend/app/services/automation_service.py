from datetime import datetime
from sqlalchemy.orm import Session
from app.models.entities import Scene
from app.schemas.scene import CommandResult, SceneAction
from app.services.activity_service import record
from app.services.device_service import DeviceService


def _conditions_pass(conditions: list[dict], at_time: str) -> bool:
    return all(condition["type"] != "time_after" or at_time >= condition["value"] for condition in conditions)


def handle_arrival(db: Session, at_time: str | None = None, device_service: DeviceService | None = None) -> dict:
    now = at_time or datetime.now().strftime("%H:%M")
    service = device_service or DeviceService()
    record(db, f"SIMULATED_ARRIVAL — {now}", "ok")
    executions: list[dict] = []
    for scene in db.query(Scene).all():
        if scene.trigger.get("type") != "resident_arrives" or not _conditions_pass(scene.conditions, now):
            continue
        record(db, f"SCENE_TRIGGERED — {scene.name}", "ok")
        results: list[CommandResult] = []
        for raw in scene.actions:
            action = SceneAction.model_validate(raw)
            record(db, f"DEVICE_COMMAND_REQUESTED — {action.device_id} {action.action}", "ok")
            result = service.execute(db, action)
            event_name = "DEVICE_COMMAND_ACKNOWLEDGED" if result.status == "acknowledged" else "DEVICE_COMMAND_FAILED"
            record(db, f"{event_name} — {action.device_id} {action.action}", "ok" if result.status == "acknowledged" else "warn")
            results.append(result)
        executions.append({"scene_id": scene.id, "scene_name": scene.name, "results": [{"device_id": item.device_id, "action": item.action, "transitions": ["requested", item.status], "status": item.status, "detail": item.detail} for item in results]})
    return {"simulated": True, "at_time": now, "executions": executions}
