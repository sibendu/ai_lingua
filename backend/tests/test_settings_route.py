from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


def test_get_settings_creates_defaults() -> None:
    family_id = f"family-{uuid4()}"
    child_id = f"child-{uuid4()}"

    with TestClient(app) as client:
        response = client.get(f"/settings/{child_id}?family_id={family_id}")

    assert response.status_code == 200
    body = response.json()
    assert body["family_id"] == family_id
    assert body["child_id"] == child_id
    assert body["difficulty"] == "beginner"
    assert body["daily_goal_minutes"] == 10
    assert body["preferred_topics"] == []


def test_patch_settings_updates_values() -> None:
    family_id = f"family-{uuid4()}"
    child_id = f"child-{uuid4()}"

    with TestClient(app) as client:
        response = client.patch(
            "/settings",
            json={
                "family_id": family_id,
                "child_id": child_id,
                "difficulty": "beginner",
                "daily_goal_minutes": 15,
                "preferred_topics": ["greetings", "food"],
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["daily_goal_minutes"] == 15
    assert body["preferred_topics"] == ["greetings", "food"]
