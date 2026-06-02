from typing import Sequence
from sqlmodel import Session, select, func, col
from sqlalchemy import case
from app.core.repository import BaseRepository
from app.modules.medical_order.model import MedicalOrder, MedicalPriority
from app.modules.medical_order.schemas import OrderFilters


class MedicalOrderRepository(BaseRepository[MedicalOrder]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, MedicalOrder)

    def find_by_external_id(self, external_id: str) -> MedicalOrder | None:
        statement = select(MedicalOrder).where(MedicalOrder.external_id == external_id)
        return self.session.exec(statement).first()

    def find_existing_external_ids(self, ids: list[str]) -> set[str]:
        statement = select(MedicalOrder.external_id).where(
            col(MedicalOrder.external_id).in_(ids)
        )
        return set(self.session.exec(statement).all())

    def _build_order_by(self, sort_by: str) -> tuple:
        if sort_by == "priority":
            return (
                case(
                    *(
                        (col(MedicalOrder.triage_priority) == p, p.order)
                        for p in MedicalPriority
                    ),
                    else_=len(list(MedicalPriority)),
                ),
                col(MedicalOrder.created_at).desc(),
            )
        return (col(MedicalOrder.created_at).desc(),)

    def find_all_filtered(
        self, filters: OrderFilters
    ) -> tuple[Sequence[MedicalOrder], int]:
        statement = select(MedicalOrder)

        if filters.start_date:
            statement = statement.where(MedicalOrder.order_date >= filters.start_date)

        if filters.end_date:
            statement = statement.where(MedicalOrder.order_date <= filters.end_date)

        if filters.patient_dni:
            statement = statement.where(MedicalOrder.patient_dni == filters.patient_dni)

        if filters.order_state:
            statement = statement.where(MedicalOrder.order_state == filters.order_state)

        if filters.was_notified:
            statement = statement.where(
                MedicalOrder.was_notified == filters.was_notified
            )

        order_exprs = self._build_order_by(filters.sort_by)

        count_statement = select(func.count()).select_from(statement.subquery())
        total = self.session.exec(count_statement).one()
        items = self.session.exec(
            statement.offset(filters.offset).limit(filters.limit).order_by(*order_exprs)
        ).all()

        return items, total
