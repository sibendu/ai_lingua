from pydantic import BaseModel, Field


class LessonItem(BaseModel):
    id: str
    language: str = "fr"
    mode: str
    topic: str
    difficulty: str = "beginner"
    text_fr: str
    text_en: str
    expected_keywords: list[str] = Field(default_factory=list)


class LessonPack(BaseModel):
    id: str
    language: str = "fr"
    title: str
    description: str
    topics: list[str]
    items: list[LessonItem]


class LessonCatalog(BaseModel):
    packs: list[LessonPack]
