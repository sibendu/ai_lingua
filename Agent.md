# AI Lingua Agent Guide

## Project Goal

Build a local-first language practice app for a child, starting with French. The app should support voice-based practice using local models where possible:

- STT: child speech to text
- SLM: local tutor and feedback generation
- TTS: French speech playback
- Dashboards: child-friendly progress and parent analytics

The first MVP is French-only. The architecture must keep language-specific pieces isolated so Bengali and other languages can be added later.

The first implementation should run locally, but it must be designed so it can later be hosted on the internet for multiple families, parents, and children. Avoid choices that assume a single child, single parent, single machine, or single global progress record.

## Current Implementation Snapshot

Last updated after the French-first MVP build-out in this repo.

Implemented stack:

- Frontend: Next.js TypeScript app in `frontend/`, Tailwind CSS, browser `MediaRecorder`.
- Backend: FastAPI app in `backend/`, SQLModel/SQLite persistence, Pydantic settings.
- Local models/services:
  - STT: `faster-whisper`.
  - TTS: Piper.
  - Tutor/SLM: Ollama `qwen3:8b`.
- Local profile constants currently used by frontend:
  - `family_id`: `local-family`
  - `child_id`: `local-child`

Implemented backend endpoints:

- `GET /health`
- `GET /lessons`
- `GET /lessons/{pack_id}`
- `POST /tts`
- `POST /stt/transcribe`
- `GET /practice/next`
- `POST /practice/attempt`
- `POST /conversation/message`
- `POST /discussion/start`
- `POST /discussion/answer`
- `GET /dashboard/child/{child_id}?family_id=...`
- `GET /dashboard/parent/{child_id}?family_id=...`
- `GET /settings/{child_id}?family_id=...`
- `PATCH /settings`

Implemented database models in `backend/app/db/models.py`:

- `Family`
- `User`
- `ChildProfile`
- `PracticeItem`
- `PracticeSession`
- `Attempt`
- `Settings`
- `AudioAsset`
- `ConversationTurn`
- `DiscussionSession`
- `DiscussionTurn`

Implemented backend services:

- `LessonService`: loads `backend/app/data/lessons/french_mvp.json`.
- `LocalAudioStorage`: local audio allocation and upload storage under `LOCAL_AUDIO_STORAGE_PATH`.
- `PiperTTSService`: Piper wrapper, generated WAV cache by text and voice path, UTF-8 subprocess input, emoji/control/symbol sanitization.
- `FasterWhisperSTTService`: French STT wrapper, in-process model cache keyed by model/device/compute type, tunable beam/VAD settings.
- `ScoringService`: deterministic text scoring with accent-insensitive tokenization, word/char similarity, missing/extra words.
- `PracticeService`: local profile creation, lesson item lookup/upsert, practice session creation.
- `OllamaTutorService`: local tutor client using Ollama `/api/chat`, `think: false`, tolerant response parsing for Qwen-style output.
- `DiscussionService`: topic discussion sessions and turns, including improvement-loop tracking.
- `ProgressService`: child and parent dashboard aggregation.
- `SettingsService`: get/create/update local child settings.

Implemented frontend behavior:

- Main screen is the actual app, not a landing page.
- Tabs:
  - `listen_repeat`
  - `vocabulary`
  - `conversation`
  - `discussion`
- Play button calls `/tts` and plays returned `/audio/...` WAV.
- Record/stop buttons use browser `MediaRecorder`, upload audio to `/stt/transcribe`, and display transcript.
- Listen/vocabulary modes submit transcript to `/practice/attempt`, then show deterministic score, feedback, missing words, stars, words practiced, and saved attempt counts.
- Conversation mode records child speech, transcribes it, sends text to `/conversation/message`, shows tutor reply, and auto-plays tutor audio.
- Discussion mode:
  - Has `Topic` textbox and `Start` button.
  - `Start` calls `/discussion/start`; tutor asks a topic-relevant question.
  - Child answers by voice; transcript goes to `/discussion/answer`.
  - Tutor gives brief feedback and either asks for one short improvement retry or moves on.
  - Backend forces movement after 2 consecutive improvement turns so the child does not get stuck.
- Parent panel:
  - Loads/saves `difficulty`, `daily_goal_minutes`, and `preferred_topics` through `/settings`.
  - Preferred topics influence visible practice items.
  - Loads child/parent dashboard data from persisted attempts.

Important performance and reliability fixes already applied:

- STT model is kept warm in memory after first load.
- STT env tuning is supported:
  - `WHISPER_BEAM_SIZE`
  - `WHISPER_VAD_FILTER`
- Recommended fast CPU STT profile:
  - `WHISPER_MODEL=base`
  - `WHISPER_DEVICE=cpu`
  - `WHISPER_COMPUTE_TYPE=int8`
  - `WHISPER_BEAM_SIZE=1`
  - `WHISPER_VAD_FILTER=false`
- `audio/webm;codecs=opus` is normalized to `audio/webm` for browser uploads.
- Piper TTS uses a backend cache so repeated prompts do not respawn Piper.
- Piper TTS sends UTF-8 bytes to subprocess to avoid Windows `UnicodeEncodeError`.
- Piper TTS strips emoji/symbol/control characters before synthesis.
- Ollama/Qwen tutor calls use `think: false`.
- Ollama responses are parsed tolerantly:
  - plain text
  - JSON
  - JSON code fences
  - output wrapped with `<think>...</think>`
  - empty content falls back to a safe short tutor reply.

Current environment variables:

- `APP_ENV`
- `DATABASE_URL`
- `STORAGE_BACKEND`
- `LOCAL_AUDIO_STORAGE_PATH`
- `PUBLIC_BASE_URL`
- `NEXT_PUBLIC_API_BASE_URL`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_AUTH_TOKEN`
- `WHISPER_MODEL`
- `WHISPER_DEVICE`
- `WHISPER_COMPUTE_TYPE`
- `WHISPER_BEAM_SIZE`
- `WHISPER_VAD_FILTER`
- `MAX_AUDIO_UPLOAD_MB`
- `PIPER_BIN_PATH`
- `PIPER_VOICE_PATH`

Verification status at this snapshot:

- Backend tests pass: 29 tests.
- Frontend production build passes.
- User manually verified:
  - frontend and backend run manually
  - STT works from the frontend
  - Ollama conversation works after disabling thinking and tolerant parsing
  - TTS audio playback works from frontend

Important workflow preference from user:

- Do not start backend or frontend servers automatically. The user runs and verifies servers manually.
- It is fine to run one-shot commands such as tests, build, dependency installs, and file inspections.

## Target User Experience

The child should be able to:

- Hear a French phrase or question.
- Record themselves speaking.
- See what the app heard.
- Get a simple score and kind correction.
- Retry or move to the next item.
- Practice vocabulary and guided conversation.
- See friendly progress indicators.

The parent should be able to:

- View practice history.
- See weak words and topics.
- Track daily/weekly progress.
- Adjust difficulty and daily practice goals.

## MVP Features

1. Listen and Repeat
   - Play a French phrase.
   - Record child speech.
   - Transcribe with STT.
   - Score transcript against target.
   - Give gentle correction and retry option.

2. Guided Conversation
   - Tutor asks simple French questions.
   - Child responds by voice.
   - Tutor replies briefly and age-appropriately.

3. Vocabulary Practice
   - Prompt with a word, phrase, or later an image.
   - Child says the French answer.
   - App validates and reinforces.

4. Parent Controls
   - Difficulty level.
   - Practice topic.
   - Daily goal.
   - Child profile settings.

5. Child Dashboard
   - Streak.
   - Stars or points.
   - Words practiced.
   - Today progress.
   - Encouraging recent wins.

6. Parent Dashboard
   - Session history.
   - Accuracy trends.
   - Weak words and topics.
   - Practice duration.
   - Recent attempts with target, transcript, score, and feedback.

## Final Technology Choices

Frontend:

- Next.js
- TypeScript
- Tailwind CSS
- shadcn/ui or Radix UI primitives where useful
- Browser MediaRecorder / Web Audio APIs for recording

Backend:

- Python
- FastAPI
- Pydantic
- SQLite for MVP persistence, with models designed to migrate cleanly to Postgres
- SQLAlchemy or SQLModel for database access

Local Models:

- SLM: Ollama `qwen3:8b`
- STT: `faster-whisper` with `openai/whisper-large-v3-turbo`
- STT fallback: Whisper medium or small if laptop performance requires it
- TTS: Piper with French voice `fr_FR-siwis-medium`

Runtime:

- Windows host with WSL2
- Ollama already running locally
- Backend runs in WSL2
- Frontend runs in WSL2 or Windows Node.js, depending on developer preference

Future hosted runtime:

- Container-friendly backend and frontend
- Postgres-compatible schema
- Object storage-compatible audio paths
- Auth-ready user and family model
- Model services behind configurable endpoints

## Multi-User And Hosted Architecture Requirements

The MVP is local-first, but code generation must assume future internet hosting for multiple users.

Design requirements:

- Every child belongs to a family or household account.
- Parent users can manage one or more child profiles.
- Progress, attempts, settings, sessions, and audio references must always be scoped by `family_id` and/or `child_id`.
- Avoid global singleton state for the active child, active lesson, active settings, or active session.
- Backend APIs should accept explicit `child_id` where child-specific data is involved.
- Do not trust client-provided ownership in the future; structure services so authorization checks can be added later.
- Use UUID primary keys where practical, or keep IDs abstract enough to migrate from local SQLite to hosted Postgres.
- Store generated/uploaded audio behind a storage abstraction instead of hard-coding permanent local filesystem paths into business logic.
- Keep model providers configurable so local Ollama/Piper/Whisper can later be replaced by hosted services or worker queues.
- Long-running STT/TTS/LLM work should be isolated in service classes so background jobs can be added later.
- Do not add full production auth in the first MVP unless asked, but leave clear seams for it.

Initial auth stance:

- Local MVP may use simple profile selection and a parent PIN.
- Future hosted version should support real authentication, such as email/password, OAuth, or magic links.
- Do not store child personal data beyond what is needed for practice.
- Avoid collecting exact age, school name, location, or sensitive personal details unless explicitly required later.

## Secrets And Configuration

Never hard-code credentials or local secrets.

Use environment variables for:

- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `OLLAMA_AUTH_TOKEN` or equivalent auth setting if needed
- `WHISPER_MODEL`
- `PIPER_BIN_PATH`
- `PIPER_VOICE_PATH`
- `DATABASE_URL`
- `APP_ENV`
- `STORAGE_BACKEND`
- `LOCAL_AUDIO_STORAGE_PATH`
- `PUBLIC_BASE_URL`

Provide `.env.example` with placeholder values only.

## Recommended Repo Structure

```text
ai_lingua/
  Agent.md
  README.md
  .env.example
  backend/
    app/
      main.py
      core/
        config.py
      db/
        models.py
        session.py
      services/
        llm_service.py
        scoring_service.py
        stt_service.py
        tts_service.py
        lesson_service.py
        progress_service.py
        storage_service.py
      api/
        routes_health.py
        routes_lessons.py
        routes_practice.py
        routes_conversation.py
        routes_dashboard.py
      data/
        lessons/
          french_mvp.json
      schemas/
        practice.py
        dashboard.py
        lessons.py
    tests/
    pyproject.toml
  frontend/
    app/
    components/
    lib/
    package.json
```

This structure is a guide. Prefer existing project conventions if the repo later evolves.

## Backend API Plan

Core endpoints:

- `GET /health`
  - Return backend, model config, and dependency status where safe.

- `GET /lessons`
  - Return available French lesson packs and practice items.

- `GET /practice/next`
  - Return the next practice item for a child, mode, topic, and difficulty.

- `POST /practice/attempt`
  - Accept recorded audio and target item metadata.
  - Run STT.
  - Score the transcript.
  - Generate feedback.
  - Save attempt.
  - Return transcript, score, feedback, and optional correction audio URL.

- `POST /conversation/message`
  - Accept child speech or text.
  - Use STT if speech.
  - Send constrained prompt to Ollama.
  - Save conversation turn.
  - Return tutor reply and optional TTS audio URL.

- `POST /tts`
  - Generate French audio for given text.

- `GET /dashboard/child/{child_id}`
  - Return simple progress summary for child UI.

- `GET /dashboard/parent/{child_id}`
  - Return detailed progress analytics.

- `PATCH /settings`
  - Update local profile or practice settings.

Hosted-readiness notes:

- Child-specific endpoints must be implemented so authorization and family ownership checks can be added later.
- Local MVP requests may pass `child_id` directly, but service methods should also accept or resolve `family_id`.
- API response shapes should not expose raw local filesystem paths. Return stable audio URLs or audio asset IDs.

## Initial Data Model

Suggested entities:

- `Family`
  - `id`
  - `name`
  - `created_at`

- `User`
  - `id`
  - `family_id`
  - `name`
  - `role`: `child` or `parent`
  - `created_at`

- `ChildProfile`
  - `id`
  - `family_id`
  - `display_name`
  - `preferred_language`
  - `created_at`

- `PracticeItem`
  - `id`
  - `language`
  - `mode`
  - `topic`
  - `difficulty`
  - `text_fr`
  - `text_en`
  - `expected_keywords`

- `PracticeSession`
  - `id`
  - `family_id`
  - `child_id`
  - `mode`
  - `started_at`
  - `ended_at`

- `Attempt`
  - `id`
  - `family_id`
  - `child_id`
  - `session_id`
  - `practice_item_id`
  - `target_text`
  - `transcript`
  - `score`
  - `feedback`
  - `audio_asset_id`
  - `created_at`

- `Settings`
  - `id`
  - `family_id`
  - `child_id`
  - `difficulty`
  - `daily_goal_minutes`
  - `preferred_topics`

- `AudioAsset`
  - `id`
  - `family_id`
  - `child_id`
  - `kind`: `upload`, `tts`, or `system_prompt`
  - `storage_uri`
  - `content_type`
  - `created_at`

For the local MVP, a `User` with role `child` and `ChildProfile` may point to the same real child, but keep `ChildProfile` explicit so parent accounts and child accounts can evolve independently later.

## Scoring Strategy

For MVP, use text-level scoring.

Steps:

1. Normalize target and transcript.
   - Lowercase.
   - Trim whitespace.
   - Remove punctuation.
   - Optionally normalize French apostrophes.
   - Keep accents initially; add accent-insensitive comparison as a secondary score.

2. Compute:
   - Word-level similarity.
   - Character-level similarity.
   - Missing target words.
   - Extra transcript words.

3. Return:
   - Overall score from 0 to 100.
   - `excellent`, `good`, `try_again`, or `needs_help`.
   - Short feedback.

Do not rely on the SLM to calculate scores. Use deterministic scoring first, then optionally ask the SLM to rewrite feedback in a child-friendly tone.

## Ollama Tutor Rules

Use `qwen3:8b` through Ollama for tutoring and natural feedback.

System prompt requirements:

- The tutor is kind, brief, and child-safe.
- The tutor teaches beginner French.
- Replies should be short.
- The tutor should encourage first, correct second.
- Avoid adult topics, politics, scary content, and open-ended unsafe conversation.
- Use simple French, with English support only when helpful.
- Do not generate long explanations.
- Prefer one question or one correction at a time.

For structured backend calls, require JSON responses and validate them with Pydantic.

## French MVP Lesson Packs

Start with these topics:

1. Greetings
   - Bonjour.
   - Salut.
   - Au revoir.
   - Comment ca va ?
   - Je vais bien.

2. Family
   - Maman.
   - Papa.
   - Ma soeur.
   - Mon frere.
   - J'aime ma famille.

3. Food
   - Une pomme.
   - Du pain.
   - De l'eau.
   - Du lait.
   - Je mange une pomme.

4. School
   - Un livre.
   - Un stylo.
   - L'ecole.
   - J'ai un livre.
   - Je vais a l'ecole.

5. Simple Sentences
   - Je suis content.
   - J'aime le chocolat.
   - Je veux de l'eau.
   - Ou est le livre ?
   - Merci beaucoup.

## Frontend Design Direction

This is a child practice app, not a marketing site.

Build the actual app as the first screen:

- Clear navigation.
- Big record button.
- Play prompt button.
- Friendly progress indicators.
- Simple feedback.
- Parent dashboard separate from child practice.

Avoid:

- Landing-page hero sections.
- Decorative cards that do not help the task.
- Overly complex controls.
- Long text instructions inside the UI.

Use accessible controls:

- Icon buttons for play, record, stop, retry, next.
- Tabs for practice modes.
- Toggle or segmented control for difficulty.
- Charts only where they help parent tracking.

## Implementation Order

1. Create repo scaffolding.
   - Backend FastAPI app.
   - Frontend Next.js app.
   - `.env.example`.
   - README setup commands.

2. Backend foundation.
   - Config loading.
   - Health endpoint.
   - SQLite models.
   - Lesson JSON loading.

3. TTS integration.
   - Piper wrapper.
   - Generate WAV files.
   - Serve generated audio.

4. STT integration.
   - Audio upload endpoint.
   - faster-whisper wrapper.
   - French language hint.

5. Practice loop.
   - Next practice item.
   - Record audio.
   - Submit attempt.
   - Return transcript, score, feedback.
   - Save attempt.

6. Ollama tutor.
   - LLM client.
   - Safe tutor prompt.
   - Guided conversation endpoint.

7. Dashboards.
   - Child dashboard.
   - Parent dashboard.
   - Progress aggregation.

8. Polish and verification.
   - Loading states.
   - Error states.
   - Empty states.
   - Basic tests for scoring and lesson loading.

## Development Guidelines For Future Agents

- Read this file before making changes.
- Keep the MVP French-only unless explicitly asked to add another language.
- Keep language-specific behavior behind configuration or lesson data.
- Keep data scoped for future multi-family, multi-child hosting.
- Do not introduce single-user assumptions into database models or APIs.
- Keep storage abstract so local audio files can later move to S3, Azure Blob, or Google Cloud Storage.
- Prefer deterministic scoring over LLM-only scoring.
- Keep child safety constraints in prompts and backend validation.
- Never commit secrets.
- Use small, testable services in the backend.
- Preserve local-first operation.
- Prefer clear, boring code over clever abstractions.
- Do not add cloud dependencies unless the user explicitly asks.
- When adding dependencies, update setup docs.
- When changing APIs, update frontend callers and README.

## Verification Checklist

Before handing off a feature:

- Backend starts successfully.
- Frontend starts successfully.
- `/health` responds.
- At least one French lesson loads.
- TTS produces playable French audio.
- STT can transcribe a sample French recording or the failure mode is documented.
- Practice attempt returns transcript, score, and feedback.
- Child dashboard reflects saved attempts.
- Parent dashboard reflects saved attempts.
- No credentials are hard-coded.
