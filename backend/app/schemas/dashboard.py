from datetime import datetime

from pydantic import BaseModel


class RecentAttemptSummary(BaseModel):
    attempt_id: str
    practice_item_id: str
    topic: str | None
    target_text: str
    transcript: str
    score: int
    feedback: str
    created_at: datetime


class WeakTopicSummary(BaseModel):
    topic: str
    attempts: int
    average_score: float


class ChildDashboardResponse(BaseModel):
    family_id: str
    child_id: str
    stars: int
    words_practiced: int
    attempts_today: int
    total_attempts: int
    average_score: float | None
    recent_wins: list[str]


class ParentDashboardResponse(BaseModel):
    family_id: str
    child_id: str
    total_attempts: int
    average_score: float | None
    weak_topics: list[WeakTopicSummary]
    recent_attempts: list[RecentAttemptSummary]
