from types import SimpleNamespace

from fastapi.testclient import TestClient

import app.api.routes_stt as routes_stt
from app.main import app
from app.services.stt_service import TranscriptionResult


def test_stt_rejects_non_french_language() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/stt/transcribe",
            data={"family_id": "family-1", "language": "en"},
            files={"file": ("sample.wav", b"RIFFfake-wave", "audio/wav")},
        )

    assert response.status_code == 400


def test_stt_rejects_unsupported_content_type() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/stt/transcribe",
            data={"family_id": "family-1", "language": "fr"},
            files={"file": ("sample.txt", b"hello", "text/plain")},
        )

    assert response.status_code == 415


class FakeSTTService:
    is_configured = True

    def transcribe_french(self, audio_path):
        return TranscriptionResult(
            transcript="Bonjour",
            language="fr",
            duration_seconds=1.0,
            segments=[SimpleNamespace(start=0.0, end=1.0, text="Bonjour")],
        )


def test_stt_accepts_webm_with_codec_parameter(monkeypatch) -> None:
    monkeypatch.setattr(routes_stt, "FasterWhisperSTTService", FakeSTTService)

    with TestClient(app) as client:
        response = client.post(
            "/stt/transcribe",
            data={"family_id": "family-1", "language": "fr"},
            files={
                "file": (
                    "sample.webm",
                    b"fake-webm",
                    "audio/webm;codecs=opus",
                )
            },
        )

    assert response.status_code == 200
    assert response.json()["transcript"] == "Bonjour"
