from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_conversation import router as conversation_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_discussion import router as discussion_router
from app.api.routes_health import router as health_router
from app.api.routes_lessons import router as lessons_router
from app.api.routes_practice import router as practice_router
from app.api.routes_question import router as question_router
from app.api.routes_settings import router as settings_router
from app.api.routes_stt import router as stt_router
from app.api.routes_tts import router as tts_router
from app.core.config import get_settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    settings.local_audio_storage_root.mkdir(parents=True, exist_ok=True)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="French-first local AI Lingua MVP backend.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(conversation_router)
app.include_router(dashboard_router)
app.include_router(discussion_router)
app.include_router(lessons_router)
app.include_router(practice_router)
app.include_router(question_router)
app.include_router(settings_router)
app.include_router(stt_router)
app.include_router(tts_router)
settings.local_audio_storage_root.mkdir(parents=True, exist_ok=True)
app.mount(
    "/audio",
    StaticFiles(directory=settings.local_audio_storage_root),
    name="audio",
)
