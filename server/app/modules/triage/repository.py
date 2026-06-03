from sqlmodel import Session, select
from app.core.repository import BaseRepository
from app.modules.triage.model import TriageRule


class TriageRuleRepository(BaseRepository[TriageRule]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, TriageRule)

    def get_enabled(self) -> list[TriageRule]:
        statement = select(TriageRule).where(TriageRule.enabled == True)
        return list(self.session.exec(statement).all())
