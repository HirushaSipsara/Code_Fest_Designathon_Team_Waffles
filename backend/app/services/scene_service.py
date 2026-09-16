import uuid
from sqlalchemy.orm import Session
from app.core.permissions import validate_scene_permission
from app.models.entities import Scene
from app.schemas.scene import ProposalResponse, SceneProposal
from app.services.activity_service import record
from app.services.device_service import validate_action


def assess_proposal(db: Session, proposal: SceneProposal, role: str) -> ProposalResponse:
    if proposal.status != "ready":
        return ProposalResponse(**proposal.model_dump())
    for action in proposal.actions:
        reason = validate_action(db, action) or validate_scene_permission(role, action)
        if reason:
            return ProposalResponse(scene_name=proposal.scene_name, trigger=proposal.trigger, conditions=proposal.conditions, actions=[], status="rejected", explanation="LIVLINK did not create a scene from an unsafe or unsupported request.", reason=reason)
    proposal_id = getattr(proposal, "proposal_id", None) or str(uuid.uuid4())
    record(db, "AI scene proposal generated", "ok")
    return ProposalResponse(**proposal.model_dump(exclude={"proposal_id", "reason"}), proposal_id=proposal_id)


def save_scene(db: Session, proposal: SceneProposal, role: str) -> Scene:
    scene = Scene(name=proposal.scene_name, role=role, trigger=proposal.trigger.model_dump(), conditions=[item.model_dump() for item in proposal.conditions], actions=[item.model_dump() for item in proposal.actions])
    db.add(scene)
    db.commit()
    db.refresh(scene)
    record(db, f"Scene confirmed by resident — {scene.name}", "ok")
    return scene
