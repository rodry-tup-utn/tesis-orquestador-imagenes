from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlmodel import Session
from app.core.unit_of_work import UnitOfWork
from app.modules.medical_order.model import MedicalOrder, OrderState
from app.modules.medical_order.schemas import (
    MedicalOrderCreate,
    MedicalOrderRead,
    BatchOrderResponse,
    OrderFilters,
    OrderBatchPayload,
    UpdateState,
    UpdateObservations,
)
from app.modules.triage.triage import TriageEngine


class MedicalOrderService:
    _session: Session

    def __init__(self, session: Session) -> None:
        self._session = session

    def list_all(self, filters: OrderFilters) -> tuple[list[MedicalOrderRead], int]:
        with UnitOfWork(self._session) as uow:
            items, total = uow.orders.find_all_filtered(filters)
            return [MedicalOrderRead.from_orm(o) for o in items], total

    def _get_or_404(self, uow: UnitOfWork, order_id: int) -> MedicalOrder:
        order = uow.orders.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    def _get_system_settings_or_404(self, uow: UnitOfWork):
        settings = uow.settings.get_by_id(1)
        if not settings:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Archivo de configuraciones no encontrado"
            )
        return settings

    def _apply_triage(self, uow: UnitOfWork, order: MedicalOrder) -> MedicalOrder:
        rules = uow.triage_rules.get_enabled()
        settings = self._get_system_settings_or_404(uow)

        order.triage_priority = TriageEngine.evaluate(order, rules, settings)
        order.triaged_at = datetime.now(timezone.utc)
        return order

    def get_by_id(self, order_id: int) -> MedicalOrderRead:
        with UnitOfWork(self._session) as uow:
            order = self._get_or_404(uow, order_id)
            return MedicalOrderRead.from_orm(order)

    def create(self, data: MedicalOrderCreate) -> MedicalOrderRead:
        with UnitOfWork(self._session) as uow:
            order = MedicalOrder.model_validate(data)
            self._apply_triage(uow, order)
            order = uow.orders.add(order)
            return MedicalOrderRead.from_orm(order)

    def create_batch(self, payload: OrderBatchPayload) -> BatchOrderResponse:
        with UnitOfWork(self._session) as uow:
            rules = uow.triage_rules.get_enabled()
            settings = self._get_system_settings_or_404(uow)
            now = datetime.now(timezone.utc)

            existing = uow.orders.find_existing_external_ids(
                [o.external_id for o in payload.orders]
            )
            orders: list[MedicalOrder] = []
            for data in payload.orders:
                if data.external_id in existing:
                    continue
                order = MedicalOrder.model_validate(data)
                order.triage_priority = TriageEngine.evaluate(order, rules, settings)
                order.triaged_at = now
                orders.append(order)

            if orders:
                uow.orders.session.add_all(orders)
                uow.orders.session.flush()

            created_ids = [o.id for o in orders] if orders else []
            return BatchOrderResponse(
                status="success",
                processed=len(payload.orders),
                created=len(orders),
                created_ids=created_ids,  # type: ignore
            )

    def retriage(self, order_id: int) -> MedicalOrderRead:
        with UnitOfWork(self._session) as uow:
            order = self._get_or_404(uow, order_id)
            self._apply_triage(uow, order)
            uow.orders.session.add(order)
            return MedicalOrderRead.from_orm(order)

    def update_state(self, order_id: int, data: UpdateState) -> MedicalOrderRead:
        with UnitOfWork(self._session) as uow:
            order = self._get_or_404(uow, order_id)
            order.order_state = data.order_state
            now = datetime.now(timezone.utc)

            if data.order_state == OrderState.FINALIZED:
                order.completed_at = now
            elif data.order_state == OrderState.CANCELLED:
                order.canceled_at = now

            uow.orders.session.add(order)
            return MedicalOrderRead.from_orm(order)

    def update_observations(
        self, order_id: int, data: UpdateObservations
    ) -> MedicalOrderRead:
        with UnitOfWork(self._session) as uow:
            order = self._get_or_404(uow, order_id)

            order.observations = data.observations
            uow.orders.session.add(order)
            return MedicalOrderRead.from_orm(order)
