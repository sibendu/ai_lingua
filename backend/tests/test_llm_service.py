from types import SimpleNamespace

import pytest

import app.services.llm_service as llm_service
from app.services.llm_service import OllamaTutorService, parse_tutor_reply


class FakeAsyncClient:
    def __init__(self, *args, **kwargs) -> None:
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback) -> None:
        return None

    async def post(self, url, json, headers):
        assert url == "http://localhost:11434/api/chat"
        assert json["think"] is False
        assert json["messages"][0]["role"] == "system"
        return SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"message": {"content": '{"reply":"Tres bien ! Comment ca va ?"}'}},
        )


@pytest.mark.anyio
async def test_ollama_tutor_parses_json_reply(monkeypatch) -> None:
    monkeypatch.setattr(llm_service.httpx, "AsyncClient", FakeAsyncClient)
    service = OllamaTutorService(
        base_url="http://localhost:11434",
        model="qwen3:8b",
    )

    reply = await service.reply_to_child(child_text="Bonjour", topic="greetings")

    assert reply.reply == "Tres bien ! Comment ca va ?"


def test_parse_tutor_reply_strips_thinking_and_extracts_json() -> None:
    reply = parse_tutor_reply(
        '<think>I should be brief.</think>\n{"reply":"Bravo ! Essaie encore."}'
    )

    assert reply.reply == "Bravo ! Essaie encore."


def test_parse_tutor_reply_accepts_json_code_fence() -> None:
    reply = parse_tutor_reply('```json\n{"reply":"Super !"}\n```')

    assert reply.reply == "Super !"


def test_parse_tutor_reply_accepts_plain_short_reply() -> None:
    reply = parse_tutor_reply("Tres bien ! Comment ca va ?")

    assert reply.reply == "Tres bien ! Comment ca va ?"


def test_parse_tutor_reply_falls_back_on_empty_content() -> None:
    reply = parse_tutor_reply("")

    assert "francais" in reply.reply
