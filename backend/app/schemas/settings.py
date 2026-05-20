from pydantic import BaseModel, Field


class SettingsResponse(BaseModel):
    id: str
    family_id: str
    child_id: str
    difficulty: str
    daily_goal_minutes: int
    preferred_topics: list[str]


class SettingsUpdateRequest(BaseModel):
    family_id: str = Field(min_length=1)
    child_id: str | None = None
    difficulty: str | None = None
    daily_goal_minutes: int | None = Field(default=None, ge=1, le=120)
    preferred_topics: list[str] | None = None
