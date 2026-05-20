from fastapi.testclient import TestClient

from app.main import app


def test_get_next_practice_item() -> None:
    with TestClient(app) as client:
        response = client.get("/practice/next?mode=listen_repeat&difficulty=beginner")

    assert response.status_code == 200
    body = response.json()
    assert body["item"]["language"] == "fr"
    assert body["item"]["text_fr"]


def test_submit_practice_attempt_persists_and_scores() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/practice/attempt",
            json={
                "family_id": "test-family-practice",
                "child_id": "test-child-practice",
                "practice_item_id": "fr-greetings-001",
                "target_text": "Bonjour.",
                "transcript": "bonjour",
                "mode": "listen_repeat",
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["attempt_id"]
    assert body["session_id"]
    assert body["score"]["label"] == "excellent"
