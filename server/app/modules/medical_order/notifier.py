import logging
import httpx
import hashlib
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, col
from app.core.config import settings
from app.core.database import get_session
from app.core.unit_of_work import UnitOfWork
from app.modules.medical_order.model import MedicalOrder, MedicalPriority
from app.modules.systemsettings.model import SystemSettings
from app.modules.medical_order.notification_model import NotificacionEmitida

logger = logging.getLogger(__name__)

class NotifierService:
    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _should_notify(self, order: MedicalOrder) -> bool:
        settings_db = await self._session.get(SystemSettings, 1)
        if not settings_db or not settings_db.notifications_enabled:
            return False
        if order.triage_priority == MedicalPriority.ROUTINE:
            return False
        if (
            not settings_db.notify_priority
            and order.triage_priority != MedicalPriority.CRITICAL
        ):
            return False
        return True

    def _build_payload(self, order: MedicalOrder) -> dict:
        # Seudonimización con SHA-256 según requerimientos de tesis
        raw_str = f"{settings.secret_key}:{order.patient_dni}"
        pseudonym = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        
        # Para la demo incluimos nombre y apellido, aunque en un entorno real 
        # estrictamente solo se mandaría el seudónimo por protección de datos PHI.
        payload = {
            "message": "Alerta médica crítica",
            "patient_pseudonym": pseudonym,
            "patient_name": f"{order.patient_lastname}, {order.patient_name}",
            "diagnosis": order.diagnosis,
            "priority": order.triage_priority.value,
            "date": datetime.now(ZoneInfo("America/Argentina/Mendoza")).strftime("%d/%m/%Y %H:%M"),
            "location": order.patient_location,
            "setting": order.study_setting.value,
            "order_id": order.id,
        }
        logger.info("PAYLOAD a n8n: %s", payload)
        return payload

    async def notify(self, order_id: int) -> bool:
        async with UnitOfWork(self._session) as uow:
            order = await uow.orders.get_by_id(order_id)
            if not order or order.was_notified:
                return False
            if not await self._should_notify(order):
                return False

            payload = self._build_payload(order)
            pseudonym = payload["patient_pseudonym"]
            
            notificacion = NotificacionEmitida(
                medical_order_id=order.id,
                pseudonym_hash=pseudonym,
                payload_sent=json.dumps(payload),
                status="PENDING"
            )

            success = False
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.post(settings.url_webhook_n8n, json=payload, timeout=5)
                    if resp.status_code != 200:
                        logger.warning(
                            "n8n respondió %d para order %d", resp.status_code, order.id
                        )
                        notificacion.status = "FAILED"
                        notificacion.error_message = f"HTTP {resp.status_code}"
                    else:
                        notificacion.status = "SUCCESS"
                        success = True
            except Exception as e:
                logger.error("Error de conexión con n8n para order %d: %s", order.id, e)
                notificacion.status = "FAILED"
                notificacion.error_message = str(e)

            uow.session.add(notificacion)

            if success:
                order.was_notified = True
                uow.session.add(order)
                logger.info("Order %d notificada exitosamente a n8n", order_id)
            
            return success

    async def notify_many(self, order_ids: list[int]) -> int:
        if not order_ids:
            return 0

        async with UnitOfWork(self._session) as uow:
            statement = select(MedicalOrder).where(col(MedicalOrder.id).in_(order_ids))
            result = await uow.orders.session.execute(statement)
            orders = result.scalars().all()

            notified = 0
            for order in orders:
                if order.was_notified:
                    continue
                if not await self._should_notify(order):
                    continue

                payload = self._build_payload(order)
                pseudonym = payload["patient_pseudonym"]
                
                notificacion = NotificacionEmitida(
                    medical_order_id=order.id,
                    pseudonym_hash=pseudonym,
                    payload_sent=json.dumps(payload),
                    status="PENDING"
                )

                success = False
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.post(settings.url_webhook_n8n, json=payload, timeout=5)
                        if resp.status_code != 200:
                            logger.warning(
                                "n8n respondió %d para order %d", resp.status_code, order.id
                            )
                            notificacion.status = "FAILED"
                            notificacion.error_message = f"HTTP {resp.status_code}"
                        else:
                            notificacion.status = "SUCCESS"
                            success = True
                except Exception as e:
                    logger.error("Error de conexión con n8n para order %d: %s", order.id, e)
                    notificacion.status = "FAILED"
                    notificacion.error_message = str(e)

                uow.session.add(notificacion)

                if success:
                    order.was_notified = True
                    uow.session.add(order)
                    notified += 1
                    logger.info("Order %d notificada (batch)", order.id)

            return notified


async def evaluate_and_notify(order_id: int):
    if not settings.url_webhook_n8n:
        logger.warning("URL_WEBHOOK_N8N no configurada")
        return
    try:
        async for session in get_session():
            await NotifierService(session).notify(order_id)
            await session.commit()
    except Exception as e:
        logger.error("Error en notificador para order %d: %s", order_id, e)


async def evaluate_and_notify_many(order_ids: list[int]):
    if not settings.url_webhook_n8n or not order_ids:
        logger.warning("URL_WEBHOOK_N8N no configurada o sin órdenes")
        return
    try:
        async for session in get_session():
            notified = await NotifierService(session).notify_many(order_ids)
            await session.commit()
            if notified:
                logger.info(
                    "Lote: %d órdenes notificadas de %d", notified, len(order_ids)
                )
    except Exception as e:
        logger.error("Error en notificador batch: %s", e)
