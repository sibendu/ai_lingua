from fastapi import APIRouter, HTTPException

from app.schemas.lessons import LessonCatalog, LessonPack
from app.services.lesson_service import LessonService


router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("", response_model=LessonCatalog)
def list_lessons() -> LessonCatalog:
    return LessonCatalog(packs=LessonService().list_packs(language="fr"))


@router.get("/{pack_id}", response_model=LessonPack)
def get_lesson_pack(pack_id: str) -> LessonPack:
    pack = LessonService().get_pack(pack_id)
    if pack is None or pack.language != "fr":
        raise HTTPException(status_code=404, detail="Lesson pack not found")
    return pack
