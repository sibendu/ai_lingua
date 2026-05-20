from pydantic import BaseModel


class STTSegment(BaseModel):
    start: float
    end: float
    text: str


class STTResponse(BaseModel):
    audio_asset_id: str
    transcript: str
    language: str
    duration_seconds: float | None
    segments: list[STTSegment]
