from fastapi.testclient import TestClient

import app.api.routes_conversation as routes_conversation
from app.main import app
from app.services.llm_service import TutorReply


class FakeTutorService:
    is_configured = True

    async def reply_to_child(self, *, child_text: str, topic: str | None, difficulty: str):
        assert child_text == "Bonjour"
        assert topic == "greetings"
        return TutorReply(reply="Bravo ! Bonjour a toi.")


def test_conversation_message_persists_turn(monkeypatch) -> None:
    monkeypatch.setattr(routes_conversation, "OllamaTutorService", FakeTutorService)

    with TestClient(app) as client:
        response = client.post(
            "/conversation/message",
            json={
                "family_id": "test-family-conversation",
                "child_id": "test-child-conversation",
                "child_text": "Bonjour",
                "topic": "greetings",
                "difficulty": "beginner",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["turn_id"]
    assert body["tutor_reply"] == "Bravo ! Bonjour a toi."
