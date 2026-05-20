from fastapi.testclient import TestClient

import app.api.routes_discussion as routes_discussion
from app.main import app
from app.services.llm_service import DiscussionTutorReply, TutorReply


class FakeTutorService:
    answer_calls = 0

    async def start_discussion(self, *, topic: str, difficulty: str):
        assert topic == "football"
        return TutorReply(reply="Tu aimes le football ?")

    async def continue_discussion(
        self,
        *,
        topic: str,
        child_text: str,
        turn_index: int,
        improvement_attempts: int,
        difficulty: str,
    ):
        FakeTutorService.answer_calls += 1
        return DiscussionTutorReply(
            feedback="Bonne idee. Prononce doucement.",
            reply="Essaie encore: J'aime le football.",
            needs_improvement=True,
        )


def test_start_and_answer_discussion(monkeypatch) -> None:
    monkeypatch.setattr(routes_discussion, "OllamaTutorService", FakeTutorService)

    with TestClient(app) as client:
        start = client.post(
            "/discussion/start",
            json={
                "family_id": "discussion-family-1",
                "child_id": "discussion-child-1",
                "topic": "football",
                "difficulty": "beginner",
            },
        )
        assert start.status_code == 200
        session_id = start.json()["session_id"]

        answer = client.post(
            "/discussion/answer",
            json={
                "family_id": "discussion-family-1",
                "child_id": "discussion-child-1",
                "session_id": session_id,
                "child_text": "J'aime football",
            },
        )

    assert answer.status_code == 200
    body = answer.json()
    assert body["feedback"] == "Bonne idee. Prononce doucement."
    assert body["tutor_reply"] == "Essaie encore: J'aime le football."
    assert body["needs_improvement"] is True
    assert body["turn_index"] == 1


def test_discussion_moves_on_after_two_improvement_turns(monkeypatch) -> None:
    monkeypatch.setattr(routes_discussion, "OllamaTutorService", FakeTutorService)

    with TestClient(app) as client:
        start = client.post(
            "/discussion/start",
            json={
                "family_id": "discussion-family-2",
                "child_id": "discussion-child-2",
                "topic": "football",
            },
        )
        session_id = start.json()["session_id"]

        for _ in range(3):
            answer = client.post(
                "/discussion/answer",
                json={
                    "family_id": "discussion-family-2",
                    "child_id": "discussion-child-2",
                    "session_id": session_id,
                    "child_text": "football",
                },
            )

    assert answer.status_code == 200
    assert answer.json()["needs_improvement"] is False
