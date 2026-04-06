from typing import Optional
from datetime import datetime, UTC
from sqlmodel import SQLModel, Field


class SystemSettingsBase(SQLModel):
    notifications_enabled: bool = Field(default=True)
    critical_only: bool = Field(default=True)
    monitored_keywords: Optional[str] = Field(default=None)
    critical_locations: Optional[str] = Field(default=None)


class SystemSettings(SystemSettingsBase, table=True):
    id: Optional[int] = Field(default=1, primary_key=True)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class SystemSettingsRead(SystemSettingsBase):
    id: int
    updated_at: datetime


# Todo opcional para que React pueda hacer PATCH de un solo switch a la vez
class SystemSettingsUpdate(SQLModel):
    notifications_enabled: Optional[bool] = None
    critical_only: Optional[bool] = None
    monitored_keywords: Optional[str] = None
    critical_locations: Optional[str] = None
