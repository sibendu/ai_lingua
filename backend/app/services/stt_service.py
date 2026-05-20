from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from threading import Lock

from app.core.config import get_settings


class STTNotConfiguredError(RuntimeError):
    pass


class STTGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class TranscriptionSegment:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    language: str
    duration_seconds: float | None
    segments: list[TranscriptionSegment]


class WhisperModelLike(Protocol):
    def transcribe(self, audio: str, **kwargs):
        pass


_MODEL_CACHE: dict[tuple[str, str, str], WhisperModelLike] = {}
_MODEL_CACHE_LOCK = Lock()


class FasterWhisperSTTService:
    def __init__(
        self,
        *,
        model_name: str | None = None,
        device: str | None = None,
        compute_type: str | None = None,
        beam_size: int | None = None,
        vad_filter: bool | None = None,
        model: WhisperModelLike | None = None,
    ) -> None:
        settings = get_settings()
        self.model_name = model_name if model_name is not None else settings.whisper_model
        self.device = device if device is not None else settings.whisper_device
        self.compute_type = compute_type if compute_type is not None else settings.whisper_compute_type
        self.beam_size = beam_size if beam_size is not None else settings.whisper_beam_size
        self.vad_filter = vad_filter if vad_filter is not None else settings.whisper_vad_filter
        self._model = model

    @property
    def is_configured(self) -> bool:
        return bool(self.model_name)

    def transcribe_french(self, audio_path: Path) -> TranscriptionResult:
        if not self.is_configured:
            raise STTNotConfiguredError("Whisper is not configured. Set WHISPER_MODEL.")
        if not audio_path.exists():
            raise STTGenerationError(f"Audio file not found: {audio_path}")

        try:
            model = self._model or self._load_model()
            segments_iter, info = model.transcribe(
                str(audio_path),
                language="fr",
                task="transcribe",
                beam_size=self.beam_size,
                vad_filter=self.vad_filter,
            )
            segments = [
                TranscriptionSegment(
                    start=float(segment.start),
                    end=float(segment.end),
                    text=segment.text.strip(),
                )
                for segment in segments_iter
            ]
        except STTNotConfiguredError:
            raise
        except Exception as exc:  # pragma: no cover - defensive wrapper around model runtime
            raise STTGenerationError(str(exc)) from exc

        transcript = " ".join(segment.text for segment in segments).strip()
        return TranscriptionResult(
            transcript=transcript,
            language=getattr(info, "language", "fr") or "fr",
            duration_seconds=getattr(info, "duration", None),
            segments=segments,
        )

    def _load_model(self) -> WhisperModelLike:
        if self.model_name is None:
            raise STTNotConfiguredError("Whisper is not configured. Set WHISPER_MODEL.")

        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - covered by installation check
            raise STTNotConfiguredError(
                "faster-whisper is not installed. Run pip install -e \".[dev]\"."
            ) from exc

        kwargs: dict[str, str] = {}
        if self.device and self.device != "auto":
            kwargs["device"] = self.device
        if self.compute_type and self.compute_type != "default":
            kwargs["compute_type"] = self.compute_type

        cache_key = (
            self.model_name,
            self.device or "auto",
            self.compute_type or "default",
        )
        if self._model is not None:
            return self._model

        with _MODEL_CACHE_LOCK:
            cached_model = _MODEL_CACHE.get(cache_key)
            if cached_model is not None:
                self._model = cached_model
                return cached_model

            self._model = WhisperModel(self.model_name, **kwargs)
            _MODEL_CACHE[cache_key] = self._model
        return self._model
