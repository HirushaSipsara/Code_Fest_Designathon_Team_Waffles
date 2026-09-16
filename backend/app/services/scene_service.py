import uuid
import logging
from sqlalchemy.orm import Session
from app.core.permissions import validate_scene_permission
from app.models.entities import Scene, SceneDraft
from app.schemas.scene import ProposalResponse, SceneProposal
from app.services.activity_service import record
from app.services.device_service import validate_action

logger = logging.getLogger("uvicorn.error")


def assess_proposal(db: Session, proposal: SceneProposal, role: str) -> ProposalResponse:
    if proposal.status != "ready":
        return ProposalResponse(**proposal.model_dump())
    if not proposal.actions or len(proposal.conditions) != 1:
        return ProposalResponse(**proposal.model_dump(exclude={"proposal_id", "reason", "status", "actions", "explanation"}), status="needs_clarification", actions=[], explanation="Specify an arrival time and supported actions before saving.")
    for action in proposal.actions:
        reason = validate_action(db, action) or validate_scene_permission(role, action)
        if reason:
            logger.warning("Policy validation failed")
            return ProposalResponse(scene_name=proposal.scene_name, trigger=proposal.trigger, conditions=proposal.conditions, actions=[], status="rejected", explanation="LIVLINK did not create a scene from an unsafe or unsupported request.", reason=reason)
    proposal_id = getattr(proposal, "proposal_id", None) or str(uuid.uuid4())
    logger.info("Policy validation passed")
    if not getattr(proposal, "proposal_id", None):
        db.add(SceneDraft(id=proposal_id, role=role, proposal=proposal.model_dump(exclude={"reason"})))
        db.commit()
        record(db, "AI_SCENE_PROPOSED", "ok")
    return ProposalResponse(**proposal.model_dump(exclude={"proposal_id", "reason"}), proposal_id=proposal_id)


def save_scene(db: Session, proposal: SceneProposal, role: str) -> Scene:
    scene = Scene(name=proposal.scene_name, role=role, trigger=proposal.trigger.model_dump(), conditions=[item.model_dump() for item in proposal.conditions], actions=[item.model_dump() for item in proposal.actions])
    db.add(scene)
    db.commit()
    db.refresh(scene)
    record(db, f"SCENE_CONFIRMED — {scene.name}", "ok")
    record(db, f"SCENE_SAVED — id {scene.id}", "ok")
    return scene


def confirmed_draft(db: Session, proposal: ProposalResponse, role: str) -> SceneDraft | None:
    draft = db.get(SceneDraft, proposal.proposal_id) if proposal.proposal_id else None
    if not draft or draft.consumed or draft.role != role:
        return None
    if draft.proposal != proposal.model_dump(exclude={"proposal_id", "reason"}):
        return None
    return draft
