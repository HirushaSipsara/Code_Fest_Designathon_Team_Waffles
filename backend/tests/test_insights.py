from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.entities import AIInsight, Scene


def test_insight_routes_are_registered():
    paths = app.openapi()["paths"]
    assert "/api/insights" in paths
    assert "/api/mqtt/status" in paths
    assert "/api/telemetry/{device_id}" in paths


def test_seeded_insights_and_in_process_bus_are_available():
    with TestClient(app) as client:
        response = client.get("/api/insights")
        assert response.status_code == 200
        insights = response.json()["insights"]
        assert {item["category"] for item in insights} == {"energy", "maintenance", "automation"}

        status = client.get("/api/mqtt/status")
        assert status.status_code == 200
        assert status.json()["connected"] is True


def test_dismiss_insight_is_persisted():
    with TestClient(app) as client:
        insight_id = client.get("/api/insights").json()["insights"][0]["id"]
        response = client.post(f"/api/insights/{insight_id}/dismiss")
        assert response.status_code == 200
        assert all(item["id"] != insight_id for item in client.get("/api/insights").json()["insights"])


def test_apply_automation_creates_valid_scene_once():
    with TestClient(app) as client:
        insight = next(item for item in client.get("/api/insights").json()["insights"] if item["category"] == "automation")
        response = client.post(f"/api/insights/{insight['id']}/apply")
        assert response.status_code == 200
        scene_id = response.json()["id"]
        with SessionLocal() as db:
            assert db.get(Scene, scene_id).name == "Welcome Home"
            assert db.get(AIInsight, insight["id"]).status == "applied"
        assert client.post(f"/api/insights/{insight['id']}/apply").status_code == 409


def test_apply_rejects_unsafe_seeded_action():
    with SessionLocal() as db:
        unsafe = AIInsight(
            category="automation",
            severity="info",
            title="Unsafe suggestion",
            body={
                "suggested_scene": {
                    "scene_name": "Unsafe",
                    "trigger": {"type": "resident_arrives"},
                    "conditions": [{"type": "time_after", "value": "18:00"}],
                    "actions": [{"device_id": "lock", "action": "unlock", "value": None}],
                }
            },
            status="active",
        )
        db.add(unsafe)
        db.commit()
        insight_id = unsafe.id

    with TestClient(app) as client:
        response = client.post(f"/api/insights/{insight_id}/apply")
        assert response.status_code == 422
        assert "not allowed" in response.json()["detail"]
