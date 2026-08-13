from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.unit_of_work import UnitOfWork
from app.modules.systemsettings.schemas import SystemSettingsRead, SystemSettingsUpdate


class SystemSettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get_or_404(self, uow: UnitOfWork):
        settings = await uow.settings.get_by_id(1)
        if not settings:
            raise HTTPException(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "Configuraciones no cargadas",
            )
        return settings

    async def get(self) -> SystemSettingsRead:
        async with UnitOfWork(self._session) as uow:
            settings = await self._get_or_404(uow)
            return SystemSettingsRead.model_validate(settings)

    async def update(self, data: SystemSettingsUpdate) -> SystemSettingsRead:
        async with UnitOfWork(self._session) as uow:
            settings = await self._get_or_404(uow)
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(settings, key, value)
            uow.session.add(settings)
            await uow.session.flush()
            await uow.session.refresh(settings)
            return SystemSettingsRead.model_validate(settings)
