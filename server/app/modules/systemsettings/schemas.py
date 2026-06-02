from datetime import datetime
from sqlmodel import SQLModel


class SystemSettingsRead(SQLModel):
    notifications_enabled: bool
    notify_priority: bool
    triage_critical_threshold: int
    triage_priority_threshold: int
    id: int
    updated_at: datetime


class SystemSettingsUpdate(SQLModel):
    notifications_enabled: bool | None = None
    notify_priority: bool | None = None
    triage_critical_threshold: int | None = None
    triage_priority_threshold: int | None = None
