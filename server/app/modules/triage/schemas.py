from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field
from app.modules.triage.model import TriageField, TriageOperator


class TriageRuleCreate(SQLModel):
    name: str = Field(max_length=100)
    field: TriageField
    operator: TriageOperator
    value: str = Field(max_length=255)
    weight: int = 0
    enabled: bool = True


class TriageRuleRead(SQLModel):
    id: int
    name: str
    field: TriageField
    operator: TriageOperator
    value: str
    weight: int
    enabled: bool
    created_at: datetime


class TriageRuleUpdate(SQLModel):
    name: Optional[str] = None
    field: Optional[TriageField] = None
    operator: Optional[TriageOperator] = None
    value: Optional[str] = None
    weight: Optional[int] = None
    enabled: Optional[bool] = None
