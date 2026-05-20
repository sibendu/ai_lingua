from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500)
    family_id: str = Field(
        min_length=1,
        description="Family scope for the generated audio asset.",
    )
    child_id: str | None = Field(
        default=None,
        description="Optional child scope for prompt audio.",
    )
    language: str = Field(default="fr")


class TTSResponse(BaseModel):
    audio_asset_id: str
    audio_url: str
    content_type: str = "audio/wav"
    text: str
    language: str
