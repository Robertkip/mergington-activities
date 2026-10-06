"""Mergington High School extracurricular activities API."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Mergington High School Activities")

# Activities live in memory only. Restarting the server restores this list.
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build small projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays and Fridays, 2:00 PM - 3:00 PM",
        "participants": ["john@mergington.edu", "olivia@mergington.edu"],
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "participants": ["liam@mergington.edu", "noah@mergington.edu"],
    },
    "Drama Club": {
        "description": "Act, direct and produce the school plays",
        "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
        "participants": ["ava@mergington.edu", "mia@mergington.edu"],
    },
    "Art Studio": {
        "description": "Explore painting, drawing and sculpture",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"],
    },
}


@app.get("/")
def root():
    """Send visitors to the activities page."""
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    """Return every activity with its description, schedule and participants."""
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str):
    """Sign a student up for an activity."""
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    participants = activities[activity_name]["participants"]
    if email in participants:
        raise HTTPException(status_code=400, detail="Student is already signed up")

    participants.append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
