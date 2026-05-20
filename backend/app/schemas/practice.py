from pydantic import BaseModel, Field

from app.schemas.lessons import LessonItem


class PracticeNextResponse(BaseModel):
    item: LessonItem


class PracticeAttemptRequest(BaseModel):
    family_id: str = Field(min_length=1)
    child_id: str | None = None
    practice_item_id: str = Field(min_length=1)
    target_text: str = Field(min_length=1)
    transcript: str = Field(min_length=0)
    mode: str = "listen_repeat"
    audio_asset_id: str | None = None


class PracticeScore(BaseModel):
    score: int
    label: str
    feedback: str
    missing_words: list[str]
    extra_words: list[str]


class PracticeAttemptResponse(BaseModel):
    attempt_id: str
    session_id: str
    practice_item_id: str
    target_text: str
    transcript: str
    score: PracticeScore
