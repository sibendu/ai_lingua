from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def create_attempt(client: TestClient, family_id: str, child_id: str, transcript: str) -> None:
    response = client.post(
        "/practice/attempt",
        json={
            "family_id": family_id,
            "child_id": child_id,
            "practice_item_id": "fr-greetings-001",
            "target_text": "Bonjour.",
            "transcript": transcript,
            "mode": "listen_repeat",
        },
    )
    assert response.status_code == 200


def test_child_dashboard_reflects_saved_attempts() -> None:
    family_id = f"family-{uuid4()}"
    child_id = f"child-{uuid4()}"

    with TestClient(app) as client:
        create_attempt(client, family_id, child_id, "bonjour")
        response = client.get(f"/dashboard/child/{child_id}?family_id={family_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["total_attempts"] == 1
    assert body["attempts_today"] == 1
    assert body["stars"] == 3
    assert body["average_score"] >= 90


def test_parent_dashboard_includes_recent_attempts_and_topics() -> None:
    family_id = f"family-{uuid4()}"
    child_id = f"child-{uuid4()}"

    with TestClient(app) as client:
        create_attempt(client, family_id, child_id, "salut")
        response = client.get(f"/dashboard/parent/{child_id}?family_id={family_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["total_attempts"] == 1
    assert body["recent_attempts"][0]["target_text"] == "Bonjour."
    assert body["recent_attempts"][0]["topic"] == "greetings"
    assert body["weak_topics"][0]["topic"] == "greetings"
