"""MQTT simulator — publishes fake device telemetry to the in-process bus.

Run as a background task from the FastAPI lifespan (started in main.py),
OR standalone:  python -m app.simulator.mqtt_simulator

The in-process bus replaces the Mosquitto broker — identical topic/payload
API, no network port required. A production deployment would swap this for
a real aiomqtt publisher pointed at an actual broker.
"""
import asyncio
import logging
import random
from datetime import datetime, timezone

logger = logging.getLogger("livlink.simulator")

DEVICES = {
    "ac":       "building/towerB/unit1204/ac",
    "bac":      "building/towerB/unit1204/bac",
    "light":    "building/towerB/unit1204/light",
    "blight":   "building/towerB/unit1204/blight",
    "klight":   "building/towerB/unit1204/klight",
    "curtain":  "building/towerB/unit1204/curtain",
    "bcurtain": "building/towerB/unit1204/bcurtain",
    "tv":       "building/towerB/unit1204/tv",
    "lock":     "building/towerB/unit1204/lock",
}
EVENTS_TOPIC = "building/towerB/unit1204/events"


def _normal_ac() -> dict:
    return {"power": round(random.uniform(2.2, 2.8), 2), "temperature": random.choice([24, 25]), "status": "ON"}

def _spike_ac() -> dict:
    return {"power": round(random.uniform(4.0, 5.2), 2), "temperature": random.choice([22, 23, 24]), "status": "ON"}

def _normal_light() -> dict:
    return {"power": round(random.uniform(0.25, 0.35), 2), "level": random.choice([60, 70, 80]), "status": "ON"}

def _lock_healthy() -> dict:
    return {"battery": random.randint(60, 90), "status": "LOCKED", "connection_failures": 0}

def _lock_degraded() -> dict:
    # Deterministic critical demo telemetry: this crosses the 10% maintenance threshold.
    return {"battery": 10, "status": "LOCKED", "connection_failures": random.randint(3, 6)}

def _heartbeat() -> dict:
    return {"status": "alive", "timestamp": datetime.now(timezone.utc).isoformat()}

def _resident_arrival() -> dict:
    return {"event": "resident_arrived", "time": datetime.now(timezone.utc).strftime("%H:%M")}


async def run_simulator() -> None:
    """Publish MQTT events to the in-process bus in a loop."""
    from app.mqtt.bus import get_bus
    bus = get_bus()

    cycle = 0
    logger.info("MQTT simulator started (in-process bus)")

    while True:
        cycle += 1

        # Energy: normal most cycles, spike every 10th
        ac_payload = _spike_ac() if cycle % 10 == 0 else _normal_ac()
        await bus.publish(DEVICES["ac"], ac_payload)
        await bus.publish(DEVICES["bac"], _normal_ac())
        await bus.publish(DEVICES["light"], _normal_light())

        # Lock: degraded every 5th cycle
        lock_payload = _lock_degraded() if cycle % 5 == 0 else _lock_healthy()
        await bus.publish(DEVICES["lock"], lock_payload)

        # Heartbeats every 3rd cycle (skip lock every 6th to simulate missing)
        if cycle % 3 == 0:
            for device_id, topic in DEVICES.items():
                if device_id == "lock" and cycle % 6 == 0:
                    continue
                await bus.publish(topic + "/heartbeat", _heartbeat())

        # Resident arrival every 20th cycle
        if cycle % 20 == 0:
            await bus.publish(EVENTS_TOPIC, _resident_arrival())
            logger.info("Simulator: resident_arrived published")

        logger.debug("Simulator cycle %d complete", cycle)
        await asyncio.sleep(random.uniform(3.0, 5.0))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    print("Note: Run via uvicorn (main.py starts the simulator automatically).")
    print("Standalone mode uses an isolated bus — messages won't reach the backend subscriber.")
    asyncio.run(run_simulator())
