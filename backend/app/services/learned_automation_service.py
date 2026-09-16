"""Learned Automation — pattern frequency counting.

Looks at ResidentEvent history to find device actions that consistently
follow a resident arrival (≥ 3 out of the last 5 arrival episodes).
If a pattern is found and no automation already exists, creates an
AIInsight suggesting the automation.  No ML — deterministic counting.
"""
import logging
from collections import Counter
from datetime import timedelta
from sqlalchemy.orm import Session
from app.models.entities import AIInsight, ResidentEvent, Scene

logger = logging.getLogger("livlink.automation")

DEVICE_NAMES = {
    "ac": "Living Room Air Conditioner",
    "bac": "Bedroom Air Conditioner",
    "light": "Living Room Ceiling Light",
    "blight": "Bedroom Bedside Lamp",
    "klight": "Kitchen Counter Light",
    "curtain": "Living Room Curtains",
    "bcurtain": "Bedroom Curtains",
    "tv": "Television",
    "lock": "Front Door Lock",
}

PATTERN_THRESHOLD = 3  # minimum matches out of last 5 arrival episodes
WINDOW_MINUTES = 10    # actions within this window after arrival count as correlated


def check_arrival_patterns(db: Session) -> AIInsight | None:
    """Analyse recent arrivals and find repeated post-arrival actions."""

    # Get the last 5 arrival events
    arrivals = (
        db.query(ResidentEvent)
        .filter(ResidentEvent.event_type == "arrival")
        .order_by(ResidentEvent.timestamp.desc())
        .limit(5)
        .all()
    )

    if len(arrivals) < 3:
        return None

    # For each arrival, find the actions that followed within WINDOW_MINUTES
    episodes: list[set[tuple[str, str]]] = []
    for arrival in arrivals:
        window_end = arrival.timestamp + timedelta(minutes=WINDOW_MINUTES)
        actions = (
            db.query(ResidentEvent)
            .filter(
                ResidentEvent.event_type == "device_action",
                ResidentEvent.timestamp >= arrival.timestamp,
                ResidentEvent.timestamp <= window_end,
            )
            .all()
        )
        episode_actions = {(a.device_id, a.action) for a in actions if a.device_id and a.action}
        episodes.append(episode_actions)

    # Count how many episodes each (device, action) pair appears in
    action_counter: Counter[tuple[str, str]] = Counter()
    for episode in episodes:
        for action_pair in episode:
            action_counter[action_pair] += 1

    # Find actions that meet the threshold
    frequent_actions = [(dev, act, count) for (dev, act), count in action_counter.items() if count >= PATTERN_THRESHOLD]

    if not frequent_actions:
        return None

    # Check if there's already an active automation insight
    existing = (
        db.query(AIInsight)
        .filter(AIInsight.category == "automation", AIInsight.status == "active")
        .first()
    )
    if existing:
        return existing  # Don't duplicate

    # Check if there's already a saved scene that covers these actions
    for scene in db.query(Scene).all():
        scene_actions = {(a.get("device_id"), a.get("action")) for a in (scene.actions or [])}
        pattern_actions = {(dev, act) for dev, act, _ in frequent_actions}
        if pattern_actions.issubset(scene_actions):
            return None  # A scene already covers this pattern

    # Build the suggested scene
    suggested_actions = []
    for dev, act, count in frequent_actions:
        action_entry = {"device_id": dev, "action": act, "value": None}
        if act == "set_temperature":
            action_entry["value"] = 24
        elif act == "set_level":
            action_entry["value"] = 0
        suggested_actions.append(action_entry)

    description_parts = []
    for dev, act, count in frequent_actions:
        name = DEVICE_NAMES.get(dev, dev)
        action_text = act.replace("_", " ")
        description_parts.append(f"{name} ({action_text})")

    description = f"You usually {' and '.join(description_parts)} shortly after arriving home."

    insight = AIInsight(
        category="automation",
        severity="info",
        title="Smart suggestion",
        body={
            "description": description,
            "pattern_days": len(arrivals),
            "pattern_matches": max(count for _, _, count in frequent_actions),
            "suggested_scene": {
                "scene_name": "Welcome Home",
                "trigger": {"type": "resident_arrives"},
                "conditions": [{"type": "time_after", "value": "18:00"}],
                "actions": suggested_actions,
            },
        },
        device_id=None,
        status="active",
    )
    db.add(insight)
    db.commit()
    logger.info("Learned automation suggested: %d frequent actions", len(frequent_actions))
    return insight
