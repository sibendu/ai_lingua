from sqlmodel import Session, select

from app.db.models import Settings
from app.schemas.settings import SettingsUpdateRequest
from app.services.practice_service import LOCAL_CHILD_ID, LOCAL_FAMILY_ID, PracticeService


class SettingsService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_or_create(
        self,
        *,
        family_id: str = LOCAL_FAMILY_ID,
        child_id: str = LOCAL_CHILD_ID,
    ) -> Settings:
        PracticeService(self.session).ensure_local_profile(
            family_id=family_id,
            child_id=child_id,
        )
        settings = self.session.exec(
            select(Settings).where(
                Settings.family_id == family_id,
                Settings.child_id == child_id,
            )
        ).first()
        if settings is not None:
            return settings

        settings = Settings(
            family_id=family_id,
            child_id=child_id,
            difficulty="beginner",
            daily_goal_minutes=10,
            preferred_topics=[],
        )
        self.session.add(settings)
        self.session.commit()
        self.session.refresh(settings)
        return settings

    def update(self, request: SettingsUpdateRequest) -> Settings:
        family_id = request.family_id
        child_id = request.child_id or LOCAL_CHILD_ID
        settings = self.get_or_create(family_id=family_id, child_id=child_id)

        if request.difficulty is not None:
            settings.difficulty = request.difficulty
        if request.daily_goal_minutes is not None:
            settings.daily_goal_minutes = request.daily_goal_minutes
        if request.preferred_topics is not None:
            settings.preferred_topics = request.preferred_topics

        self.session.add(settings)
        self.session.commit()
        self.session.refresh(settings)
        return settings
