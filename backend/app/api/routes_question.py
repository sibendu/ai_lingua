from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.models import ConversationTurn
from app.db.session import get_session
from app.schemas.question import QuestionAskRequest, QuestionAskResponse
from app.services.llm_service import LLMGenerationError, LLMNotConfiguredError, OllamaTutorService
from app.services.practice_service import PracticeService


router = APIRouter(prefix="/question", tags=["question"])


@router.post("/ask", response_model=QuestionAskResponse)
async def ask_question(
    request: QuestionAskRequest,
    session: Session = Depends(get_session),
) -> QuestionAskResponse:
    practice_service = PracticeService(session)
    family_id, child_id = practice_service.ensure_local_profile(
        family_id=request.family_id,
        child_id=request.child_id,
    )

    tutor = OllamaTutorService()
    try:
        reply = await tutor.answer_child_question(
            question=request.question,
            difficulty=request.difficulty,
        )
    except LLMNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except LLMGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    turn = ConversationTurn(
        family_id=family_id,
        child_id=child_id,
        topic="my_question",
        child_text=request.question,
        tutor_reply=reply.reply,
    )
    session.add(turn)
    session.commit()
    session.refresh(turn)

    return QuestionAskResponse(
        turn_id=turn.id,
        question=request.question,
        tutor_reply=reply.reply,
    )

