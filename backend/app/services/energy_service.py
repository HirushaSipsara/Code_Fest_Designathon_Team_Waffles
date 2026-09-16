"""Energy Intelligence — baseline + anomaly detection.

Compares the latest energy reading for a device against its 7-day average.
If deviation exceeds 50%, creates an AIInsight card.  No neural network —
honest anomaly scoring for the prototype.
"""
import logging
from sqlalchemy.orm import Session
from app.models.entities import AIInsight, DeviceTelemetry

logger = logging.getLogger("livlink.energy")

DEVICE_NAMES = {
    "ac": "Living Room Air Conditioner",
    "bac": "Bedroom Air Conditioner",
    "light": "Living Room Ceiling Light",
    "blight": "Bedroom Bedside Lamp",
    "klight": "Kitchen Counter Light",
}

RECOMMENDATIONS = {
    "ac": "Set AC to 25°C during low-occupancy periods to reduce consumption.",
    "bac": "Set bedroom AC to 25°C or use a timer to turn off when unoccupied.",
    "light": "Dim lights to 50% when full brightness isn't needed.",
    "blight": "Use scheduled auto-off for the bedside lamp.",
    "klight": "Switch to motion-activated lighting in the kitchen.",
}

ANOMALY_THRESHOLD_PCT = 50  # deviation % to trigger an alert


def check_energy_anomaly(db: Session, device_id: str) -> AIInsight | None:
    """Compare latest energy reading to the historical baseline."""
    readings = (
        db.query(DeviceTelemetry)
        .filter(DeviceTelemetry.device_id == device_id, DeviceTelemetry.event_type == "energy")
        .order_by(DeviceTelemetry.timestamp.desc())
        .limit(8)
        .all()
    )

    if len(readings) < 2:
        return None

    current = readings[0].payload.get("power", 0)
    historical = [r.payload.get("power", 0) for r in readings[1:]]
    avg = sum(historical) / len(historical) if historical else 0

    if avg == 0:
        return None

    deviation_pct = round(((current - avg) / avg) * 100)

    if deviation_pct < ANOMALY_THRESHOLD_PCT:
        return None

    # Check if there's already an active energy insight for this device
    existing = (
        db.query(AIInsight)
        .filter(AIInsight.device_id == device_id, AIInsight.category == "energy", AIInsight.status == "active")
        .first()
    )
    if existing:
        # Update the existing insight with latest numbers
        existing.body = {
            "device_name": DEVICE_NAMES.get(device_id, device_id),
            "device_id": device_id,
            "current_kwh": current,
            "typical_kwh": round(avg, 2),
            "deviation_pct": deviation_pct,
            "recommendation": RECOMMENDATIONS.get(device_id, "Review device usage patterns."),
        }
        db.commit()
        return existing

    insight = AIInsight(
        category="energy",
        severity="warning" if deviation_pct < 100 else "critical",
        title="Unusual energy usage",
        body={
            "device_name": DEVICE_NAMES.get(device_id, device_id),
            "device_id": device_id,
            "current_kwh": current,
            "typical_kwh": round(avg, 2),
            "deviation_pct": deviation_pct,
            "recommendation": RECOMMENDATIONS.get(device_id, "Review device usage patterns."),
        },
        device_id=device_id,
        status="active",
    )
    db.add(insight)
    db.commit()
    logger.info("Energy anomaly detected for %s: +%d%% deviation", device_id, deviation_pct)
    return insight
