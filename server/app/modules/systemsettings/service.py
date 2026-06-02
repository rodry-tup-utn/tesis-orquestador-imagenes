from sqlmodel import Session
from fastapi import HTTPException, status
from app.core.unit_of_work import UnitOfWork
from app.modules.systemsettings.schemas import SystemSettingsRead, SystemSettingsUpdate


class SystemSettingsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def _get_or_404(self, uow: UnitOfWork):
        settings = uow.settings.get_by_id(1)
        if not settings:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Configuraciones no cargadas",
            )
        return settings

    def get(self) -> SystemSettingsRead:
        with UnitOfWork(self._session) as uow:
            settings = self._get_or_404(uow)
            return SystemSettingsRead.model_validate(settings)

    def update(self, data: SystemSettingsUpdate) -> SystemSettingsRead:
        with UnitOfWork(self._session) as uow:
            settings = self._get_or_404(uow)
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(settings, key, value)
            uow.session.add(settings)
            uow.session.flush()
            uow.session.refresh(settings)
            return SystemSettingsRead.model_validate(settings)
