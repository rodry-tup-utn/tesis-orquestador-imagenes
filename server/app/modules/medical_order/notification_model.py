from sqlmodel import SQLModel, Field
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime
from typing import Optional


class NotificacionEmitida(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    medical_order_id: int = Field(foreign_key="medicalorder.id", index=True)
    pseudonym_hash: str = Field(max_length=64)
    status: str = Field(max_length=50)  # "SUCCESS", "FAILED"
    payload_sent: str = Field()
    sent_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        sa_column=Column(DateTime(timezone=True)),
    )
    error_message: Optional[str] = Field(default=None)
