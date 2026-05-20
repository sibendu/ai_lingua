from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.dashboard import ChildDashboardResponse, ParentDashboardResponse
from app.services.practice_service import LOCAL_FAMILY_ID, PracticeService
from app.services.progress_service import ProgressService


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/child/{child_id}", response_model=ChildDashboardResponse)
def get_child_dashboard(
    child_id: str,
    family_id: str = Query(default=LOCAL_FAMILY_ID),
    session: Session = Depends(get_session),
) -> ChildDashboardResponse:
    PracticeService(session).ensure_local_profile(family_id=family_id, child_id=child_id)
    return ProgressService(session).child_dashboard(family_id=family_id, child_id=child_id)


@router.get("/parent/{child_id}", response_model=ParentDashboardResponse)
def get_parent_dashboard(
    child_id: str,
    family_id: str = Query(default=LOCAL_FAMILY_ID),
    session: Session = Depends(get_session),
) -> ParentDashboardResponse:
    PracticeService(session).ensure_local_profile(family_id=family_id, child_id=child_id)
    return ProgressService(session).parent_dashboard(family_id=family_id, child_id=child_id)
