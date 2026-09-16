from fastapi.testclient import TestClient
from app.main import app
from app.schemas.scene import SceneAction, SceneProposal
from app.services.ai_service import AIService
from app.services.automation_service import _conditions_pass
from app.services.device_service import execute_simulated, validate_action
from app.db.session import SessionLocal
from app.db.seed import seed_devices
from app.models.entities import Device
from app.core.permissions import validate_scene_permission


def proposal() -> SceneProposal:
    return SceneProposal(scene_name="Evening Arrival", trigger={"type": "resident_arrives"}, conditions=[{"type": "time_after", "value": "19:00"}], actions=[{"device_id": "ac", "action": "set_temperature", "value": 24}, {"device_id": "light", "action": "turn_on"}], status="ready", explanation="Prepares the home after 7 PM.")


def test_schema_rejects_malformed_condition():
    try:
        SceneProposal(scene_name="Bad", trigger={"type": "resident_arrives"}, conditions=[{"type": "time_after", "value": "tonight"}], actions=[], status="needs_clarification", explanation="Need a time.")
        assert False, "invalid time was accepted"
    except ValueError:
        assert True


def test_unsupported_device_is_rejected():
    with SessionLocal() as db:
        seed_devices(db)
        assert validate_action(db, SceneAction(device_id="hallway-light", action="turn_on")) == "Unknown LIVLINK device: hallway-light."


def test_simulator_changes_state_and_acknowledges():
    with SessionLocal() as db:
        seed_devices(db)
        result = execute_simulated(db, SceneAction(device_id="ac", action="set_temperature", value=24))
        assert result.status == "acknowledged"
        assert db.get(Device, "ac").state["temperature"] == 24


def test_trigger_condition_logic():
    assert _conditions_pass([{"type": "time_after", "value": "19:00"}], "20:00")
    assert not _conditions_pass([{"type": "time_after", "value": "19:00"}], "18:59")


def test_policy_allows_everyday_action_and_rejects_unlock():
    assert validate_scene_permission("occupier", SceneAction(device_id="light", action="turn_on")) is None
    assert validate_scene_permission("tenant", SceneAction(device_id="lock", action="unlock")) == "That action is not allowed in an AI-created scene."


def test_api_parse_confirm_execute(monkeypatch):
    monkeypatch.setattr(AIService, "parse_scene_request", lambda *_: proposal())
    with TestClient(app) as client:
        parsed = client.post("/api/ai/scenes/parse", json={"request": "arrival comfort", "role": "tenant"})
        assert parsed.status_code == 200
        assert parsed.json()["status"] == "ready"
        confirmed = client.post("/api/scenes/confirm", json={"role": "tenant", "proposal": parsed.json()})
        assert confirmed.status_code == 200
        ran = client.post("/api/simulation/resident-arrival", json={"at_time": "20:00"})
        assert ran.status_code == 200
        assert any(item["scene_name"] == "Evening Arrival" for item in ran.json()["executions"])
