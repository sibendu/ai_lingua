from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db.models import AudioAsset
from app.db.session import get_session
from app.schemas.tts import TTSRequest, TTSResponse
from app.services.tts_service import (
    PiperTTSService,
    TTSGenerationError,
    TTSNotConfiguredError,
)


router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("", response_model=TTSResponse)
def synthesize_tts(
    request: TTSRequest,
    session: Session = Depends(get_session),
) -> TTSResponse:
    if request.language != "fr":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The MVP TTS endpoint supports French only.",
        )

    try:
        location = PiperTTSService().synthesize_french(request.text)
    except TTSNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except TTSGenerationError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    asset = AudioAsset(
        family_id=request.family_id,
        child_id=request.child_id,
        kind="tts",
        storage_uri=location.storage_uri,
        content_type=location.content_type,
    )
    session.add(asset)
    session.commit()
    session.refresh(asset)

    return TTSResponse(
        audio_asset_id=asset.id,
        audio_url=location.public_url,
        content_type=location.content_type,
        text=request.text,
        language=request.language,
    )
