from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.systemsettings.model import SystemSettings


async def seed_system_settings(session: AsyncSession) -> SystemSettings:
    settings = await session.get(SystemSettings, 1)
    if settings:
        return settings
    settings = SystemSettings(id=1)
    session.add(settings)
    await session.flush()
    await session.refresh(settings)
    return settings
