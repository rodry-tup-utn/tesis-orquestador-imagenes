from fastapi import APIRouter, Depends
from app.systemsettings.service import get_system_settings, update_system_settings
from sqlmodel import Session
from app.database import get_session
from app.systemsettings.model import SystemSettingsRead, SystemSettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


@router.get("", response_model=SystemSettingsRead)
def get_settings(session: Session = Depends(get_session)):
    return get_system_settings(session)


@router.patch("", response_model=SystemSettingsRead)
def update_settings(
    data: SystemSettingsUpdate, session: Session = Depends(get_session)
):
    return update_system_settings(session, data)
