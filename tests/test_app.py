from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module

client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Arrange: ensure the in-memory database is fresh for every test."""
    original = deepcopy(app_module.activities)
    yield
    app_module.activities.clear()
    app_module.activities.update(original)


def test_root_redirects_to_static_index():
    # Arrange: client is ready (fixture already ran)
    # Act (don't follow redirect so we can inspect headers)
    response = client.get("/", follow_redirects=False)
    # Assert
    assert response.status_code in (307, 308, 200)
    # If FastAPI followed the redirect automatically we still want to verify the final URL
    if response.status_code in (307, 308):
        assert response.headers["location"].endswith("/static/index.html")
    else:
        # testclient automatically handled it and returned content for index.html
        assert "<" in response.text  # simple sanity check


def test_get_activities_returns_full_dict():
    # Act
    response = client.get("/activities")
    # Assert
    assert response.status_code == 200
    assert "Chess Club" in response.json()


def test_signup_success_new_participant():
    # Arrange
    activity = "Chess Club"
    email = "newstudent@mergington.edu"
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert email in app_module.activities[activity]["participants"]


def test_signup_already_signed():
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"
    # Act
    response = client.post(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_signup_nonexistent_activity():
    # Act
    response = client.post("/activities/Nonexistent/signup", params={"email": "a@b.com"})
    # Assert
    assert response.status_code == 404


def test_signup_activity_full():
    # Arrange: create a full activity
    name = "Tiny"
    app_module.activities[name] = {
        "description": "",
        "schedule": "",
        "max_participants": 1,
        "participants": ["a@b.com"],
    }
    # Act
    response = client.post(f"/activities/{name}/signup", params={"email": "new@b.com"})
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_remove_success():
    # Arrange
    activity = "Chess Club"
    email = "michael@mergington.edu"
    # Act
    response = client.delete(f"/activities/{activity}/signup", params={"email": email})
    # Assert
    assert response.status_code == 200
    assert email not in app_module.activities[activity]["participants"]


def test_remove_not_signed():
    # Act
    response = client.delete(
        "/activities/Chess Club/signup", params={"email": "nouser@mergington.edu"}
    )
    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up"


def test_remove_nonexistent_activity():
    # Act
    response = client.delete("/activities/Nowhere/signup", params={"email": "x@x.com"})
    # Assert
    assert response.status_code == 404
