from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field


class MedicalOrderBase(SQLModel):
    external_id: str = Field(index=True, unique=True)
    origin: str
    modality: str
    medical_order: str
    location: str = Field(index=True)
    study_setting: str
    diagnosis: str
    observations: Optional[str] = None
    patient_name: str
    patient_lastname: str
    patient_pseudonym: str
    patient_dni: str
    patient_dob: str
    patient_age: int
    requesting_physician: str
    is_urgent: bool = Field(default=False)
    is_active: bool = Field(default=True)


class MedicalOrder(MedicalOrderBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    was_notified: bool = Field(default=False)
    is_critical: bool = Field(default=False)


class MedicalOrderCreate(MedicalOrderBase):
    pass


class MedicalOrderRead(MedicalOrderBase):
    id: int
    created_at: datetime
    was_notified: bool
