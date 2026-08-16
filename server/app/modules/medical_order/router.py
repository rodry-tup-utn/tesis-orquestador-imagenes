from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession
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
    NotificationRead,
    OrderStats,
)
from fastapi import Path
from app.core.database import get_session
from app.modules.medical_order.notifier import evaluate_and_notify, evaluate_and_notify_many
from app.core.metrics import now_ms, log_metric
from typing import Annotated

router = APIRouter(prefix="/orders", tags=["Ordenes"])


def get_order_service(session: AsyncSession = Depends(get_session)) -> MedicalOrderService:
    return MedicalOrderService(session)


@router.get("", response_model=MedicalOrderPagination)
async def list_orders(
    filters: OrderFilters = Depends(),
    svc: MedicalOrderService = Depends(get_order_service),
):
    items, total = await svc.list_all(filters)
    return MedicalOrderPagination(items=items, total=total)


@router.get("/stats", response_model=OrderStats)
async def get_stats_endpoint(
    svc: MedicalOrderService = Depends(get_order_service),
):
    return await svc.get_stats()


@router.get("/notifications", response_model=list[NotificationRead])
async def list_notifications_endpoint(
    offset: int = 0, limit: int = 50,
    svc: MedicalOrderService = Depends(get_order_service),
):
    return await svc.list_notifications(limit, offset)


@router.post("", response_model=MedicalOrderRead, status_code=201)
async def create_order(
    data: MedicalOrderCreate,
    background_tasks: BackgroundTasks,
    svc: MedicalOrderService = Depends(get_order_service),
):
    t_received = now_ms()
    order = await svc.create(data)
    t_done = now_ms()
    log_metric(
        "t_proc",
        event="single",
        external_id=data.external_id,
        t_received=round(t_received, 3),
        t_done=round(t_done, 3),
        T_server=round(t_done - t_received, 3),
    )
    if order.id:
        background_tasks.add_task(evaluate_and_notify, order.id, t_received)
    return order


@router.post("/batch", response_model=BatchOrderResponse)
async def create_orders_batch(
    payload: OrderBatchPayload,
    background_tasks: BackgroundTasks,
    svc: MedicalOrderService = Depends(get_order_service),
):
    t_received = now_ms()
    if payload.cycle_id:
        log_metric(
            "t_proc",
            cycle_id=payload.cycle_id,
            event="received",
            ts_start=round(payload.ts_start, 3) if payload.ts_start else None,
            ts=round(t_received, 3),
        )
    result = await svc.create_batch(payload)
    t_done = now_ms()
    T_server = t_done - t_received
    T_n8n = (t_received - payload.ts_start) if payload.ts_start else None
    T_proc = (t_done - payload.ts_start) if payload.ts_start else None
    log_metric(
        "t_proc",
        cycle_id=payload.cycle_id,
        event="done",
        ts_start=round(payload.ts_start, 3) if payload.ts_start else None,
        ts_sent=round(payload.ts_sent, 3) if payload.ts_sent else None,
        t_received=round(t_received, 3),
        t_done=round(t_done, 3),
        T_n8n=round(T_n8n, 3) if T_n8n is not None else None,
        T_server=round(T_server, 3),
        T_proc=round(T_proc, 3) if T_proc is not None else None,
        created=result.created,
    )
    if result.created_ids:
        background_tasks.add_task(
            evaluate_and_notify_many,
            result.created_ids,
            payload.cycle_id,
            t_received,
        )
    return result


@router.get("/{order_id}", response_model=MedicalOrderRead)
async def get_order(
    order_id: Annotated[int, Path(ge=1)],
    svc: MedicalOrderService = Depends(get_order_service),
):
    return await svc.get_by_id(order_id)


@router.post("/{order_id}/retriage", response_model=MedicalOrderRead)
async def retriage_order(
    order_id: Annotated[int, Path(ge=1)],
    svc: MedicalOrderService = Depends(get_order_service),
):
    return await svc.retriage(order_id)


@router.patch("/{order_id}/state", response_model=MedicalOrderRead)
async def update_order_state(
    order_id: Annotated[int, Path(ge=1)],
    data: UpdateState,
    svc: MedicalOrderService = Depends(get_order_service),
):
    return await svc.update_state(order_id, data)


@router.patch("/{order_id}/observations", response_model=MedicalOrderRead)
async def update_order_observations(
    order_id: Annotated[int, Path(ge=1)],
    data: UpdateObservations,
    svc: MedicalOrderService = Depends(get_order_service),
):
    return await svc.update_observations(order_id, data)


@router.post("/{order_id}/send-to-orthanc", response_model=MedicalOrderRead)
async def send_order_to_orthanc(
    order_id: Annotated[int, Path(ge=1)],
    svc: MedicalOrderService = Depends(get_order_service),
):
    return await svc.send_to_orthanc(order_id)
