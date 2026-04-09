from fastapi import APIRouter, Depends, BackgroundTasks, Request
from app.medicalorder.service import create_order, get_all, create_orders_batch_service
from sqlmodel import Session
from app.medicalorder.model import (
    MedicalOrderRead,
    MedicalOrderCreate,
    MedicalOrderPagination,
    BatchOrderResponse,
    OrderBatchPayload,
)
from app.database import get_session
from app.medicalorder.notifier import evaluate_and_notify
from typing import List

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


@router.post("/batch", response_model=BatchOrderResponse)
def create_batch_orders(
    payload: OrderBatchPayload,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
):
    data_list = payload.orders
    print("Ordenes ", data_list)

    nuevas_ordenes = create_orders_batch_service(session, data_list)

    for order in nuevas_ordenes:
        background_tasks.add_task(evaluate_and_notify, order.id)

    return {
        "status": "success",
        "processed": len(data_list),
        "created": len(nuevas_ordenes),
    }


@router.post("/studies")
async def create_studies(request: Request):
    body = await request.body()
    print(body)
    return {}
