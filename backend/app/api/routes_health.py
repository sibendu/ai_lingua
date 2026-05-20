from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlmodel import Session

from app.core.config import get_settings
from app.db.session import get_session
from app.schemas.health import DependencyStatus, HealthResponse, ModelProviderStatus
from app.services.lesson_service import LessonService
from app.services.llm_service import OllamaTutorService
from app.services.stt_service import FasterWhisperSTTService
from app.services.tts_service import PiperTTSService


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(session: Session = Depends(get_session)) -> HealthResponse:
    settings = get_settings()

    dependencies: dict[str, DependencyStatus] = {}

    try:
        session.exec(text("SELECT 1")).one()
        dependencies["database"] = DependencyStatus(status="ok")
    except Exception as exc:  # pragma: no cover - defensive health reporting
        dependencies["database"] = DependencyStatus(status="error", detail=str(exc))

    lesson_count = len(LessonService().list_packs(language="fr"))
    dependencies["french_lessons"] = DependencyStatus(
        status="ok" if lesson_count else "missing",
        detail=f"{lesson_count} lesson pack(s)",
    )

    tts_service = PiperTTSService()
    stt_service = FasterWhisperSTTService()
    tutor_service = OllamaTutorService()

    return HealthResponse(
        status="ok" if all(item.status == "ok" for item in dependencies.values()) else "degraded",
        app=settings.app_name,
        environment=settings.app_env,
        dependencies=dependencies,
        model_providers={
            "ollama": ModelProviderStatus(
                configured=bool(settings.ollama_base_url and settings.ollama_model),
                enabled=tutor_service.is_configured,
            ),
            "whisper": ModelProviderStatus(
                configured=bool(settings.whisper_model),
                enabled=stt_service.is_configured,
            ),
            "piper": ModelProviderStatus(
                configured=bool(settings.piper_bin_path and settings.piper_voice_path),
                enabled=tts_service.is_configured,
            ),
        },
    )
