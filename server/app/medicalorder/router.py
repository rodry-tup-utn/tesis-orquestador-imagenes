from fastapi import APIRouter, Depends, BackgroundTasks
from app.medicalorder.service import create_order, get_all
from sqlmodel import Session
from app.medicalorder.model import (
    MedicalOrderRead,
    MedicalOrderCreate,
    MedicalOrderPagination,
)
from app.database import get_session
from app.medicalorder.notifier import evaluate_and_notify

router = APIRouter(prefix="/orders", tags=["Ordenes"])


@router.get("", response_model=MedicalOrderPagination)
def get_orders(skip: int = 0, limit: int = 50, session: Session = Depends(get_session)):
    items, total = get_all(session, skip, limit)

    return {
        "items": [MedicalOrderRead.from_orm_flat(order) for order in items],
        "total": total,
    }


@router.post("", response_model=MedicalOrderRead)
def create(
    data: MedicalOrderCreate,
    background_task: BackgroundTasks,
    session: Session = Depends(get_session),
):
    order = create_order(session, data)

    if order is None or order.id is None:
        print(f"⚠️ Alerta: La orden con ID {order.id} no se encontró en la DB.")
        return

    background_task.add_task(evaluate_and_notify, order.id)

    return MedicalOrderRead.from_orm_flat(order)
