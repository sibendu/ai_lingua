from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    app_name: str = "AI Lingua API"
    app_env: str = "local"
    database_url: str = "sqlite:///./ai_lingua.db"
    public_base_url: str = "http://localhost:8000"
    frontend_cors_origins: str = "http://localhost:3000"

    storage_backend: str = "local"
    local_audio_storage_path: str = "./storage/audio"

    ollama_base_url: str | None = None
    ollama_model: str | None = None
    ollama_auth_token: str | None = None
    whisper_model: str | None = None
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    whisper_beam_size: int = 1
    whisper_vad_filter: bool = False
    max_audio_upload_mb: int = 25
    piper_bin_path: str | None = None
    piper_voice_path: str | None = None

    lesson_dir: Path = Field(default=BACKEND_DIR / "app" / "data" / "lessons")

    model_config = SettingsConfigDict(
        env_file=REPO_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def frontend_cors_origin_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.frontend_cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def local_audio_storage_root(self) -> Path:
        path = Path(self.local_audio_storage_path)
        return path if path.is_absolute() else BACKEND_DIR / path


@lru_cache
def get_settings() -> Settings:
    return Settings()
