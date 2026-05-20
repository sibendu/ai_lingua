from app.services.lesson_service import LessonService


def test_french_lesson_pack_loads() -> None:
    packs = LessonService().list_packs(language="fr")

    assert len(packs) == 1
    assert packs[0].id == "french-mvp"
    assert len(packs[0].items) == 25
