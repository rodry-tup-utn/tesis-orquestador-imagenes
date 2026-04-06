from sqlmodel import Session
from app.systemsettings.model import (
    SystemSettings,
    SystemSettingsUpdate,
)


def get_system_settings(session: Session) -> SystemSettings:
    settings = session.get(SystemSettings, 1)

    if not settings:
        settings = SystemSettings(id=1)
        session.add(settings)
        session.commit()
        session.refresh(settings)

    return settings


def update_system_settings(
    session: Session, settings_data: SystemSettingsUpdate
) -> SystemSettings:

    db_settings = get_system_settings(session)

    # exclude unset para evitar errores en PATCH
    update_data = settings_data.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_settings, key, value)

    session.add(db_settings)
    session.commit()
    session.refresh(db_settings)

    return db_settings
