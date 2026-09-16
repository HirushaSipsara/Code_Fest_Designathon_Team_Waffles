"""In-process MQTT bus — replaces the Mosquitto broker for the prototype.

Uses asyncio.Queue so the simulator and subscriber communicate without
any network broker. The topic/payload API is identical to aiomqtt, making
the "production path" (real Mosquitto) a simple config swap.

Usage
-----
The backend imports get_bus() once; the simulator puts() messages;
the subscriber gets() and processes them.
"""
import asyncio
from dataclasses import dataclass

@dataclass
class Message:
    topic: str
    payload: dict


class InProcessBus:
    """Single shared asyncio.Queue acting as a zero-broker MQTT bus."""

    def __init__(self):
        self._queue: asyncio.Queue[Message] = asyncio.Queue()

    async def publish(self, topic: str, payload: dict) -> None:
        await self._queue.put(Message(topic=topic, payload=payload))

    async def messages(self):
        """Async generator — yields messages as they arrive."""
        while True:
            yield await self._queue.get()


# Module-level singleton — created once per process
_bus: InProcessBus | None = None


def get_bus() -> InProcessBus:
    global _bus
    if _bus is None:
        _bus = InProcessBus()
    return _bus


def reset_bus() -> InProcessBus:
    """Create a queue for this application lifespan's event loop."""
    global _bus
    _bus = InProcessBus()
    return _bus
