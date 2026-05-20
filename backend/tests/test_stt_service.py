from types import SimpleNamespace

from app.services.stt_service import FasterWhisperSTTService, STTNotConfiguredError


class FakeWhisperModel:
    def transcribe(self, audio: str, **kwargs):
        assert kwargs["language"] == "fr"
        assert kwargs["task"] == "transcribe"
        assert kwargs["beam_size"] == 1
        assert kwargs["vad_filter"] is False
        segments = [
            SimpleNamespace(start=0.0, end=0.5, text=" Bonjour"),
            SimpleNamespace(start=0.5, end=1.0, text=" les amis"),
        ]
        info = SimpleNamespace(language="fr", duration=1.0)
        return segments, info


def test_stt_requires_configuration(tmp_path) -> None:
    service = FasterWhisperSTTService(model_name="")

    try:
        service.transcribe_french(tmp_path / "sample.wav")
    except STTNotConfiguredError:
        return

    raise AssertionError("Expected STTNotConfiguredError")


def test_stt_transcribes_with_french_hint(tmp_path) -> None:
    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(b"RIFFfake-wave")
    service = FasterWhisperSTTService(
        model_name="tiny",
        model=FakeWhisperModel(),
    )

    result = service.transcribe_french(audio_path)

    assert result.transcript == "Bonjour les amis"
    assert result.language == "fr"
    assert result.duration_seconds == 1.0
    assert len(result.segments) == 2
