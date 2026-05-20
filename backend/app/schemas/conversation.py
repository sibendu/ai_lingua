from pydantic import BaseModel, Field


class ConversationMessageRequest(BaseModel):
    family_id: str = Field(min_length=1)
    child_id: str | None = None
    child_text: str = Field(min_length=1, max_length=500)
    topic: str | None = Field(default=None, max_length=80)
    difficulty: str = "beginner"


class ConversationMessageResponse(BaseModel):
    turn_id: str
    child_text: str
    tutor_reply: str
    topic: str | None = None
