"""Replaceable device transport boundary. No physical hardware is connected."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time
from app.schemas.scene import SceneAction

@dataclass(frozen=True)
class AdapterReply:
    acknowledged: bool
    state: dict
    detail: str

class DeviceAdapter(ABC):
    @abstractmethod
    def send(self, action: SceneAction, state: dict) -> AdapterReply:
        """Return the simulated or real gateway acknowledgement and resulting state."""

class MockDeviceAdapter(DeviceAdapter):
    def send(self, action: SceneAction, state: dict) -> AdapterReply:
        time.sleep(0.12)
        changed = dict(state)
        if action.action == "set_temperature": changed.update(on=True, temperature=action.value)
        elif action.action == "set_level": changed.update(on=bool(action.value), level=action.value)
        elif action.action == "turn_on": changed["on"] = True
        elif action.action == "turn_off": changed["on"] = False
        elif action.action == "lock": changed["locked"] = True
        elif action.action == "unlock": changed["locked"] = False
        else: return AdapterReply(False, state, "Unsupported simulated command")
        return AdapterReply(True, changed, "Simulated device acknowledged command")
