from datetime import datetime, date, timezone
from typing import Annotated, Literal
from sqlmodel import SQLModel
from pydantic import BaseModel
from app.modules.medical_order.model import (
    Sex,
    OrderSetting,
    Modality,
    OrderState,
    MedicalPriority,
    MedicalOrder,
)
from pydantic import Field as PydanticField


class MedicalOrderCreate(SQLModel):
    external_id: str
    source_system: str
    description: str
    modality: Modality
    origin_service: str
    patient_location: str
    study_setting: OrderSetting = OrderSetting.SERVICE
    diagnosis: str
    observations: str | None = None
    order_date: datetime
    requesting_physician: str
    patient_lastname: str
    patient_name: str
    patient_pseudonym: str
    patient_dni: str
    patient_dob: date
    patient_sex: Sex
    is_urgent: bool = False
    triage_priority: MedicalPriority = MedicalPriority.ROUTINE


class PatientInfo(SQLModel):
    name: str
    lastname: str
    pseudonym: str
    dni: str
    dob: date
    sex: Sex


class OrderDetails(SQLModel):
    modality: Modality
    description: str
    location: str
    study_setting: OrderSetting
    diagnosis: str
    observations: str | None = None
    date: datetime
    requesting_physician: str
    original_priority: str
    triage_priority: MedicalPriority
    state: OrderState


class MedicalOrderRead(SQLModel):
    id: int | None
    external_id: str
    source_system: str
    created_at: datetime
    was_notified: bool
    sent_to_orthanc: bool = False
    study_instance_uid: str | None = None
    patient: PatientInfo
    order: OrderDetails

    @classmethod
    def from_orm(cls, obj: MedicalOrder) -> "MedicalOrderRead":
        return cls(
            id=obj.id,  # type: ignore
            external_id=obj.external_id,
            source_system=obj.source_system,
            created_at=obj.created_at.astimezone(datetime.now().astimezone().tzinfo),
            was_notified=obj.was_notified,
            sent_to_orthanc=obj.sent_to_orthanc,
            study_instance_uid=obj.study_instance_uid,
            patient=PatientInfo(
                name=obj.patient_name,
                lastname=obj.patient_lastname,
                pseudonym=obj.patient_pseudonym,
                dni=obj.patient_dni,
                dob=obj.patient_dob,
                sex=obj.patient_sex,
            ),
            order=OrderDetails(
                modality=obj.modality,
                description=obj.description,
                location=obj.patient_location,
                study_setting=obj.study_setting,
                diagnosis=obj.diagnosis,
                observations=obj.observations,
                date=obj.order_date,
                requesting_physician=obj.requesting_physician,
                original_priority="URGENTE" if obj.is_urgent else "RUTINA",
                triage_priority=obj.triage_priority,
                state=obj.order_state,
            ),
        )


class UpdateState(BaseModel):
    order_state: OrderState


class UpdateObservations(BaseModel):
    observations: str = PydanticField(min_length=4, max_length=2000)


class MedicalOrderPagination(BaseModel):
    items: list[MedicalOrderRead]
    total: int


class OrderBatchPayload(BaseModel):
    orders: list[MedicalOrderCreate]
    # Campos de instrumentacion (benchmark Escenario B). Opcionales:
    # permiten al backend computar T_n8n / T_proc / TDCC en milisegundos.
    ts_start: float | None = None
    ts_sent: float | None = None
    cycle_id: str | None = None


class BatchOrderResponse(BaseModel):
    status: str
    processed: int
    created: int
    created_ids: list[int] = []


class OrderFilters(BaseModel):
    offset: Annotated[int | None, PydanticField(ge=0)] = 0
    limit: Annotated[int | None, PydanticField(ge=1, le=100)] = 50
    patient_dni: Annotated[str | None, PydanticField(max_length=10, min_length=4)] = (
        None
    )
    q: Annotated[str | None, PydanticField(max_length=100)] = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    order_state: OrderState | None = None
    was_notified: bool | None = None
    modality: Modality | None = None
    source_system: Annotated[str | None, PydanticField(max_length=80)] = None
    study_setting: OrderSetting | None = None
    sort_by: Literal["created_at", "priority", "patient_name"] = "created_at"
    sort_dir: Literal["asc", "desc"] = "desc"


class OrderStats(BaseModel):
    total: int
    notified: int
    critical_pending: int
    by_state: dict[str, int]
    by_priority: dict[str, int]
    by_modality: dict[str, int]
    latest_created_at: datetime | None = None


class NotificationRead(SQLModel):
    id: int
    medical_order_id: int
    pseudonym_hash: str
    status: str
    payload_sent: str
    sent_at: datetime
    error_message: str | None = None
    patient_name: str | None = None
    patient_lastname: str | None = None

