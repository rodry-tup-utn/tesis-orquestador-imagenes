from sqlmodel import Session
from app.modules.medical_order.repository import MedicalOrderRepository
from app.modules.triage.repository import TriageRuleRepository
from app.modules.systemsettings.repository import SystemSettingsRepository


class UnitOfWork:

    def __init__(self, session: Session) -> None:
        self.session = session

    def __enter__(self):
        self.orders = MedicalOrderRepository(self.session)
        self.triage_rules = TriageRuleRepository(self.session)
        self.settings = SystemSettingsRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is None:
            self.session.commit()  # type: ignore
        else:
            self.session.rollback()  # type: ignore
        self.session.close()  # type: ignore

    def commit(self) -> None:
        self.session.commit()  # type: ignore

    def rollback(self) -> None:
        self.session.rollback()  # type: ignore


def get_uow(session: Session) -> UnitOfWork:
    return UnitOfWork(session)
