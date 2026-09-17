from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum
from sqlalchemy import Column, DateTime


class TriageField(str, Enum):
    MODALITY = "modality"
    DIAGNOSIS = "diagnosis"
    ORIGIN_SERVICE = "origin_service"
    PATIENT_LOCATION = "patient_location"
    IS_URGENT = "is_urgent"


class TriageOperator(str, Enum):
    EQUALS = "equals"
    CONTAINS = "contains"
    STARTSWITH = "startswith"


class TriageRule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    field: TriageField
    operator: TriageOperator
    value: str = Field(max_length=255)
    weight: int = Field(default=0)
    enabled: bool = Field(default=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )
