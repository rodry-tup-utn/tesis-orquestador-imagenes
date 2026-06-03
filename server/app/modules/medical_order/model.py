from datetime import datetime, timezone, date
from typing import Optional
from sqlmodel import SQLModel, Field
from enum import Enum
from sqlalchemy import Column, DateTime


class Sex(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class OrderSetting(str, Enum):
    BEDSIDE = "En Cama"
    SERVICE = "En Efector"


class Modality(str, Enum):
    CT = "CT"
    MR = "MR"
    US = "US"
    DX = "DX"
    MG = "MG"
    XA = "XA"
    NM = "NM"
    PT = "PT"


class OrderState(str, Enum):
    PENDING = "Pendiente"
    PROCESS = "En Proceso"
    FINALIZED = "Finalizada"
    CANCELLED = "Cancelada"


class MedicalPriority(str, Enum):
    order: int
    CRITICAL = (0, "Crítico")
    PRIORITY = (1, "Prioritario")
    ROUTINE = (2, "Rutina")

    def __new__(cls, value: int, display: str):
        obj = str.__new__(cls, display)
        obj._value_ = display
        obj.order = value
        return obj


class MedicalOrder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True, unique=True)
    source_system: str = Field(max_length=80)

    # Datos de la orden médica
    description: str = Field(max_length=255)
    modality: Modality
    origin_service: str = Field(max_length=255)
    patient_location: str = Field(index=True, max_length=255)
    study_setting: OrderSetting = Field(index=True, default=OrderSetting.SERVICE)
    diagnosis: str = Field(index=True, max_length=255)
    observations: str | None = Field(max_length=255, default=None)
    order_date: datetime = Field(sa_column=Column(DateTime(timezone=True)))
    requesting_physician: str = Field(max_length=255, min_length=1)

    # Datos demográficos del paciente
    patient_lastname: str = Field(max_length=255, min_length=2)
    patient_name: str = Field(max_length=255, min_length=2)
    patient_pseudonym: str = Field(max_length=64, min_length=1)
    patient_dni: str = Field(max_length=20, min_length=1)
    patient_dob: date
    patient_sex: Sex

    # Datos del urgencia
    is_urgent: bool = Field(default=False)
    triage_priority: MedicalPriority = Field(default=MedicalPriority.ROUTINE)

    # Estado y marcas de hora
    order_state: OrderState = Field(default=OrderState.PENDING)
    triaged_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    canceled_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    completed_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True)),
    )

    # Bandera por si fue notificado
    was_notified: bool = Field(default=False)
