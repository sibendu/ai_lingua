from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.settings import SettingsResponse, SettingsUpdateRequest
from app.services.practice_service import LOCAL_FAMILY_ID
from app.services.settings_service import SettingsService


router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/{child_id}", response_model=SettingsResponse)
def get_settings(
    child_id: str,
    family_id: str = Query(default=LOCAL_FAMILY_ID),
    session: Session = Depends(get_session),
) -> SettingsResponse:
    settings = SettingsService(session).get_or_create(
        family_id=family_id,
        child_id=child_id,
    )
    return SettingsResponse.model_validate(settings, from_attributes=True)


@router.patch("", response_model=SettingsResponse)
def update_settings(
    request: SettingsUpdateRequest,
    session: Session = Depends(get_session),
) -> SettingsResponse:
    settings = SettingsService(session).update(request)
    return SettingsResponse.model_validate(settings, from_attributes=True)
