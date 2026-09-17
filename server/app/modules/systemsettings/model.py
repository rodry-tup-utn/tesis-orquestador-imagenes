from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field


class SystemSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    notifications_enabled: bool = Field(default=True)
    notify_priority: bool = Field(default=False)
    triage_critical_threshold: int = Field(default=25)
    triage_urgent_threshold: int = Field(default=15)
    triage_priority_threshold: int = Field(default=10)
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
