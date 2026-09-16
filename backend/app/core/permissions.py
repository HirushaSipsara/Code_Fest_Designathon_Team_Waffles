from app.schemas.scene import SceneAction

# The prototype explicitly keeps everyday device control open to all three resident roles.
# This allowlist additionally prevents an AI proposal from unlocking a door.
RESIDENT_ROLES = {"owner", "occupier", "tenant"}
AI_ALLOWED_ACTIONS = {"set_temperature", "set_level", "turn_on", "turn_off", "lock"}


def validate_scene_permission(role: str, action: SceneAction) -> str | None:
    if role not in RESIDENT_ROLES:
        return "This account does not have a supported resident role."
    if action.action not in AI_ALLOWED_ACTIONS:
        return "That action is not allowed in an AI-created scene."
    if action.action == "unlock":
        return "AI-created scenes cannot unlock a door."
    return None
