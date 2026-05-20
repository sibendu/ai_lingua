# AI Lingua

Local-first language practice app for children, starting with French.

This scaffold covers Phase 1 and Phase 2:

- FastAPI backend with config loading
- `/health` endpoint
- SQLite-ready SQLModel models
- French MVP lesson loading from JSON
- Next.js TypeScript frontend shell

Phase 3 has started with Piper TTS:

- `POST /tts` generates French WAV audio when Piper is configured
- generated audio is served from `/audio/...`
- audio references are stored as `AudioAsset` rows with family and child scope
- the frontend play button synthesizes and plays the current French prompt
- conversation tutor replies are played automatically when Piper is configured

Phase 4 has started with faster-whisper STT:

- `POST /stt/transcribe` accepts French audio uploads
- uploads are stored as `AudioAsset` rows when Whisper is configured
- transcription uses a French language hint

Phase 5 has started with the deterministic practice loop:

- `GET /practice/next` returns a French practice item
- `POST /practice/attempt` scores a transcript and saves the attempt
- the frontend records, transcribes, scores, and displays feedback

Phase 6 has started with Ollama guided conversation:

- `POST /conversation/message` sends child text to a constrained local tutor prompt
- conversation turns are saved with family and child scope
- the frontend conversation tab records, transcribes, and displays the tutor reply
- `POST /discussion/start` starts a topic-based discussion
- `POST /discussion/answer` assesses each child answer, gives brief feedback, and keeps the discussion moving
- the frontend discussion tab has a topic box, start button, tutor audio, and turn history

Phase 7 has started with dashboards:

- `GET /dashboard/child/{child_id}` returns child-friendly progress totals
- `GET /dashboard/parent/{child_id}` returns parent analytics and recent attempts
- the frontend side panel loads persisted progress for `local-family` / `local-child`

Parent controls/settings are wired:

- `GET /settings/{child_id}` returns saved child practice settings
- `PATCH /settings` updates difficulty, daily goal, and preferred topics
- the frontend loads and saves settings for `local-family` / `local-child`

## Requirements

- Python 3.11+
- Node.js 20+

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Backend defaults to `sqlite:///./ai_lingua.db`. Override values by copying `.env.example` to `.env` at the repo root or setting environment variables in your shell.

Useful endpoints:

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/lessons`
- `GET http://localhost:8000/lessons/french-mvp`
- `POST http://localhost:8000/tts`
- `POST http://localhost:8000/stt/transcribe`
- `GET http://localhost:8000/practice/next`
- `POST http://localhost:8000/practice/attempt`
- `POST http://localhost:8000/conversation/message`
- `POST http://localhost:8000/discussion/start`
- `POST http://localhost:8000/discussion/answer`
- `GET http://localhost:8000/dashboard/child/local-child?family_id=local-family`
- `GET http://localhost:8000/dashboard/parent/local-child?family_id=local-family`
- `GET http://localhost:8000/settings/local-child?family_id=local-family`
- `PATCH http://localhost:8000/settings`

Example TTS request:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8000/tts `
  -ContentType "application/json" `
  -Body '{"family_id":"local-family","text":"Bonjour.","language":"fr"}'
```

## Piper TTS Setup

Piper is only needed when testing `/tts`. Install Piper where the backend process runs.

Set these values in `.env`:

```text
PIPER_BIN_PATH=C:\path\to\piper.exe
PIPER_VOICE_PATH=C:\path\to\fr_FR-siwis-medium.onnx
LOCAL_AUDIO_STORAGE_PATH=./storage/audio
```

If you run the backend inside WSL2, use Linux paths for both Piper settings. If you run the backend from Windows PowerShell, use Windows paths.

Generated Piper WAV files are cached by text and voice path, so repeated prompts such as `Bonjour.` return the existing audio file instead of spawning Piper again.

## faster-whisper STT Setup

STT is only needed when testing `/stt/transcribe`. The backend dependency is installed from `pyproject.toml`.

Set these values in `.env`:

```text
WHISPER_MODEL=large-v3-turbo
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_BEAM_SIZE=1
WHISPER_VAD_FILTER=false
MAX_AUDIO_UPLOAD_MB=25
```

For lower-memory laptops, start with:

```text
WHISPER_MODEL=small
WHISPER_COMPUTE_TYPE=int8
```

Fastest CPU profile:

```text
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8
WHISPER_BEAM_SIZE=1
WHISPER_VAD_FILTER=false
```

The backend keeps the loaded Whisper model warm in memory after the first request. The first transcription after restart can still be slow, but later requests avoid reloading the model.

Use CUDA only after CUDA 12 runtime libraries are installed and available on the backend process PATH:

```text
WHISPER_DEVICE=cuda
WHISPER_COMPUTE_TYPE=float16
```

`WHISPER_MODEL` can be a faster-whisper model name, a compatible Hugging Face model repo, or a local model directory. The first transcription may download model files and take longer.

## Ollama Tutor Setup

Ollama is only needed when testing the conversation tab or `/conversation/message`.

Set these values in `.env`:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen3:8b
OLLAMA_AUTH_TOKEN=
```

If Ollama is running inside WSL2 and the backend is running from Windows PowerShell, `http://localhost:11434` usually works when Ollama is listening on all needed interfaces. If it does not, use the WSL2 host/IP URL that your Windows backend can reach.

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

The frontend reads `NEXT_PUBLIC_API_BASE_URL`, defaulting to `http://localhost:8000`.

Browser recording is wired to `/stt/transcribe`:

- allow microphone access when the browser asks
- press the microphone button, speak the French prompt, then press stop
- the transcript appears in the practice panel
- use `http://localhost:3000` or `https`; browser microphone APIs do not work on arbitrary insecure origins

Tutor audio is wired to `/tts`:

- press the play button to hear the current prompt
- in conversation mode, the tutor reply auto-plays after STT and Ollama finish
- if Piper is not configured, text practice still works and the audio error appears in the panel

## Data Model Direction

The MVP is local-first, but models are scoped for future hosted use:

- families own users, child profiles, sessions, attempts, settings, and audio assets
- child-specific data carries `family_id` and `child_id`
- IDs are string UUIDs for easier migration from SQLite to Postgres
- audio is represented as `AudioAsset.storage_uri`, not hard-coded business paths

## Current Non-Goals

- No production authentication
