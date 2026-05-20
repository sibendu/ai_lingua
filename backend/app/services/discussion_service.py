from sqlmodel import Session, select

from app.db.models import DiscussionSession, DiscussionTurn
from app.services.llm_service import DiscussionTutorReply, TutorReply
from app.services.practice_service import LOCAL_CHILD_ID, PracticeService


class DiscussionService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_session(
        self,
        *,
        family_id: str,
        child_id: str | None,
        topic: str,
        difficulty: str,
        first_reply: TutorReply,
    ) -> DiscussionSession:
        resolved_family_id, resolved_child_id = PracticeService(self.session).ensure_local_profile(
            family_id=family_id,
            child_id=child_id or LOCAL_CHILD_ID,
        )
        discussion = DiscussionSession(
            family_id=resolved_family_id,
            child_id=resolved_child_id,
            topic=topic,
            difficulty=difficulty,
        )
        self.session.add(discussion)
        self.session.commit()
        self.session.refresh(discussion)

        self.session.add(
            DiscussionTurn(
                session_id=discussion.id,
                family_id=resolved_family_id,
                child_id=resolved_child_id,
                turn_index=0,
                child_text="",
                feedback="",
                tutor_reply=first_reply.reply,
                needs_improvement=False,
            )
        )
        self.session.commit()
        return discussion

    def get_session(self, session_id: str) -> DiscussionSession | None:
        return self.session.get(DiscussionSession, session_id)

    def next_turn_index(self, session_id: str) -> int:
        latest = self.session.exec(
            select(DiscussionTurn)
            .where(DiscussionTurn.session_id == session_id)
            .order_by(DiscussionTurn.turn_index.desc())
        ).first()
        return 1 if latest is None else latest.turn_index + 1

    def recent_improvement_attempts(self, session_id: str) -> int:
        turns = list(
            self.session.exec(
                select(DiscussionTurn)
                .where(DiscussionTurn.session_id == session_id)
                .order_by(DiscussionTurn.turn_index.desc())
            )
        )
        count = 0
        for turn in turns:
            if not turn.child_text:
                continue
            if not turn.needs_improvement:
                break
            count += 1
        return count

    def save_turn(
        self,
        *,
        discussion: DiscussionSession,
        child_text: str,
        tutor_reply: DiscussionTutorReply,
        turn_index: int,
    ) -> DiscussionTurn:
        turn = DiscussionTurn(
            session_id=discussion.id,
            family_id=discussion.family_id,
            child_id=discussion.child_id,
            turn_index=turn_index,
            child_text=child_text,
            feedback=tutor_reply.feedback,
            tutor_reply=tutor_reply.reply,
            needs_improvement=tutor_reply.needs_improvement,
        )
        self.session.add(turn)
        self.session.commit()
        self.session.refresh(turn)
        return turn
