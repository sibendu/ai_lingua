import subprocess

from app.services.storage_service import LocalAudioStorage
from app.services.tts_service import PiperTTSService, TTSNotConfiguredError, sanitize_tts_text


def test_piper_tts_requires_configuration() -> None:
    service = PiperTTSService(piper_bin_path="", piper_voice_path="")

    try:
        service.synthesize_french("Bonjour.")
    except TTSNotConfiguredError:
        return

    raise AssertionError("Expected TTSNotConfiguredError")


def test_piper_tts_writes_generated_audio(tmp_path, monkeypatch) -> None:
    piper_bin = tmp_path / "piper.exe"
    voice = tmp_path / "fr_FR-siwis-medium.onnx"
    piper_bin.write_text("fake", encoding="utf-8")
    voice.write_text("fake", encoding="utf-8")

    def fake_run(command, **kwargs):
        output_path = command[command.index("--output_file") + 1]
        with open(output_path, "wb") as wav_file:
            wav_file.write(b"RIFFfake-wave")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    service = PiperTTSService(
        storage=LocalAudioStorage(root=tmp_path / "audio"),
        piper_bin_path=str(piper_bin),
        piper_voice_path=str(voice),
    )

    location = service.synthesize_french("Bonjour.")

    assert location.file_path.exists()
    assert location.storage_uri.startswith("local://tts/")
    assert location.public_url.startswith("/audio/tts/")


def test_piper_tts_reuses_cached_audio(tmp_path, monkeypatch) -> None:
    piper_bin = tmp_path / "piper.exe"
    voice = tmp_path / "fr_FR-siwis-medium.onnx"
    piper_bin.write_text("fake", encoding="utf-8")
    voice.write_text("fake", encoding="utf-8")
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        output_path = command[command.index("--output_file") + 1]
        with open(output_path, "wb") as wav_file:
            wav_file.write(b"RIFFfake-wave")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    service = PiperTTSService(
        storage=LocalAudioStorage(root=tmp_path / "audio"),
        piper_bin_path=str(piper_bin),
        piper_voice_path=str(voice),
    )

    first = service.synthesize_french("Bonjour.")
    second = service.synthesize_french("Bonjour.")

    assert first.file_path == second.file_path
    assert len(calls) == 1


def test_piper_tts_encodes_input_as_utf8_bytes(tmp_path, monkeypatch) -> None:
    piper_bin = tmp_path / "piper.exe"
    voice = tmp_path / "fr_FR-siwis-medium.onnx"
    piper_bin.write_text("fake", encoding="utf-8")
    voice.write_text("fake", encoding="utf-8")
    observed_input = []

    def fake_run(command, **kwargs):
        observed_input.append(kwargs["input"])
        output_path = command[command.index("--output_file") + 1]
        with open(output_path, "wb") as wav_file:
            wav_file.write(b"RIFFfake-wave")
        return subprocess.CompletedProcess(command, 0, stdout=b"", stderr=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    service = PiperTTSService(
        storage=LocalAudioStorage(root=tmp_path / "audio"),
        piper_bin_path=str(piper_bin),
        piper_voice_path=str(voice),
    )

    service.synthesize_french("Tres bien 😊 !")

    assert observed_input == ["Tres bien !".encode("utf-8")]


def test_sanitize_tts_text_removes_symbols_and_controls() -> None:
    assert sanitize_tts_text("Bravo 😊\nEncore !") == "Bravo Encore !"
