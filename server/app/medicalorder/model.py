from typing import Optional
from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from pydantic import BaseModel
from typing import List


class MedicalOrderBase(SQLModel):
    external_id: str = Field(index=True, unique=True)
    origin: str
    modality: str
    medical_order: str
    location: str = Field(index=True)
    study_setting: str
    diagnosis: str
    observations: Optional[str] = None
    internal_notes: Optional[str] = None
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


# READ agrupado para mejor consumo desde cliente


class PatientInfo(SQLModel):
    name: str
    lastname: str
    pseudonym: str
    dni: str
    dob: str
    age: int


class OrderDetails(SQLModel):
    modality: str
    medical_order: str
    location: str
    study_setting: str
    diagnosis: str
    observations: Optional[str] = None
    internal_notes: Optional[str]
    requesting_physician: str
    is_urgent: bool
    is_active: bool
    is_critical: bool


class MedicalOrderRead(SQLModel):
    id: int
    external_id: str
    origin: str
    created_at: datetime
    was_notified: bool
    patient: PatientInfo
    order: OrderDetails

    @classmethod
    def from_orm_flat(cls, obj: MedicalOrder) -> "MedicalOrderRead":
        assert obj.id is not None, "La orden debe tener un id"
        return cls(
            id=obj.id,
            external_id=obj.external_id,
            origin=obj.origin,
            created_at=obj.created_at,
            was_notified=obj.was_notified,
            patient=PatientInfo(
                name=obj.patient_name,
                lastname=obj.patient_lastname,
                pseudonym=obj.patient_pseudonym,
                dni=obj.patient_dni,
                dob=obj.patient_dob,
                age=obj.patient_age,
            ),
            order=OrderDetails(
                modality=obj.modality,
                medical_order=obj.medical_order,
                location=obj.location,
                study_setting=obj.study_setting,
                diagnosis=obj.diagnosis,
                observations=obj.observations,
                internal_notes=obj.internal_notes,
                requesting_physician=obj.requesting_physician,
                is_urgent=obj.is_urgent,
                is_active=obj.is_active,
                is_critical=obj.is_critical,
            ),
        )


class MedicalOrderUpdate(SQLModel):
    is_active: Optional[bool] = None
    is_critical: Optional[bool] = None
    was_notified: Optional[bool] = None
    internal_notes: Optional[str] = None


class MedicalOrderPagination(BaseModel):
    items: List[MedicalOrderRead]
    total: int


class BatchOrderResponse(BaseModel):
    status: str
    processed: int
    created: int


class OrderBatchPayload(BaseModel):
    orders: List[MedicalOrderCreate]
