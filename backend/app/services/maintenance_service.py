"""Predictive Maintenance — weighted risk scoring.

Analyses battery trends, connection failures, error frequency, and
heartbeat gaps to produce a risk score for each device.
No ML model — honest deterministic scoring for the prototype.
"""
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.entities import AIInsight, DeviceTelemetry

logger = logging.getLogger("livlink.maintenance")

DEVICE_NAMES = {
    "ac": "Living Room Air Conditioner",
    "bac": "Bedroom Air Conditioner",
    "light": "Living Room Ceiling Light",
    "lock": "Front Door Lock",
    "tv": "Television",
    "curtain": "Living Room Curtains",
}


def check_device_health(db: Session, device_id: str) -> AIInsight | None:
    """Calculate a risk score for the given device."""

    # Get the latest battery reading
    latest_battery = (
        db.query(DeviceTelemetry)
        .filter(DeviceTelemetry.device_id == device_id, DeviceTelemetry.event_type == "battery")
        .order_by(DeviceTelemetry.timestamp.desc())
        .first()
    )
    if not latest_battery:
        return None

    payload = latest_battery.payload
    battery_pct = payload.get("battery", 100)
    connection_failures = payload.get("connection_failures", 0)

    # Check battery trend (last 5 readings)
    battery_readings = (
        db.query(DeviceTelemetry)
        .filter(DeviceTelemetry.device_id == device_id, DeviceTelemetry.event_type == "battery")
        .order_by(DeviceTelemetry.timestamp.desc())
        .limit(5)
        .all()
    )
    battery_values = [r.payload.get("battery", 100) for r in battery_readings]

    # Check heartbeat gaps
    cutoff = datetime.now(timezone.utc) - timedelta(hours=8)
    recent_heartbeats = (
        db.query(DeviceTelemetry)
        .filter(DeviceTelemetry.device_id == device_id, DeviceTelemetry.event_type == "heartbeat", DeviceTelemetry.timestamp >= cutoff)
        .count()
    )
    # Expect at least 2 heartbeats in 8 hours
    missing_heartbeat = recent_heartbeats < 2

    # --- Risk scoring ---
    score = 0
    factors = []

    # Battery declining rapidly (difference between oldest and newest > 20 in 5 readings)
    if len(battery_values) >= 3:
        decline = battery_values[-1] - battery_values[0]  # oldest - newest (readings are desc order, so [0]=newest)
        # Actually [0] is newest, [-1] is oldest; decline = oldest - newest
        actual_decline = battery_values[-1] - battery_values[0]
        # If oldest is higher than newest, battery is declining
        if actual_decline > 15:
            score += 30
            factors.append("Battery declining rapidly (+30)")

    # Low battery
    if battery_pct < 20:
        score += 10
        factors.append(f"Battery critically low at {battery_pct}% (+10)")

    # Connection failures
    if connection_failures > 2:
        score += 25
        factors.append(f"Connection failures: {connection_failures} (+25)")

    # Missing heartbeat
    if missing_heartbeat:
        score += 25
        factors.append("Missing heartbeat in last 8 hours (+25)")

    # Repeated errors (connection_failures as proxy)
    if connection_failures > 0:
        error_score = min(connection_failures * 5, 20)
        score += error_score
        factors.append(f"Repeated errors (+{error_score})")

    # Determine risk level
    if score >= 70:
        risk_level = "high"
        severity = "critical"
    elif score >= 40:
        risk_level = "medium"
        severity = "warning"
    else:
        return None  # Low risk — don't create an insight

    # Check for existing active insight
    existing = (
        db.query(AIInsight)
        .filter(AIInsight.device_id == device_id, AIInsight.category == "maintenance", AIInsight.status == "active")
        .first()
    )

    body = {
        "device_name": DEVICE_NAMES.get(device_id, device_id),
        "device_id": device_id,
        "battery_pct": battery_pct,
        "connection_failures": connection_failures,
        "risk_score": score,
        "risk_level": risk_level,
        "factors": factors,
        "recommendation": "Schedule a technician to inspect or replace the device battery." if battery_pct < 25 else "Monitor the device closely and check wiring.",
    }

    if existing:
        existing.body = body
        existing.severity = severity
        db.commit()
        return existing

    insight = AIInsight(
        category="maintenance",
        severity=severity,
        title="Possible device failure",
        body=body,
        device_id=device_id,
        status="active",
    )
    db.add(insight)
    db.commit()
    logger.info("Maintenance risk for %s: score=%d (%s)", device_id, score, risk_level)
    return insight
