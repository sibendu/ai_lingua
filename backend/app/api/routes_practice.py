from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.db.models import Attempt
from app.db.session import get_session
from app.schemas.practice import (
    PracticeAttemptRequest,
    PracticeAttemptResponse,
    PracticeNextResponse,
)
from app.services.practice_service import PracticeService
from app.services.scoring_service import ScoringService


router = APIRouter(prefix="/practice", tags=["practice"])


@router.get("/next", response_model=PracticeNextResponse)
def get_next_practice_item(
    mode: str = Query(default="listen_repeat"),
    topic: str | None = Query(default=None),
    difficulty: str = Query(default="beginner"),
    session: Session = Depends(get_session),
) -> PracticeNextResponse:
    service = PracticeService(session)
    try:
        item = service.get_next_item(mode=mode, topic=topic, difficulty=difficulty)
    except IndexError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching French practice item found.",
        ) from exc

    service.ensure_practice_item(item)
    return PracticeNextResponse(item=item)


@router.post("/attempt", response_model=PracticeAttemptResponse)
def submit_practice_attempt(
    request: PracticeAttemptRequest,
    session: Session = Depends(get_session),
) -> PracticeAttemptResponse:
    service = PracticeService(session)
    family_id, child_id = service.ensure_local_profile(
        family_id=request.family_id,
        child_id=request.child_id,
    )

    lesson_item = service.get_lesson_item(request.practice_item_id)
    if lesson_item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Practice item not found.",
        )

    practice_item = service.ensure_practice_item(lesson_item)
    practice_session = service.create_session(
        family_id=family_id,
        child_id=child_id,
        mode=request.mode,
    )
    score = ScoringService().score(request.target_text, request.transcript)

    attempt = Attempt(
        family_id=family_id,
        child_id=child_id,
        session_id=practice_session.id,
        practice_item_id=practice_item.id,
        target_text=request.target_text,
        transcript=request.transcript,
        score=score.score,
        feedback=score.feedback,
        audio_asset_id=request.audio_asset_id,
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)

    return PracticeAttemptResponse(
        attempt_id=attempt.id,
        session_id=practice_session.id,
        practice_item_id=practice_item.id,
        target_text=request.target_text,
        transcript=request.transcript,
        score=score,
    )
