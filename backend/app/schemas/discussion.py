from pydantic import BaseModel, Field


class DiscussionStartRequest(BaseModel):
    family_id: str = Field(min_length=1)
    child_id: str | None = None
    topic: str = Field(min_length=1, max_length=120)
    difficulty: str = "beginner"


class DiscussionStartResponse(BaseModel):
    session_id: str
    topic: str
    tutor_reply: str


class DiscussionAnswerRequest(BaseModel):
    family_id: str = Field(min_length=1)
    child_id: str | None = None
    session_id: str = Field(min_length=1)
    child_text: str = Field(min_length=1, max_length=500)


class DiscussionAnswerResponse(BaseModel):
    session_id: str
    turn_id: str
    topic: str
    child_text: str
    feedback: str
    tutor_reply: str
    needs_improvement: bool
    turn_index: int
