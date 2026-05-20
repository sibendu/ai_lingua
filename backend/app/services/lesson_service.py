import json
from pathlib import Path

from app.core.config import get_settings
from app.schemas.lessons import LessonPack


class LessonService:
    def __init__(self, lesson_dir: Path | None = None) -> None:
        settings = get_settings()
        self.lesson_dir = lesson_dir or settings.lesson_dir

    def list_packs(self, language: str = "fr") -> list[LessonPack]:
        packs = [self._load_pack(path) for path in sorted(self.lesson_dir.glob("*.json"))]
        return [pack for pack in packs if pack.language == language]

    def get_pack(self, pack_id: str) -> LessonPack | None:
        for path in sorted(self.lesson_dir.glob("*.json")):
            pack = self._load_pack(path)
            if pack.id == pack_id:
                return pack
        return None

    def _load_pack(self, path: Path) -> LessonPack:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return LessonPack.model_validate(raw)
