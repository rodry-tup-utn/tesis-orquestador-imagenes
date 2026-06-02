from sqlmodel import Session
from app.modules.systemsettings.model import SystemSettings


def seed_system_settings(session: Session) -> SystemSettings:
    settings = session.get(SystemSettings, 1)
    if settings:
        return settings
    settings = SystemSettings(id=1)
    session.add(settings)
    session.flush()
    session.refresh(settings)
    return settings
