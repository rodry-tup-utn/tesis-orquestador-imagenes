from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.medical_order.repository import MedicalOrderRepository
from app.modules.triage.repository import TriageRuleRepository
from app.modules.systemsettings.repository import SystemSettingsRepository


class UnitOfWork:

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def __aenter__(self):
        self.orders = MedicalOrderRepository(self.session)
        self.triage_rules = TriageRuleRepository(self.session)
        self.settings = SystemSettingsRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            await self.session.commit()
        else:
            await self.session.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()


def get_uow(session: AsyncSession) -> UnitOfWork:
    return UnitOfWork(session)
