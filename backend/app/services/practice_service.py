from sqlmodel import Session, select

from app.db.models import ChildProfile, Family, PracticeItem, PracticeSession, User
from app.schemas.lessons import LessonItem
from app.services.lesson_service import LessonService


LOCAL_FAMILY_ID = "local-family"
LOCAL_CHILD_ID = "local-child"


class PracticeService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_next_item(
        self,
        *,
        mode: str = "listen_repeat",
        topic: str | None = None,
        difficulty: str = "beginner",
    ) -> LessonItem:
        items = [
            item
            for pack in LessonService().list_packs(language="fr")
            for item in pack.items
            if item.difficulty == difficulty
        ]
        matching = [
            item
            for item in items
            if item.mode == mode and (topic is None or item.topic == topic)
        ]
        return (matching or items)[0]

    def get_lesson_item(self, item_id: str) -> LessonItem | None:
        for pack in LessonService().list_packs(language="fr"):
            for item in pack.items:
                if item.id == item_id:
                    return item
        return None

    def ensure_local_profile(
        self,
        family_id: str = LOCAL_FAMILY_ID,
        child_id: str | None = None,
    ) -> tuple[str, str]:
        resolved_child_id = child_id or LOCAL_CHILD_ID

        family = self.session.get(Family, family_id)
        if family is None:
            self.session.add(Family(id=family_id, name="Local Family"))

        child = self.session.get(ChildProfile, resolved_child_id)
        if child is None:
            self.session.add(
                ChildProfile(
                    id=resolved_child_id,
                    family_id=family_id,
                    display_name="Local Learner",
                    preferred_language="fr",
                )
            )

        parent_user = self.session.exec(
            select(User).where(User.family_id == family_id, User.role == "parent")
        ).first()
        if parent_user is None:
            self.session.add(User(family_id=family_id, name="Local Parent", role="parent"))

        child_user = self.session.exec(
            select(User).where(User.family_id == family_id, User.role == "child")
        ).first()
        if child_user is None:
            self.session.add(User(family_id=family_id, name="Local Learner", role="child"))

        self.session.commit()
        return family_id, resolved_child_id

    def ensure_practice_item(self, item: LessonItem) -> PracticeItem:
        existing = self.session.get(PracticeItem, item.id)
        if existing is not None:
            return existing

        practice_item = PracticeItem(
            id=item.id,
            language=item.language,
            mode=item.mode,
            topic=item.topic,
            difficulty=item.difficulty,
            text_fr=item.text_fr,
            text_en=item.text_en,
            expected_keywords=item.expected_keywords,
        )
        self.session.add(practice_item)
        self.session.commit()
        self.session.refresh(practice_item)
        return practice_item

    def create_session(self, *, family_id: str, child_id: str, mode: str) -> PracticeSession:
        practice_session = PracticeSession(
            family_id=family_id,
            child_id=child_id,
            mode=mode,
        )
        self.session.add(practice_session)
        self.session.commit()
        self.session.refresh(practice_session)
        return practice_session
