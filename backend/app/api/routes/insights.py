"""REST API for AI insights, telemetry, and MQTT status."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session
from app.core.permissions import validate_scene_permission
from app.db.session import get_db
from app.models.entities import AIInsight, DeviceTelemetry, Scene
from app.mqtt.subscriber import mqtt_status
from app.schemas.scene import SceneProposal
from app.services.device_service import validate_action
from app.services.scene_service import save_scene

router = APIRouter(tags=["LIVLINK intelligence"])


@router.get("/insights")
def list_insights(db: Session = Depends(get_db)):
    """Return all active AI insight cards."""
    insights = (
        db.query(AIInsight)
        .filter(AIInsight.status == "active")
        .order_by(AIInsight.created_at.desc())
        .all()
    )
    return {
        "insights": [
            {
                "id": i.id,
                "category": i.category,
                "severity": i.severity,
                "title": i.title,
                "body": i.body,
                "device_id": i.device_id,
                "status": i.status,
                "created_at": i.created_at.isoformat() if i.created_at else None,
            }
            for i in insights
        ]
    }


@router.post("/insights/{insight_id}/dismiss")
def dismiss_insight(insight_id: int, db: Session = Depends(get_db)):
    """Dismiss an insight card."""
    insight = db.get(AIInsight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    if insight.status != "active":
        raise HTTPException(status_code=409, detail="Insight is no longer active")
    insight.status = "dismissed"
    db.commit()
    return {"id": insight.id, "status": "dismissed"}


@router.post("/insights/{insight_id}/apply")
def apply_insight(insight_id: int, db: Session = Depends(get_db)):
    """Apply an automation suggestion — creates a Scene from the insight."""
    insight = db.get(AIInsight, insight_id)
    if not insight:
        raise HTTPException(status_code=404, detail="Insight not found")
    if insight.status != "active":
        raise HTTPException(status_code=409, detail="Insight is no longer active")
    if insight.category != "automation":
        raise HTTPException(status_code=422, detail="Only automation insights can be applied")

    suggested = insight.body.get("suggested_scene", {})
    if not suggested:
        raise HTTPException(status_code=422, detail="No suggested scene in this insight")

    try:
        proposal = SceneProposal.model_validate({
            **suggested,
            "status": "ready",
            "explanation": "Resident accepted a seeded automation suggestion.",
        })
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid suggested scene") from exc
    if not proposal.actions or len(proposal.conditions) != 1:
        raise HTTPException(status_code=422, detail="Suggestion needs an arrival time and actions")
    for action in proposal.actions:
        reason = validate_action(db, action) or validate_scene_permission("owner", action)
        if reason:
            raise HTTPException(status_code=422, detail=reason)

    scene = save_scene(db, proposal, "owner")
    insight.status = "applied"
    db.commit()
    return {"id": scene.id, "name": scene.name, "status": "applied"}


@router.get("/telemetry/{device_id}")
def device_telemetry(device_id: str, db: Session = Depends(get_db)):
    """Return recent telemetry readings for a device."""
    readings = (
        db.query(DeviceTelemetry)
        .filter(DeviceTelemetry.device_id == device_id)
        .order_by(DeviceTelemetry.timestamp.desc())
        .limit(20)
        .all()
    )
    return {
        "device_id": device_id,
        "readings": [
            {
                "id": r.id,
                "event_type": r.event_type,
                "payload": r.payload,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            }
            for r in readings
        ],
    }


@router.get("/telemetry/summary/all")
def telemetry_summary(db: Session = Depends(get_db)):
    """Return latest energy reading per device for the dashboard."""
    devices = ["ac", "bac", "light", "blight", "klight"]
    summary = []
    for dev_id in devices:
        latest = (
            db.query(DeviceTelemetry)
            .filter(DeviceTelemetry.device_id == dev_id, DeviceTelemetry.event_type == "energy")
            .order_by(DeviceTelemetry.timestamp.desc())
            .first()
        )
        if latest:
            summary.append({
                "device_id": dev_id,
                "power": latest.payload.get("power"),
                "timestamp": latest.timestamp.isoformat() if latest.timestamp else None,
            })
    return {"summary": summary}


@router.get("/mqtt/status")
def get_mqtt_status():
    """Return in-process simulated event-stream status and event count."""
    return mqtt_status()
