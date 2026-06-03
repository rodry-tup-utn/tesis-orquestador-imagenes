from sqlmodel import Session
from app.core.repository import BaseRepository
from app.modules.systemsettings.model import SystemSettings


class SystemSettingsRepository(BaseRepository[SystemSettings]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, SystemSettings)
