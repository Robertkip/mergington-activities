import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Undo any sign-ups a test makes so the tests stay independent."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_get_activities_returns_the_seeded_activities():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    assert set(data["Chess Club"]) == {"description", "schedule", "participants"}


def test_signup_adds_the_participant():
    email = "new.student@mergington.edu"

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in client.get("/activities").json()["Chess Club"]["participants"]


def test_signing_up_twice_is_rejected():
    email = "new.student@mergington.edu"
    client.post("/activities/Chess Club/signup", params={"email": email})

    response = client.post("/activities/Chess Club/signup", params={"email": email})

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}


def test_signup_for_an_unknown_activity_returns_404():
    response = client.post(
        "/activities/Underwater Basket Weaving/signup",
        params={"email": "new.student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_root_redirects_to_the_static_page():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_page_is_served():
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="activities-list"' in response.text
