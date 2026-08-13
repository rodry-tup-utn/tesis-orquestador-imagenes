from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.core.repository import BaseRepository
from app.modules.triage.model import TriageRule


class TriageRuleRepository(BaseRepository[TriageRule]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TriageRule)

    async def get_enabled(self) -> list[TriageRule]:
        statement = select(TriageRule).where(TriageRule.enabled == True)
        result = await self.session.execute(statement)
        return list(result.scalars().all())
