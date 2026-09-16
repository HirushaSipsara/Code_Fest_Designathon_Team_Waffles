from datetime import datetime
from sqlalchemy.orm import Session
from app.models.entities import Scene
from app.schemas.scene import CommandResult, SceneAction
from app.services.activity_service import record
from app.services.device_service import execute_simulated


def _conditions_pass(conditions: list[dict], at_time: str) -> bool:
    return all(condition["type"] != "time_after" or at_time >= condition["value"] for condition in conditions)


def handle_arrival(db: Session, at_time: str | None = None) -> dict:
    now = at_time or datetime.now().strftime("%H:%M")
    record(db, f"Resident arrival simulated at {now}", "ok")
    executions: list[dict] = []
    for scene in db.query(Scene).all():
        if scene.trigger.get("type") != "resident_arrives" or not _conditions_pass(scene.conditions, now):
            continue
        record(db, f"{scene.name} triggered", "ok")
        results: list[CommandResult] = []
        for raw in scene.actions:
            action = SceneAction.model_validate(raw)
            record(db, f"{action.device_id} requested — {action.action}", "ok")
            result = execute_simulated(db, action)
            record(db, f"{action.device_id} {result.status}", "ok" if result.status == "acknowledged" else "warn")
            results.append(result)
        executions.append({"scene_id": scene.id, "scene_name": scene.name, "results": [item.model_dump() for item in results]})
    return {"simulated": True, "at_time": now, "executions": executions}
