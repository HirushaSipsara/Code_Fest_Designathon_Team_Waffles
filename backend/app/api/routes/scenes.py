from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.scene import ArrivalRequest, ConfirmRequest, ParseRequest, ProposalResponse
from app.services.activity_service import recent
from app.services.ai_service import AIService
from app.services.automation_service import handle_arrival
from app.services.device_service import supported_devices
from app.services.scene_service import assess_proposal, save_scene

router = APIRouter(prefix="/api", tags=["LIVLINK scenes"])


@router.get("/health")
def health():
    return {"status": "ok", "device_layer": "simulated"}


@router.get("/devices")
def devices(db: Session = Depends(get_db)):
    return {"simulated": True, "devices": supported_devices(db)}


@router.post("/ai/scenes/parse", response_model=ProposalResponse)
def parse_scene(payload: ParseRequest, db: Session = Depends(get_db)):
    proposal = AIService().parse_scene_request(payload.request, supported_devices(db), payload.role)
    return assess_proposal(db, proposal, payload.role)


@router.post("/scenes/confirm")
def confirm_scene(payload: ConfirmRequest, db: Session = Depends(get_db)):
    checked = assess_proposal(db, payload.proposal, payload.role)
    if checked.status != "ready":
        raise HTTPException(status_code=422, detail=checked.reason or "Only a safe, ready proposal may be confirmed.")
    scene = save_scene(db, payload.proposal, payload.role)
    return {"id": scene.id, "name": scene.name, "status": "confirmed"}


@router.post("/simulation/resident-arrival")
def simulate_arrival(payload: ArrivalRequest, db: Session = Depends(get_db)):
    return handle_arrival(db, payload.at_time)


@router.get("/activity")
def activity(db: Session = Depends(get_db)):
    return {"events": [{"id": item.id, "message": item.message, "category": item.category, "created_at": item.created_at.isoformat() if item.created_at else None} for item in recent(db)]}
