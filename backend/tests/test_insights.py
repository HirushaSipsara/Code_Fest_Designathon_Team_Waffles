from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models.entities import AIInsight, DeviceTelemetry, MaintenanceRequest, Scene
from app.services.maintenance_service import check_device_health


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


def test_critical_battery_creates_and_updates_operator_request():
    with SessionLocal() as db:
        base_time = datetime.now(timezone.utc) - timedelta(minutes=5)
        for index, battery in enumerate([48, 41, 33, 24, 10]):
            db.add(DeviceTelemetry(
                device_id="lock",
                event_type="battery",
                payload={"battery": battery, "connection_failures": 4, "status": "LOCKED"},
                timestamp=base_time + timedelta(minutes=index),
            ))
        db.commit()
        insight = check_device_health(db, "lock")
        request = db.query(MaintenanceRequest).one()
        assert request.status == "open"
        assert request.decision["battery_pct"] == 10
        assert request.decision["reading_count"] == 5
        assert insight.body["maintenance_request"]["id"] == request.id

    with TestClient(app) as client:
        listed = client.get("/api/maintenance-requests")
        assert listed.status_code == 200
        request_id = listed.json()["requests"][0]["id"]
        assigned = client.post(f"/api/maintenance-requests/{request_id}/assign")
        assert assigned.json()["status"] == "assigned"
        resolved = client.post(f"/api/maintenance-requests/{request_id}/resolve")
        assert resolved.json()["status"] == "resolved"
        maintenance = next(item for item in client.get("/api/insights").json()["insights"] if item["category"] == "maintenance")
        assert maintenance["body"]["maintenance_request"]["status"] == "resolved"
