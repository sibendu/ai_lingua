from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.models import ConversationTurn
from app.db.session import get_session
from app.schemas.conversation import ConversationMessageRequest, ConversationMessageResponse
from app.services.llm_service import LLMGenerationError, LLMNotConfiguredError, OllamaTutorService
from app.services.practice_service import PracticeService


router = APIRouter(prefix="/conversation", tags=["conversation"])


@router.post("/message", response_model=ConversationMessageResponse)
async def send_conversation_message(
    request: ConversationMessageRequest,
    session: Session = Depends(get_session),
) -> ConversationMessageResponse:
    practice_service = PracticeService(session)
    family_id, child_id = practice_service.ensure_local_profile(
        family_id=request.family_id,
        child_id=request.child_id,
    )

    tutor = OllamaTutorService()
    try:
        reply = await tutor.reply_to_child(
            child_text=request.child_text,
            topic=request.topic,
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
        topic=request.topic,
        child_text=request.child_text,
        tutor_reply=reply.reply,
    )
    session.add(turn)
    session.commit()
    session.refresh(turn)

    return ConversationMessageResponse(
        turn_id=turn.id,
        child_text=request.child_text,
        tutor_reply=reply.reply,
        topic=request.topic,
    )
