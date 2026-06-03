from fastapi import APIRouter, BackgroundTasks, Depends
from app.modules.medical_order.service import MedicalOrderService
from app.modules.medical_order.schemas import (
    MedicalOrderCreate,
    MedicalOrderRead,
    MedicalOrderPagination,
    OrderBatchPayload,
    BatchOrderResponse,
    OrderFilters,
    UpdateState,
    UpdateObservations,
)
from sqlmodel import Session
from fastapi import Path
from app.core.database import get_session
from app.modules.medical_order.notifier import evaluate_and_notify, evaluate_and_notify_many
from typing import Annotated

router = APIRouter(prefix="/orders", tags=["Ordenes"])


def get_order_service(session: Session = Depends(get_session)) -> MedicalOrderService:
    return MedicalOrderService(session)


@router.get("", response_model=MedicalOrderPagination)
def list_orders(
    filters: OrderFilters = Depends(),
    svc: MedicalOrderService = Depends(get_order_service),
):
    items, total = svc.list_all(filters)
    return MedicalOrderPagination(items=items, total=total)


@router.post("", response_model=MedicalOrderRead, status_code=201)
def create_order(
    data: MedicalOrderCreate,
    background_tasks: BackgroundTasks,
    svc: MedicalOrderService = Depends(get_order_service),
):
    order = svc.create(data)
    if order.id:
        background_tasks.add_task(evaluate_and_notify, order.id)
    return order


@router.post("/batch", response_model=BatchOrderResponse)
def create_orders_batch(
    payload: OrderBatchPayload,
    background_tasks: BackgroundTasks,
    svc: MedicalOrderService = Depends(get_order_service),
):
    result = svc.create_batch(payload)
    if result.created_ids:
        background_tasks.add_task(evaluate_and_notify_many, result.created_ids)
    return result


@router.get("/{order_id}", response_model=MedicalOrderRead)
def get_order(
    order_id: Annotated[int, Path(ge=1)],
    svc: MedicalOrderService = Depends(get_order_service),
):
    return svc.get_by_id(order_id)


@router.post("/{order_id}/retriage", response_model=MedicalOrderRead)
def retriage_order(
    order_id: Annotated[int, Path(ge=1)],
    svc: MedicalOrderService = Depends(get_order_service),
):
    return svc.retriage(order_id)


@router.patch("/{order_id}/state", response_model=MedicalOrderRead)
def update_order_state(
    order_id: Annotated[int, Path(ge=1)],
    data: UpdateState,
    svc: MedicalOrderService = Depends(get_order_service),
):
    return svc.update_state(order_id, data)


@router.patch("/{order_id}/observations", response_model=MedicalOrderRead)
def update_order_observations(
    order_id: Annotated[int, Path(ge=1)],
    data: UpdateObservations,
    svc: MedicalOrderService = Depends(get_order_service),
):
    return svc.update_observations(order_id, data)
