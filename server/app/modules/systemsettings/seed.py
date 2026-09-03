from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.systemsettings.model import SystemSettings
from app.modules.triage.configuration import load_triage_config


async def seed_system_settings(session: AsyncSession) -> SystemSettings:
    settings = await session.get(SystemSettings, 1)
    if settings:
        return settings
    thresholds = load_triage_config()["thresholds"]
    settings = SystemSettings(
        id=1,
        triage_critical_threshold=thresholds["critical"],
        triage_urgent_threshold=thresholds["urgent"],
        triage_priority_threshold=thresholds["priority"],
    )
    session.add(settings)
    await session.flush()
    await session.refresh(settings)
    return settings
