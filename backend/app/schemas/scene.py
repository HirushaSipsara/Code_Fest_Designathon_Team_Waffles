from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Trigger(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["resident_arrives"]


class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal["time_after"]
    value: str

    @field_validator("value")
    @classmethod
    def validate_time(cls, value: str) -> str:
        try:
            datetime.strptime(value, "%H:%M")
        except ValueError as exc:
            raise ValueError("time_after must use 24-hour HH:MM") from exc
        return value


class SceneAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    device_id: str
    action: Literal["set_temperature", "set_level", "turn_on", "turn_off", "lock", "unlock"]
    value: int | None = None


class SceneProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scene_name: str = Field(min_length=1, max_length=80)
    trigger: Trigger
    conditions: list[Condition] = Field(default_factory=list, max_length=3)
    actions: list[SceneAction] = Field(default_factory=list, max_length=8)
    status: Literal["ready", "needs_clarification", "unsupported", "service_unavailable", "rejected"]
    explanation: str = Field(min_length=1, max_length=280)


class ParseRequest(BaseModel):
    request: str = Field(min_length=3, max_length=500)
    role: Literal["owner", "occupier", "tenant"]


class ProposalResponse(SceneProposal):
    proposal_id: str | None = None
    reason: str | None = None


class ConfirmRequest(BaseModel):
    role: Literal["owner", "occupier", "tenant"]
    proposal: ProposalResponse


class ArrivalRequest(BaseModel):
    at_time: str | None = None


class CommandResult(BaseModel):
    device_id: str
    action: str
    status: Literal["acknowledged", "failed"]
    detail: str
