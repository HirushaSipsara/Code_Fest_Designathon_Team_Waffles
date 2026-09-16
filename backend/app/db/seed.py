from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models.entities import AIInsight, Device, DeviceTelemetry, ResidentEvent
from app.db.session import SessionLocal

DEVICES = [
    ("ac", "Air Conditioner", "ac", "Living Room", {"on": True, "temperature": 25}),
    ("light", "Ceiling Light", "light", "Living Room", {"on": True, "level": 70}),
    ("tv", "Television", "tv", "Living Room", {"on": False}),
    ("curtain", "Curtains", "curtain", "Living Room", {"on": True, "level": 40}),
    ("lock", "Front Door Lock", "lock", "Living Room", {"locked": True}),
    ("bac", "Air Conditioner", "ac", "Bedroom", {"on": False, "temperature": 24}),
    ("blight", "Bedside Lamp", "light", "Bedroom", {"on": False, "level": 20}),
    ("bcurtain", "Curtains", "curtain", "Bedroom", {"on": True, "level": 0}),
    ("klight", "Counter Light", "light", "Kitchen", {"on": True, "level": 60}),
]


def seed_devices(db: Session) -> None:
    if db.query(Device).count():
        return
    db.add_all(Device(id=id, name=name, kind=kind, room=room, state=state) for id, name, kind, room, state in DEVICES)
    db.commit()


def seed_telemetry(db: Session) -> None:
    """Seed 7 days of historical telemetry so analytics work on first load."""
    if db.query(DeviceTelemetry).count():
        return

    now = datetime.now(timezone.utc)

    # --- Energy readings (kWh per period) for ACs ---
    ac_normal = [2.4, 2.6, 2.5, 2.7, 2.5, 2.6, 2.4]
    bac_normal = [1.8, 1.9, 1.7, 1.8, 2.0, 1.9, 1.8]
    light_normal = [0.3, 0.28, 0.32, 0.3, 0.29, 0.31, 0.3]

    for day_offset, kwh in enumerate(ac_normal):
        ts = now - timedelta(days=7 - day_offset)
        db.add(DeviceTelemetry(device_id="ac", event_type="energy", payload={"power": kwh, "temperature": 25, "status": "ON"}, timestamp=ts))

    for day_offset, kwh in enumerate(bac_normal):
        ts = now - timedelta(days=7 - day_offset)
        db.add(DeviceTelemetry(device_id="bac", event_type="energy", payload={"power": kwh, "temperature": 24, "status": "ON"}, timestamp=ts))

    for day_offset, kwh in enumerate(light_normal):
        ts = now - timedelta(days=7 - day_offset)
        db.add(DeviceTelemetry(device_id="light", event_type="energy", payload={"power": kwh, "level": 70, "status": "ON"}, timestamp=ts))

    # Inject today's anomaly — AC spike
    db.add(DeviceTelemetry(device_id="ac", event_type="energy", payload={"power": 4.5, "temperature": 24, "status": "ON"}, timestamp=now))

    # --- Battery readings for the lock (declining) ---
    lock_battery = [48, 41, 33, 24, 10]
    lock_failures = [0, 0, 1, 2, 4]
    for day_offset, (batt, fails) in enumerate(zip(lock_battery, lock_failures)):
        ts = now - timedelta(days=5 - day_offset)
        db.add(DeviceTelemetry(device_id="lock", event_type="battery", payload={"battery": batt, "status": "LOCKED", "connection_failures": fails}, timestamp=ts))

    # --- Heartbeats for all devices (last 24h, every 4 hours) ---
    for device_id in ["ac", "light", "tv", "curtain", "bac", "blight", "bcurtain", "klight"]:
        for hour_offset in range(0, 24, 4):
            ts = now - timedelta(hours=24 - hour_offset)
            db.add(DeviceTelemetry(device_id=device_id, event_type="heartbeat", payload={"status": "alive"}, timestamp=ts))

    # Skip lock heartbeats for the last 2 to simulate missing heartbeat
    for hour_offset in range(0, 20, 4):
        ts = now - timedelta(hours=24 - hour_offset)
        db.add(DeviceTelemetry(device_id="lock", event_type="heartbeat", payload={"status": "alive"}, timestamp=ts))

    db.commit()


def seed_resident_events(db: Session) -> None:
    """Seed 5 days of resident arrival → action patterns."""
    if db.query(ResidentEvent).count():
        return

    now = datetime.now(timezone.utc)

    # Pattern: arrival → lights ON + AC ON (happens 5/5 days)
    # curtains CLOSE happens 3/5 days
    patterns = [
        # Day 1: arrival → light ON, AC ON
        [("arrival", None, None), ("device_action", "light", "turn_on"), ("device_action", "ac", "set_temperature")],
        # Day 2: arrival → light ON, AC ON, curtain CLOSE
        [("arrival", None, None), ("device_action", "light", "turn_on"), ("device_action", "ac", "set_temperature"), ("device_action", "curtain", "set_level")],
        # Day 3: arrival → light ON, AC ON
        [("arrival", None, None), ("device_action", "light", "turn_on"), ("device_action", "ac", "set_temperature")],
        # Day 4: arrival → light ON, AC ON, curtain CLOSE
        [("arrival", None, None), ("device_action", "light", "turn_on"), ("device_action", "ac", "set_temperature"), ("device_action", "curtain", "set_level")],
        # Day 5: arrival → light ON, AC ON, curtain CLOSE
        [("arrival", None, None), ("device_action", "light", "turn_on"), ("device_action", "ac", "set_temperature"), ("device_action", "curtain", "set_level")],
    ]

    for day_offset, day_events in enumerate(patterns):
        base_ts = now - timedelta(days=5 - day_offset, hours=-18, minutes=-2)  # ~18:02
        for minute_offset, (etype, dev_id, action) in enumerate(day_events):
            ts = base_ts + timedelta(minutes=minute_offset)
            value = "24" if action == "set_temperature" else "0" if action == "set_level" else None
            db.add(ResidentEvent(event_type=etype, device_id=dev_id, action=action, value=value, timestamp=ts))

    db.commit()


def seed_insights(db: Session) -> None:
    """Pre-generate AI insight cards so the UI has content on first load."""
    if db.query(AIInsight).count():
        return

    # Energy anomaly
    db.add(AIInsight(
        category="energy", severity="warning",
        title="Unusual energy usage",
        body={
            "device_name": "Living Room Air Conditioner",
            "device_id": "ac",
            "current_kwh": 4.5,
            "typical_kwh": 2.54,
            "deviation_pct": 77,
            "recommendation": "Set AC to 25°C during low-occupancy periods to reduce consumption.",
        },
        device_id="ac", status="active",
    ))

    # Predictive maintenance
    db.add(AIInsight(
        category="maintenance", severity="critical",
        title="Possible device failure",
        body={
            "device_name": "Front Door Lock",
            "device_id": "lock",
            "battery_pct": 10,
            "connection_failures": 4,
            "risk_score": 100,
            "risk_level": "high",
            "factors": ["Battery declining rapidly (+30)", "Connection failures > 2 (+25)", "Repeated errors (+20)", "Missing heartbeat (+25)"],
            "recommendation": "Schedule a technician to inspect or replace the lock battery.",
        },
        device_id="lock", status="active",
    ))

    # Learned automation suggestion
    db.add(AIInsight(
        category="automation", severity="info",
        title="Smart suggestion",
        body={
            "description": "You usually turn on the living-room lights and AC shortly after arriving home.",
            "pattern_days": 5,
            "pattern_matches": 5,
            "suggested_scene": {
                "scene_name": "Welcome Home",
                "trigger": {"type": "resident_arrives"},
                "conditions": [{"type": "time_after", "value": "18:00"}],
                "actions": [
                    {"device_id": "light", "action": "turn_on", "value": None},
                    {"device_id": "ac", "action": "set_temperature", "value": 24},
                ],
            },
        },
        device_id=None, status="active",
    ))

    db.commit()


if __name__ == "__main__":
    with SessionLocal() as session:
        seed_devices(session)
        seed_telemetry(session)
        seed_resident_events(session)
        seed_insights(session)
    print("LIVLINK prototype device catalogue and telemetry seeded.")
