from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, JSON, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass


class Device(Base):
    __tablename__ = "devices"
    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    kind: Mapped[str] = mapped_column(String(30))
    room: Mapped[str] = mapped_column(String(50))
    state: Mapped[dict] = mapped_column(JSON)


class Scene(Base):
    __tablename__ = "scenes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(20))
    trigger: Mapped[dict] = mapped_column(JSON)
    conditions: Mapped[list] = mapped_column(JSON)
    actions: Mapped[list] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SceneDraft(Base):
    __tablename__ = "scene_drafts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    role: Mapped[str] = mapped_column(String(20))
    proposal: Mapped[dict] = mapped_column(JSON)
    consumed: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ActivityEvent(Base):
    __tablename__ = "activity_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(20), default="ok")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DeviceTelemetry(Base):
    """Every MQTT reading stored for analytics."""
    __tablename__ = "device_telemetry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    device_id: Mapped[str] = mapped_column(String(50), index=True)
    event_type: Mapped[str] = mapped_column(String(30))  # energy, heartbeat, battery, status
    payload: Mapped[dict] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIInsight(Base):
    """Generated intelligence cards shown in the UI."""
    __tablename__ = "ai_insights"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String(20))  # energy, maintenance, automation
    severity: Mapped[str] = mapped_column(String(10))  # info, warning, critical
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[dict] = mapped_column(JSON)
    device_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, dismissed, applied
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MaintenanceRequest(Base):
    """Operator work item created from a critical device-health decision."""
    __tablename__ = "maintenance_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    unit: Mapped[str] = mapped_column(String(20), default="1204")
    device_id: Mapped[str] = mapped_column(String(50), index=True)
    device_name: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(200))
    decision: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, assigned, resolved
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ResidentEvent(Base):
    """Resident arrival + action patterns for learned automation."""
    __tablename__ = "resident_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    event_type: Mapped[str] = mapped_column(String(30))  # arrival, device_action
    device_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    action: Mapped[str | None] = mapped_column(String(30), nullable=True)
    value: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
