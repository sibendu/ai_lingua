from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.core.config import get_settings


@dataclass(frozen=True)
class StoredAudioLocation:
    file_path: Path
    storage_uri: str
    public_url: str
    content_type: str


class LocalAudioStorage:
    def __init__(self, root: Path | None = None, public_prefix: str = "/audio") -> None:
        settings = get_settings()
        self.root = root or settings.local_audio_storage_root
        self.public_prefix = public_prefix.rstrip("/")

    def allocate_wav(self, kind: str) -> StoredAudioLocation:
        return self.allocate_audio(kind=kind, extension=".wav", content_type="audio/wav")

    def cached_wav(self, *, kind: str, cache_key: str) -> StoredAudioLocation:
        if not kind.replace("_", "").isalnum():
            raise ValueError("Audio kind must be alphanumeric or underscore")
        if not cache_key.replace("-", "").replace("_", "").isalnum():
            raise ValueError("Audio cache key must be alphanumeric, dash, or underscore")

        directory = self.root / kind
        directory.mkdir(parents=True, exist_ok=True)
        file_name = f"{cache_key}.wav"
        file_path = directory / file_name

        return StoredAudioLocation(
            file_path=file_path,
            storage_uri=f"local://{kind}/{file_name}",
            public_url=f"{self.public_prefix}/{kind}/{file_name}",
            content_type="audio/wav",
        )

    def allocate_audio(
        self,
        *,
        kind: str,
        extension: str,
        content_type: str,
    ) -> StoredAudioLocation:
        if not kind.replace("_", "").isalnum():
            raise ValueError("Audio kind must be alphanumeric or underscore")
        if not extension.startswith(".") or "/" in extension or "\\" in extension:
            raise ValueError("Audio extension must be a safe file extension")

        file_name = f"{uuid4()}{extension.lower()}"
        directory = self.root / kind
        directory.mkdir(parents=True, exist_ok=True)
        file_path = directory / file_name

        return StoredAudioLocation(
            file_path=file_path,
            storage_uri=f"local://{kind}/{file_name}",
            public_url=f"{self.public_prefix}/{kind}/{file_name}",
            content_type=content_type,
        )

    def save_audio_bytes(
        self,
        *,
        content: bytes,
        kind: str,
        original_filename: str | None,
        content_type: str,
    ) -> StoredAudioLocation:
        extension = self._safe_extension(original_filename, content_type)
        location = self.allocate_audio(
            kind=kind,
            extension=extension,
            content_type=content_type,
        )
        location.file_path.write_bytes(content)
        return location

    def _safe_extension(self, filename: str | None, content_type: str) -> str:
        normalized_content_type = content_type.split(";", 1)[0].strip().lower()
        suffix = Path(filename or "").suffix.lower()
        allowed_suffixes = {".wav", ".mp3", ".mp4", ".m4a", ".webm", ".ogg", ".flac"}
        if suffix in allowed_suffixes:
            return suffix

        return {
            "audio/wav": ".wav",
            "audio/x-wav": ".wav",
            "audio/mpeg": ".mp3",
            "audio/mp4": ".m4a",
            "audio/webm": ".webm",
            "audio/ogg": ".ogg",
            "audio/flac": ".flac",
        }.get(normalized_content_type, ".bin")
