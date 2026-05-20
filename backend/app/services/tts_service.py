import hashlib
import unicodedata
import subprocess
from pathlib import Path

from app.core.config import get_settings
from app.services.storage_service import LocalAudioStorage, StoredAudioLocation


class TTSNotConfiguredError(RuntimeError):
    pass


class TTSGenerationError(RuntimeError):
    pass


class PiperTTSService:
    def __init__(
        self,
        *,
        storage: LocalAudioStorage | None = None,
        piper_bin_path: str | None = None,
        piper_voice_path: str | None = None,
        timeout_seconds: int = 60,
    ) -> None:
        settings = get_settings()
        self.storage = storage or LocalAudioStorage()
        self.piper_bin_path = (
            piper_bin_path if piper_bin_path is not None else settings.piper_bin_path
        )
        self.piper_voice_path = (
            piper_voice_path if piper_voice_path is not None else settings.piper_voice_path
        )
        self.timeout_seconds = timeout_seconds

    @property
    def is_configured(self) -> bool:
        return bool(self.piper_bin_path and self.piper_voice_path)

    def synthesize_french(self, text: str) -> StoredAudioLocation:
        if not self.is_configured:
            raise TTSNotConfiguredError(
                "Piper is not configured. Set PIPER_BIN_PATH and PIPER_VOICE_PATH."
            )

        piper_bin = Path(str(self.piper_bin_path))
        voice_path = Path(str(self.piper_voice_path))

        if not piper_bin.exists():
            raise TTSNotConfiguredError(f"Piper binary not found: {piper_bin}")
        if not voice_path.exists():
            raise TTSNotConfiguredError(f"Piper voice not found: {voice_path}")

        spoken_text = sanitize_tts_text(text)
        location = self.storage.cached_wav(
            kind="tts",
            cache_key=self._cache_key(text=spoken_text, voice_path=voice_path),
        )
        if location.file_path.exists() and location.file_path.stat().st_size > 0:
            return location

        command = [
            str(piper_bin),
            "--model",
            str(voice_path),
            "--output_file",
            str(location.file_path),
        ]

        result = subprocess.run(
            command,
            input=spoken_text.encode("utf-8"),
            capture_output=True,
            timeout=self.timeout_seconds,
            check=False,
        )

        if result.returncode != 0:
            raise TTSGenerationError(result.stderr.strip() or "Piper generation failed")

        if not location.file_path.exists() or location.file_path.stat().st_size == 0:
            raise TTSGenerationError("Piper did not create a WAV file")

        return location

    def _cache_key(self, *, text: str, voice_path: Path) -> str:
        digest = hashlib.sha256(
            f"{voice_path.resolve()}|{text.strip()}".encode("utf-8")
        ).hexdigest()
        return digest[:32]


def sanitize_tts_text(text: str) -> str:
    cleaned = "".join(
        character
        for character in text
        if unicodedata.category(character)[0] not in {"C", "S"}
    )
    return " ".join(cleaned.split()).strip() or "Bonjour."
