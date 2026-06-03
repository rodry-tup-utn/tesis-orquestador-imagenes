from fastapi import APIRouter, Depends
from sqlmodel import Session
from app.core.database import get_session
from app.modules.systemsettings.schemas import SystemSettingsRead, SystemSettingsUpdate
from app.modules.systemsettings.service import SystemSettingsService

router = APIRouter(prefix="/settings", tags=["Settings"])


def get_settings_service(
    session: Session = Depends(get_session),
) -> SystemSettingsService:
    return SystemSettingsService(session)


@router.get("", response_model=SystemSettingsRead)
def get_settings(svc: SystemSettingsService = Depends(get_settings_service)):
    return svc.get()


@router.patch("", response_model=SystemSettingsRead)
def update_settings(
    data: SystemSettingsUpdate,
    svc: SystemSettingsService = Depends(get_settings_service),
):
    return svc.update(data)
