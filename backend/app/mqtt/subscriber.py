"""MQTT subscriber — ingests device telemetry and triggers AI analysis.

Uses the in-process bus (app.mqtt.bus) so no external broker is needed.
The production path (real Mosquitto via aiomqtt) is a single config swap.
"""
import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger("livlink.mqtt")

_mqtt_connected = False
_mqtt_event_count = 0


def mqtt_status() -> dict:
    return {
        "connected": _mqtt_connected,
        "events_received": _mqtt_event_count,
        "transport": "in_process_simulation",
    }


async def start_subscriber(broker_host: str, broker_port: int, db_factory) -> None:
    """Subscribe to the in-process bus and ingest events into the database."""
    global _mqtt_connected, _mqtt_event_count

    from app.mqtt.bus import get_bus
    bus = get_bus()
    _mqtt_event_count = 0
    _mqtt_connected = True
    logger.info("MQTT subscriber ready (in-process bus, no broker required)")

    try:
        async for message in bus.messages():
            _mqtt_event_count += 1
            try:
                await _handle_message(message.topic, message.payload, db_factory)
            except Exception:
                logger.exception("Error handling MQTT message on topic %s", message.topic)
    except asyncio.CancelledError:
        _mqtt_connected = False
        logger.info("MQTT subscriber stopped")
        raise


async def _handle_message(topic: str, payload: dict, db_factory) -> None:
    """Route an incoming message to the appropriate analysis pipeline."""
    from app.models.entities import DeviceTelemetry, ResidentEvent
    from app.services.energy_service import check_energy_anomaly
    from app.services.maintenance_service import check_device_health
    from app.services.learned_automation_service import check_arrival_patterns

    parts = topic.split("/")
    # Expected: building/towerB/unit1204/device_id[/heartbeat]
    if len(parts) < 4:
        return

    device_id = parts[3]
    is_heartbeat = len(parts) >= 5 and parts[4] == "heartbeat"

    with db_factory() as db:
        if is_heartbeat:
            event_type = "heartbeat"
        elif "battery" in payload:
            event_type = "battery"
        elif "power" in payload:
            event_type = "energy"
        elif "event" in payload:
            event_type = "event"
        else:
            event_type = "status"

        db.add(DeviceTelemetry(
            device_id=device_id,
            event_type=event_type,
            payload=payload,
            timestamp=datetime.now(timezone.utc),
        ))
        db.commit()

        if event_type == "energy":
            check_energy_anomaly(db, device_id)
        elif event_type == "battery":
            check_device_health(db, device_id)
        elif event_type == "event" and payload.get("event") == "resident_arrived":
            db.add(ResidentEvent(event_type="arrival", timestamp=datetime.now(timezone.utc)))
            db.commit()
            check_arrival_patterns(db)

        logger.debug("Stored %s event for %s", event_type, device_id)
