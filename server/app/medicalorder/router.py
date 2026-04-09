from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
import app.medicalorder.service as service
from sqlmodel import Session
from app.medicalorder.model import (
    MedicalOrderRead,
    MedicalOrderCreate,
    MedicalOrderPagination,
    BatchOrderResponse,
    OrderBatchPayload,
    MedicalOrderUpdate,
)
from app.database import get_session
from app.medicalorder.notifier import evaluate_and_notify

router = APIRouter(prefix="/orders", tags=["Ordenes"])


@router.get("", response_model=MedicalOrderPagination)
def get_orders(
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),
    only_active: bool = True,
):
    items, total = service.get_all(session, skip, limit, only_active)

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
    order = service.create_order(session, data)

    if order is None or order.id is None:
        raise HTTPException(400, "No se pudo crear la orden")

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

    nuevas_ordenes = service.create_orders_batch_service(session, data_list)

    for order in nuevas_ordenes:
        background_tasks.add_task(evaluate_and_notify, order.id)

    return {
        "status": "success",
        "processed": len(data_list),
        "created": len(nuevas_ordenes),
    }


@router.get("/{order_id}", response_model=MedicalOrderRead)
def get_order_id(order_id: int, session: Session = Depends(get_session)):
    try:
        order = service.get_order_id(session, order_id)
        return MedicalOrderRead.from_orm_flat(order)
    except LookupError:
        raise HTTPException(404, f"Orden con id {order_id} no encontrada")


@router.delete("/{order_id}")
def soft_delete(order_id: int, session: Session = Depends(get_session)):
    try:
        order = service.delete_order(session, order_id)
        return MedicalOrderRead.from_orm_flat(order)

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # Para cualquier otro error inesperado (DB, etc.)
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")


@router.patch("/{order_id}", response_model=MedicalOrderRead)
def update_order(
    order_id: int,
    data: MedicalOrderUpdate,
    session: Session = Depends(get_session),
):
    try:

        order = service.update_order(session, order_id, data)
        if not order:
            raise HTTPException(404, f"Orden con id {order_id} no encontrada")

        return MedicalOrderRead.from_orm_flat(order)
    except LookupError as e:
        raise HTTPException(404, detail=str(e))
