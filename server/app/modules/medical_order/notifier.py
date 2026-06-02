import logging

import requests
from sqlmodel import Session, select, col

from app.core.config import settings
from app.core.database import engine
from app.core.unit_of_work import UnitOfWork
from app.modules.medical_order.model import MedicalOrder, MedicalPriority
from app.modules.systemsettings.model import SystemSettings

logger = logging.getLogger(__name__)


class NotifierService:
    _session: Session

    def __init__(self, session: Session) -> None:
        self._session = session

    def _should_notify(self, order: MedicalOrder) -> bool:
        settings = self._session.get(SystemSettings, 1)
        if not settings or not settings.notifications_enabled:
            return False
        if order.triage_priority == MedicalPriority.ROUTINE:
            return False
        if (
            not settings.notify_priority
            and order.triage_priority != MedicalPriority.CRITICAL
        ):
            return False
        return True

    def _build_payload(self, order: MedicalOrder) -> dict:
        return {
            "message": "Alerta médica crítica",
            "patient": f"{order.patient_name} {order.patient_lastname}",
            "diagnosis": order.diagnosis,
            "date": order.order_date.isoformat(),
            "location": order.patient_location,
            "setting": order.study_setting.value,
            "order_id": order.id,
        }

    def _send(self, order: MedicalOrder) -> bool:
        payload = self._build_payload(order)
        try:
            resp = requests.post(settings.url_webhook_n8n, json=payload, timeout=5)
            if resp.status_code != 200:
                logger.warning(
                    "n8n respondió %d para order %d", resp.status_code, order.id
                )
                return False
            return True
        except Exception as e:
            logger.error("Error de conexión con n8n para order %d: %s", order.id, e)
            return False

    def notify(self, order_id: int) -> bool:
        with UnitOfWork(self._session) as uow:
            order = uow.orders.get_by_id(order_id)
            if not order or order.was_notified:
                return False
            if not self._should_notify(order):
                return False

            if not self._send(order):
                return False

            order.was_notified = True
            uow.session.add(order)
            logger.info("Order %d notificada exitosamente", order_id)
            return True

    def notify_many(self, order_ids: list[int]) -> int:
        if not order_ids:
            return 0

        with UnitOfWork(self._session) as uow:
            orders = uow.orders.session.exec(
                select(MedicalOrder).where(col(MedicalOrder.id).in_(order_ids))
            ).all()

            notified = 0
            for order in orders:
                if order.was_notified:
                    continue
                if not self._should_notify(order):
                    continue
                if not self._send(order):
                    continue

                order.was_notified = True
                uow.session.add(order)
                notified += 1
                logger.info("Order %d notificada (batch)", order.id)

            return notified


def evaluate_and_notify(order_id: int):
    if not settings.url_webhook_n8n:
        logger.warning("URL_WEBHOOK_N8N no configurada")
        return
    try:
        with Session(engine) as session:
            NotifierService(session).notify(order_id)
    except Exception as e:
        logger.error("Error en notificador para order %d: %s", order_id, e)


def evaluate_and_notify_many(order_ids: list[int]):
    if not settings.url_webhook_n8n or not order_ids:
        logger.warning("URL_WEBHOOK_N8N no configurada o sin órdenes")
        return
    try:
        with Session(engine) as session:
            notified = NotifierService(session).notify_many(order_ids)
            if notified:
                logger.info(
                    "Lote: %d órdenes notificadas de %d", notified, len(order_ids)
                )
    except Exception as e:
        logger.error("Error en notificador batch: %s", e)
