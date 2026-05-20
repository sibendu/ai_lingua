from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import Column, JSON
from sqlmodel import Field, SQLModel


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class Family(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=utc_now)


class User(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    name: str
    role: str = Field(index=True, description="Expected values: child or parent")
    created_at: datetime = Field(default_factory=utc_now)


class ChildProfile(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    display_name: str
    preferred_language: str = Field(default="fr", index=True)
    created_at: datetime = Field(default_factory=utc_now)


class PracticeItem(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    language: str = Field(default="fr", index=True)
    mode: str = Field(index=True)
    topic: str = Field(index=True)
    difficulty: str = Field(default="beginner", index=True)
    text_fr: str
    text_en: str
    expected_keywords: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )


class PracticeSession(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    child_id: str = Field(foreign_key="childprofile.id", index=True)
    mode: str = Field(index=True)
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None


class Attempt(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    child_id: str = Field(foreign_key="childprofile.id", index=True)
    session_id: str = Field(foreign_key="practicesession.id", index=True)
    practice_item_id: str = Field(foreign_key="practiceitem.id", index=True)
    target_text: str
    transcript: str
    score: int
    feedback: str
    audio_asset_id: str | None = Field(default=None, foreign_key="audioasset.id")
    created_at: datetime = Field(default_factory=utc_now)


class Settings(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    child_id: str = Field(foreign_key="childprofile.id", index=True)
    difficulty: str = Field(default="beginner")
    daily_goal_minutes: int = Field(default=10, ge=1)
    preferred_topics: list[str] = Field(
        default_factory=list,
        sa_column=Column(JSON, nullable=False),
    )


class AudioAsset(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    child_id: str | None = Field(default=None, foreign_key="childprofile.id", index=True)
    kind: str = Field(index=True, description="Expected values: upload, tts, or system_prompt")
    storage_uri: str
    content_type: str
    created_at: datetime = Field(default_factory=utc_now)


class ConversationTurn(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    child_id: str = Field(foreign_key="childprofile.id", index=True)
    topic: str | None = Field(default=None, index=True)
    child_text: str
    tutor_reply: str
    created_at: datetime = Field(default_factory=utc_now)


class DiscussionSession(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    child_id: str = Field(foreign_key="childprofile.id", index=True)
    topic: str = Field(index=True)
    difficulty: str = Field(default="beginner")
    started_at: datetime = Field(default_factory=utc_now)
    ended_at: datetime | None = None


class DiscussionTurn(SQLModel, table=True):
    id: str = Field(default_factory=new_id, primary_key=True)
    session_id: str = Field(foreign_key="discussionsession.id", index=True)
    family_id: str = Field(foreign_key="family.id", index=True)
    child_id: str = Field(foreign_key="childprofile.id", index=True)
    turn_index: int
    child_text: str
    tutor_reply: str
    feedback: str
    needs_improvement: bool = Field(default=False)
    created_at: datetime = Field(default_factory=utc_now)
