from fastapi.testclient import TestClient

import app.api.routes_question as routes_question
from app.main import app
from app.services.llm_service import TutorReply


class FakeTutorService:
    async def answer_child_question(self, *, question: str, difficulty: str):
        assert question == "Comment dit-on apple ?"
        assert difficulty == "beginner"
        return TutorReply(reply="On dit pomme.")


def test_question_ask_persists_turn(monkeypatch) -> None:
    monkeypatch.setattr(routes_question, "OllamaTutorService", FakeTutorService)

    with TestClient(app) as client:
        response = client.post(
            "/question/ask",
            json={
                "family_id": "question-family-1",
                "child_id": "question-child-1",
                "question": "Comment dit-on apple ?",
                "difficulty": "beginner",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["turn_id"]
    assert body["question"] == "Comment dit-on apple ?"
    assert body["tutor_reply"] == "On dit pomme."

