from typing import Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func, col
from sqlalchemy import case, or_
from app.core.repository import BaseRepository
from app.modules.medical_order.model import (
    MedicalOrder,
    MedicalPriority,
    OrderState,
    Modality,
)
from app.modules.medical_order.schemas import OrderFilters, OrderStats


class MedicalOrderRepository(BaseRepository[MedicalOrder]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MedicalOrder)

    async def find_by_external_id(self, external_id: str) -> MedicalOrder | None:
        statement = select(MedicalOrder).where(MedicalOrder.external_id == external_id)
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def find_existing_external_ids(self, ids: list[str]) -> set[str]:
        statement = select(MedicalOrder.external_id).where(
            col(MedicalOrder.external_id).in_(ids)
        )
        result = await self.session.execute(statement)
        return set(result.scalars().all())

    def _direction(self, expr, sort_dir: str):
        return expr.desc() if sort_dir == "desc" else expr.asc()

    def _build_order_by(self, sort_by: str, sort_dir: str) -> tuple:
        priority_order = case(
            *(
                (col(MedicalOrder.triage_priority) == p, p.order)
                for p in MedicalPriority
            ),
            else_=len(list(MedicalPriority)),
        )
        if sort_by == "priority":
            return (
                self._direction(priority_order, sort_dir),
                self._direction(col(MedicalOrder.created_at), sort_dir),
            )
        if sort_by == "patient_name":
            return (
                self._direction(func.lower(col(MedicalOrder.patient_lastname)), sort_dir),
                self._direction(func.lower(col(MedicalOrder.patient_name)), sort_dir),
            )
        return (self._direction(col(MedicalOrder.created_at), sort_dir),)

    async def find_all_filtered(
        self, filters: OrderFilters
    ) -> tuple[Sequence[MedicalOrder], int]:
        statement = select(MedicalOrder)

        if filters.start_date:
            statement = statement.where(MedicalOrder.order_date >= filters.start_date)

        if filters.end_date:
            statement = statement.where(MedicalOrder.order_date <= filters.end_date)

        if filters.patient_dni:
            statement = statement.where(MedicalOrder.patient_dni == filters.patient_dni)

        if filters.q:
            pattern = f"%{filters.q.strip()}%"
            statement = statement.where(
                or_(
                    MedicalOrder.patient_name.ilike(pattern),
                    MedicalOrder.patient_lastname.ilike(pattern),
                    MedicalOrder.patient_dni.ilike(pattern),
                    MedicalOrder.external_id.ilike(pattern),
                )
            )

        if filters.order_state:
            statement = statement.where(MedicalOrder.order_state == filters.order_state)

        if filters.was_notified:
            statement = statement.where(
                MedicalOrder.was_notified == filters.was_notified
            )

        if filters.modality:
            statement = statement.where(MedicalOrder.modality == filters.modality)

        if filters.source_system:
            statement = statement.where(
                MedicalOrder.source_system == filters.source_system
            )

        if filters.study_setting:
            statement = statement.where(
                MedicalOrder.study_setting == filters.study_setting
            )

        order_exprs = self._build_order_by(filters.sort_by, filters.sort_dir)

        count_statement = select(func.count()).select_from(statement.subquery())
        total_result = await self.session.execute(count_statement)
        total = total_result.scalar_one()
        
        items_result = await self.session.execute(
            statement.offset(filters.offset).limit(filters.limit).order_by(*order_exprs)
        )
        items = items_result.scalars().all()

        return items, total

    @staticmethod
    def _display_value(enum_cls, stored: str) -> str:
        try:
            return enum_cls[stored].value
        except KeyError:
            return stored

    async def get_stats(self) -> OrderStats:
        total = await self.count()

        notified = (
            await self.session.execute(
                select(func.count())
                .select_from(MedicalOrder)
                .where(MedicalOrder.was_notified == True)  # noqa: E712
            )
        ).scalar_one()

        critical_pending = (
            await self.session.execute(
                select(func.count())
                .select_from(MedicalOrder)
                .where(
                    MedicalOrder.triage_priority == MedicalPriority.CRITICAL,
                    MedicalOrder.order_state == OrderState.PENDING,
                )
            )
        ).scalar_one()

        async def _grouped(column, enum_cls) -> dict[str, int]:
            result = await self.session.execute(
                select(column, func.count()).group_by(column)
            )
            return {
                self._display_value(
                    enum_cls, k.value if isinstance(k, enum_cls) else str(k)
                ): v
                for k, v in result.all()
            }

        by_state = await _grouped(MedicalOrder.order_state, OrderState)
        by_priority = await _grouped(MedicalOrder.triage_priority, MedicalPriority)
        by_modality = await _grouped(MedicalOrder.modality, Modality)

        latest = (
            await self.session.execute(
                select(MedicalOrder.created_at)
                .order_by(MedicalOrder.created_at.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

        return OrderStats(
            total=total,
            notified=notified,
            critical_pending=critical_pending,
            by_state=by_state,
            by_priority=by_priority,
            by_modality=by_modality,
            latest_created_at=latest,
        )
