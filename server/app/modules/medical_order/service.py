from datetime import datetime, timezone
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
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
from pydicom.uid import generate_uid
from app.core.orthanc_client import OrthancClient
from app.core.websocket import manager

class MedicalOrderService:
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, filters: OrderFilters) -> tuple[list[MedicalOrderRead], int]:
        async with UnitOfWork(self._session) as uow:
            items, total = await uow.orders.find_all_filtered(filters)
            return [MedicalOrderRead.from_orm(o) for o in items], total

    async def list_notifications(self, limit: int = 50, offset: int = 0):
        from app.modules.medical_order.notification_model import NotificacionEmitida
        from sqlmodel import select
        async with UnitOfWork(self._session) as uow:
            statement = select(NotificacionEmitida).order_by(NotificacionEmitida.sent_at.desc()).offset(offset).limit(limit)
            result = await uow.session.execute(statement)
            return result.scalars().all()

    async def _get_or_404(self, uow: UnitOfWork, order_id: int) -> MedicalOrder:
        order = await uow.orders.get_by_id(order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        return order

    async def _get_system_settings_or_404(self, uow: UnitOfWork):
        settings = await uow.settings.get_by_id(1)
        if not settings:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND, "Archivo de configuraciones no encontrado"
            )
        return settings

    async def _apply_triage(self, uow: UnitOfWork, order: MedicalOrder) -> MedicalOrder:
        rules = await uow.triage_rules.get_enabled()
        settings = await self._get_system_settings_or_404(uow)

        priority, criterios = TriageEngine.evaluate(order, rules, settings)
        order.triage_priority = priority
        order.criterios_evaluados = criterios
        order.triaged_at = datetime.now(timezone.utc)
        return order

    async def get_by_id(self, order_id: int) -> MedicalOrderRead:
        async with UnitOfWork(self._session) as uow:
            order = await self._get_or_404(uow, order_id)
            return MedicalOrderRead.from_orm(order)

    async def _send_to_orthanc(self, order: MedicalOrder) -> None:
        if not order.study_instance_uid:
            return
            
        fecha_prog = order.order_date.strftime("%Y%m%d")
        hora_prog = order.order_date.strftime("%H%M%S")
        
        sexo_map = {"MALE": "M", "FEMALE": "F", "OTHER": "O"}
        sexo = sexo_map.get(order.patient_sex.value, "O")
        
        dicom_json = {
            "0010,0010": f"{order.patient_lastname}^{order.patient_name}",
            "0010,0020": order.patient_dni,
            "0010,0030": order.patient_dob.strftime("%Y%m%d"),
            "0010,0040": sexo,
            "0020,000D": order.study_instance_uid,
            "0008,0050": f"ACC-{order.id}-{fecha_prog}",
            "0040,0100": [{
                "0008,0060": order.modality.value,
                "0040,0001": f"AET_{order.modality.value}_1",
                "0040,0002": fecha_prog,
                "0040,0003": hora_prog,
                "0040,0007": order.description
            }]
        }
        
        client = OrthancClient()
        success = await client.create_worklist(dicom_json)
        order.sent_to_orthanc = success

    async def create(self, data: MedicalOrderCreate) -> MedicalOrderRead:
        async with UnitOfWork(self._session) as uow:
            order = MedicalOrder.model_validate(data)
            await self._apply_triage(uow, order)
            
            order.study_instance_uid = generate_uid()
            order = await uow.orders.add(order)
            await uow.session.flush()
            
            await self._send_to_orthanc(order)
            uow.session.add(order)
            
            await manager.broadcast("orders_updated")
            return MedicalOrderRead.from_orm(order)

    async def create_batch(self, payload: OrderBatchPayload) -> BatchOrderResponse:
        async with UnitOfWork(self._session) as uow:
            rules = await uow.triage_rules.get_enabled()
            settings = await self._get_system_settings_or_404(uow)
            now = datetime.now(timezone.utc)

            existing = await uow.orders.find_existing_external_ids(
                [o.external_id for o in payload.orders]
            )
            orders: list[MedicalOrder] = []
            for data in payload.orders:
                if data.external_id in existing:
                    continue
                order = MedicalOrder.model_validate(data)
                priority, criterios = TriageEngine.evaluate(order, rules, settings)
                order.triage_priority = priority
                order.criterios_evaluados = criterios
                order.triaged_at = now
                order.study_instance_uid = generate_uid()
                orders.append(order)

            if orders:
                uow.orders.session.add_all(orders)
                await uow.orders.session.flush()
                
                for order in orders:
                    await self._send_to_orthanc(order)
                    uow.orders.session.add(order)

            created_ids = [o.id for o in orders] if orders else []
            
            if created_ids:
                await manager.broadcast("orders_updated")
                
            return BatchOrderResponse(
                status="success",
                processed=len(payload.orders),
                created=len(orders),
                created_ids=created_ids,
            )

    async def retriage(self, order_id: int) -> MedicalOrderRead:
        async with UnitOfWork(self._session) as uow:
            order = await self._get_or_404(uow, order_id)
            await self._apply_triage(uow, order)
            uow.orders.session.add(order)
            await manager.broadcast("orders_updated")
            return MedicalOrderRead.from_orm(order)

    async def update_state(self, order_id: int, data: UpdateState) -> MedicalOrderRead:
        async with UnitOfWork(self._session) as uow:
            order = await self._get_or_404(uow, order_id)
            order.order_state = data.order_state
            now = datetime.now(timezone.utc)

            if data.order_state == OrderState.FINALIZED:
                order.completed_at = now
            elif data.order_state == OrderState.CANCELLED:
                order.canceled_at = now

            uow.orders.session.add(order)
            await manager.broadcast("orders_updated")
            return MedicalOrderRead.from_orm(order)

    async def update_observations(
        self, order_id: int, data: UpdateObservations
    ) -> MedicalOrderRead:
        async with UnitOfWork(self._session) as uow:
            order = await self._get_or_404(uow, order_id)

            order.observations = data.observations
            uow.orders.session.add(order)
            return MedicalOrderRead.from_orm(order)
