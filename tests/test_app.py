"""Tests for the Mergington High School API endpoints."""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities database before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    """Provide a FastAPI TestClient instance."""
    return TestClient(app)


# ──────────────────────────────────────────────
# GET /
# ──────────────────────────────────────────────

class TestRootRedirect:
    def test_redirects_to_index(self, client):
        # Arrange — no special setup needed

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


# ──────────────────────────────────────────────
# GET /activities
# ──────────────────────────────────────────────

class TestGetActivities:
    def test_returns_all_activities(self, client):
        # Arrange
        expected_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == len(activities)
        for name, details in data.items():
            assert expected_keys.issubset(details.keys())

    def test_activity_has_participants_list(self, client):
        # Arrange — use a known activity
        activity_name = "Chess Club"

        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        assert activity_name in data
        assert isinstance(data[activity_name]["participants"], list)
        assert len(data[activity_name]["participants"]) > 0


# ──────────────────────────────────────────────
# POST /activities/{activity_name}/signup
# ──────────────────────────────────────────────

class TestSignup:
    def test_successful_signup(self, client):
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email},
        )

        # Assert
        assert response.status_code == 200
        assert new_email in response.json()["message"]
        assert new_email in activities[activity_name]["participants"]

    def test_duplicate_signup_returns_400(self, client):
        # Arrange — michael is already in Chess Club
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email},
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_nonexistent_activity_returns_404(self, client):
        # Arrange
        fake_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{fake_activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


# ──────────────────────────────────────────────
# DELETE /activities/{activity_name}/signup
# ──────────────────────────────────────────────

class TestUnregister:
    def test_successful_unregister(self, client):
        # Arrange — michael is currently in Chess Club
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act
        response = client.request(
            "DELETE",
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert email not in activities[activity_name]["participants"]

    def test_unregister_non_participant_returns_400(self, client):
        # Arrange — this student is not in Chess Club
        activity_name = "Chess Club"
        email = "nobody@mergington.edu"

        # Act
        response = client.request(
            "DELETE",
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_unregister_nonexistent_activity_returns_404(self, client):
        # Arrange
        fake_activity = "Underwater Basket Weaving"
        email = "student@mergington.edu"

        # Act
        response = client.request(
            "DELETE",
            f"/activities/{fake_activity}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
