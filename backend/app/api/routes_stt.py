from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlmodel import Session

from app.core.config import get_settings
from app.db.models import AudioAsset
from app.db.session import get_session
from app.schemas.stt import STTResponse, STTSegment
from app.services.storage_service import LocalAudioStorage
from app.services.stt_service import (
    FasterWhisperSTTService,
    STTGenerationError,
    STTNotConfiguredError,
)


router = APIRouter(prefix="/stt", tags=["stt"])

SUPPORTED_AUDIO_TYPES = {
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp4",
    "audio/webm",
    "audio/ogg",
    "audio/flac",
}


@router.post("/transcribe", response_model=STTResponse)
async def transcribe_audio(
    family_id: str = Form(..., min_length=1),
    child_id: str | None = Form(default=None),
    language: str = Form(default="fr"),
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> STTResponse:
    if language != "fr":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The MVP STT endpoint supports French only.",
        )

    stt_service = FasterWhisperSTTService()
    if not stt_service.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Whisper is not configured. Set WHISPER_MODEL.",
        )

    content_type = normalize_content_type(file.content_type)
    if content_type not in SUPPORTED_AUDIO_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported audio content type: {content_type}",
        )

    content = await file.read()
    max_bytes = get_settings().max_audio_upload_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio upload exceeds {get_settings().max_audio_upload_mb} MB.",
        )

    location = LocalAudioStorage().save_audio_bytes(
        content=content,
        kind="upload",
        original_filename=file.filename,
        content_type=content_type,
    )

    asset = AudioAsset(
        family_id=family_id,
        child_id=child_id,
        kind="upload",
        storage_uri=location.storage_uri,
        content_type=location.content_type,
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)

    try:
        result = stt_service.transcribe_french(location.file_path)
    except STTNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except STTGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    return STTResponse(
        audio_asset_id=asset.id,
        transcript=result.transcript,
        language=result.language,
        duration_seconds=result.duration_seconds,
        segments=[
            STTSegment(start=segment.start, end=segment.end, text=segment.text)
            for segment in result.segments
        ],
    )


def normalize_content_type(content_type: str | None) -> str:
    return (content_type or "application/octet-stream").split(";", 1)[0].strip().lower()
