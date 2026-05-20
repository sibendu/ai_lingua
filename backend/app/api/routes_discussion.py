from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.discussion import (
    DiscussionAnswerRequest,
    DiscussionAnswerResponse,
    DiscussionStartRequest,
    DiscussionStartResponse,
)
from app.services.discussion_service import DiscussionService
from app.services.llm_service import LLMGenerationError, LLMNotConfiguredError, OllamaTutorService


router = APIRouter(prefix="/discussion", tags=["discussion"])


@router.post("/start", response_model=DiscussionStartResponse)
async def start_discussion(
    request: DiscussionStartRequest,
    session: Session = Depends(get_session),
) -> DiscussionStartResponse:
    tutor = OllamaTutorService()
    try:
        first_reply = await tutor.start_discussion(
            topic=request.topic,
            difficulty=request.difficulty,
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except LLMGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    discussion = DiscussionService(session).create_session(
        family_id=request.family_id,
        child_id=request.child_id,
        topic=request.topic,
        difficulty=request.difficulty,
        first_reply=first_reply,
    )
    return DiscussionStartResponse(
        session_id=discussion.id,
        topic=discussion.topic,
        tutor_reply=first_reply.reply,
    )


@router.post("/answer", response_model=DiscussionAnswerResponse)
async def answer_discussion(
    request: DiscussionAnswerRequest,
    session: Session = Depends(get_session),
) -> DiscussionAnswerResponse:
    service = DiscussionService(session)
    discussion = service.get_session(request.session_id)
    if discussion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found.")
    if discussion.family_id != request.family_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discussion not found.")

    turn_index = service.next_turn_index(discussion.id)
    improvement_attempts = service.recent_improvement_attempts(discussion.id)
    tutor = OllamaTutorService()
    try:
        tutor_reply = await tutor.continue_discussion(
            topic=discussion.topic,
            child_text=request.child_text,
            turn_index=turn_index,
            improvement_attempts=improvement_attempts,
            difficulty=discussion.difficulty,
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except LLMGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    if improvement_attempts >= 2:
        tutor_reply.needs_improvement = False

    turn = service.save_turn(
        discussion=discussion,
        child_text=request.child_text,
        tutor_reply=tutor_reply,
        turn_index=turn_index,
    )
    return DiscussionAnswerResponse(
        session_id=discussion.id,
        turn_id=turn.id,
        topic=discussion.topic,
        child_text=turn.child_text,
        feedback=turn.feedback,
        tutor_reply=turn.tutor_reply,
        needs_improvement=turn.needs_improvement,
        turn_index=turn.turn_index,
    )
