from fastapi.testclient import TestClient
from app.main import app
from app.schemas.scene import SceneAction, SceneProposal
from app.services.ai_service import AIService
from app.services import ai_service as ai_module
from app.services.automation_service import _conditions_pass
from app.services.device_service import DeviceService, execute_simulated, validate_action
from app.db.session import SessionLocal
from app.db.seed import seed_devices
from app.models.entities import ActivityEvent, Device, Scene
from app.core.permissions import validate_scene_permission
from app.simulator.device_adapter import AdapterReply, DeviceAdapter
from types import SimpleNamespace


def proposal() -> SceneProposal:
    return SceneProposal(scene_name="Evening Arrival", trigger={"type": "resident_arrives"}, conditions=[{"type": "time_after", "value": "19:00"}], actions=[{"device_id": "ac", "action": "set_temperature", "value": 24}, {"device_id": "light", "action": "turn_on"}], status="ready", explanation="Prepares the home after 7 PM.")


def test_schema_rejects_malformed_condition():
    try:
        SceneProposal(scene_name="Bad", trigger={"type": "resident_arrives"}, conditions=[{"type": "time_after", "value": "tonight"}], actions=[], status="needs_clarification", explanation="Need a time.")
        assert False, "invalid time was accepted"
    except ValueError:
        assert True


def test_pydantic_rejects_extra_output():
    raw = proposal().model_dump()
    raw["dangerous_extra"] = "execute"
    try:
        SceneProposal.model_validate(raw)
        assert False, "extra field was accepted"
    except ValueError:
        assert True


def test_provider_output_is_parsed(monkeypatch):
    class Provider:
        def parse_scene(self, **_): return proposal().model_dump_json()
    monkeypatch.setattr(ai_module, "get_settings", lambda: SimpleNamespace(ai_api_key="configured", ai_model="test-model", ai_base_url="https://provider.invalid/v1"))
    result = AIService(Provider()).parse_scene_request("a new supported request", [{"id":"ac","name":"Air Conditioner","kind":"ac","room":"Living Room","state":{}}], "owner")
    assert result.status == "ready"
    assert result.actions[0].device_id == "ac"


def test_invalid_provider_output_uses_honest_fallback(monkeypatch):
    class Provider:
        def parse_scene(self, **_): return '{"not":"a scene"}'
    monkeypatch.setattr(ai_module, "get_settings", lambda: SimpleNamespace(ai_api_key="configured", ai_model="test-model", ai_base_url="https://provider.invalid/v1"))
    result = AIService(Provider()).parse_scene_request("request", [], "owner")
    assert result.status == "service_unavailable"
    assert result.reason == "AI returned invalid structured data"


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


def test_adapter_failure_does_not_change_state():
    class FailingAdapter(DeviceAdapter):
        def send(self, action, state): return AdapterReply(False, state, "Unavailable")
    with SessionLocal() as db:
        seed_devices(db)
        before = dict(db.get(Device, "ac").state)
        result = DeviceService(FailingAdapter()).execute(db, SceneAction(device_id="ac", action="set_temperature", value=22))
        assert result.status == "failed"
        assert db.get(Device, "ac").state == before


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
        saved_id = confirmed.json()["id"]
        assert client.get("/api/scenes").json()["scenes"][0]["id"] == saved_id
        ran = client.post("/api/simulation/resident-arrival", json={"at_time": "20:00"})
        assert ran.status_code == 200
        execution = next(item for item in ran.json()["executions"] if item["scene_name"] == "Evening Arrival")
        assert execution["results"][0]["transitions"] == ["requested", "acknowledged"]
        with SessionLocal() as db:
            assert db.get(Scene, saved_id) is not None
            messages = [item.message for item in db.query(ActivityEvent).all()]
            assert any(message.startswith("DEVICE_COMMAND_ACKNOWLEDGED") for message in messages)


def test_confirmation_rejects_fabricated_frontend_proposal():
    with TestClient(app) as client:
        response = client.post("/api/scenes/confirm", json={"role":"owner", "proposal": proposal().model_dump()})
        assert response.status_code == 422
