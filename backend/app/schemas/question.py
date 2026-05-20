from pydantic import BaseModel, Field


class QuestionAskRequest(BaseModel):
    family_id: str = Field(min_length=1)
    child_id: str | None = None
    question: str = Field(min_length=1, max_length=500)
    difficulty: str = "beginner"


class QuestionAskResponse(BaseModel):
    turn_id: str
    question: str
    tutor_reply: str

