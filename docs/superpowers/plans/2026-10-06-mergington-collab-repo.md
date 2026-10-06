# Mergington Collaboration Repo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a small runnable Mergington High School activities site plus the files that let several teachers collaborate on it safely: ruleset, contributor guide, code owners, code of conduct, security policy, Dependabot config and a GitHub setup guide.

**Architecture:** One FastAPI app serves a JSON API and a static HTML/JS page. Every collaboration artifact is a plain file in the repository. Settings that cannot be files are documented in docs/github-setup.md. Nothing in this plan changes GitHub settings.

**Tech Stack:** Python 3.10+, FastAPI 0.142.2, uvicorn 0.54.0, pytest 9.1.1, httpx2 2.13.1 (used by FastAPI's TestClient), vanilla HTML/CSS/JS, GitHub rulesets, CODEOWNERS and Dependabot configuration.

**Design:** [docs/superpowers/specs/2026-10-06-mergington-collab-repo-design.md](../specs/2026-10-06-mergington-collab-repo-design.md)

## Global Constraints

Every task's requirements include this section.

- The repository lives in a GitHub organization named `mergington-high-school` with teams `maintainers`, `backend` and `frontend`. These are stand-in names the owner replaces before pushing.
- Files only: no CI, no setup scripts, nothing that changes GitHub settings.
- Python with FastAPI plus a static HTML/JS page. pip is the only dependency ecosystem. requirements.txt pins exact versions.
- The default branch is `main`. The ruleset targets `~DEFAULT_BRANCH` and has an empty bypass list.
- Stand-in values: conduct contact `conduct@mergington-high-school.example`; security contact `security@mergington-high-school.example`; acknowledgment within 3 business days; security update pull requests reviewed within 5 business days.
- Site data lives in memory. No database, no authentication, no persistence.
- Statements about GitHub features must be supported by GitHub's documentation (the sources are listed in docs/github-setup.md). Do not add claims the documentation does not support.
- Run every command from the repository root.
- Python tools run from a virtualenv outside the repository. Set `VENV` and `CHECKS` in every new shell (in a Claude Code session, use the session scratchpad directory instead of `/tmp`):

  ```bash
  export VENV=/tmp/mergington-venv
  export CHECKS=/tmp/mergington-checks
  mkdir -p "$CHECKS"
  ```

- Every commit message ends with the trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. Commit with `git commit -m "<subject>" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"`.

## File Structure

| File | Responsibility | Task |
|---|---|---|
| .gitignore | Keep virtualenvs and caches out of git | 1 |
| requirements.txt | Pinned runtime and test dependencies | 1 |
| src/app.py | Activities data, list and sign-up endpoints, static file serving | 1, 2 |
| tests/test_app.py | Tests for the API and the static page | 1, 2 |
| README.md | What the site is, how to run and test it, links to the collaboration docs | 1, 9 |
| src/static/index.html, styles.css, app.js | The page students see | 2 |
| .github/rulesets/protect-main.json | Branch ruleset for the default branch | 3 |
| .github/CODEOWNERS | Which team owns which path | 4 |
| CONTRIBUTING.md, .github/pull_request_template.md, .github/ISSUE_TEMPLATE/ | Procedure for collaborators | 5 |
| CODE_OF_CONDUCT.md | Ground rules | 6 |
| SECURITY.md, .github/dependabot.yml | Security reporting and the update process | 7 |
| docs/github-setup.md | Manual settings, stand-in values, personal vs organization | 8 |

---

### Task 1: Activities API

**Files:**
- Create: `.gitignore`
- Create: `requirements.txt`
- Create: `src/app.py`
- Create: `tests/test_app.py`
- Create: `README.md`

**Interfaces:**
- Produces: `src.app.app` (the FastAPI instance) and `src.app.activities`, a `dict[str, dict]` mapping an activity name to `{"description": str, "schedule": str, "participants": list[str]}`.
- Produces: `GET /activities` returns `activities` as JSON.
- Produces: `POST /activities/{activity_name}/signup?email=<email>` returns 200 `{"message": "Signed up <email> for <activity_name>"}`, 404 `{"detail": "Activity not found"}` for an unknown activity, or 400 `{"detail": "Student is already signed up"}` for a repeat sign-up.
- Produces: README.md with the sections "Run the site" and "Run the tests".

- [ ] **Step 1: Create .gitignore and requirements.txt**

`.gitignore`:

```
.venv/
__pycache__/
.pytest_cache/
```

`requirements.txt` (httpx2 is the package Starlette's TestClient now expects; plain httpx makes it print a deprecation warning):

```
fastapi==0.142.2
httpx2==2.13.1
pytest==9.1.1
uvicorn==0.54.0
```

- [ ] **Step 2: Create the virtualenv and install the dependencies**

Run:

```bash
python3 -m venv "$VENV"
"$VENV/bin/pip" install -q -r requirements.txt
"$VENV/bin/pip" freeze | grep -iE '^(fastapi|uvicorn|httpx2|pytest)=='
```

Expected: exactly these four lines (other installed packages are dependencies and are filtered out):

```
fastapi==0.142.2
httpx2==2.13.1
pytest==9.1.1
uvicorn==0.54.0
```

- [ ] **Step 3: Write the failing tests**

Create `tests/test_app.py`:

```python
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
```

- [ ] **Step 4: Run the tests to verify they fail**

Run: `"$VENV/bin/python" -m pytest -q`

Expected: a collection error, `ModuleNotFoundError: No module named 'src'`, and `1 error` in the summary. (`python -m pytest` rather than bare `pytest` puts the repository root on the import path, which is what makes `src.app` importable.)

- [ ] **Step 5: Write the implementation**

Create `src/app.py`:

```python
"""Mergington High School extracurricular activities API."""
from fastapi import FastAPI, HTTPException

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
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `"$VENV/bin/python" -m pytest -v`

Expected: `4 passed` and no warnings.

- [ ] **Step 7: Write README.md**

Create `README.md`:

````markdown
# Mergington High School Activities

A small website where students can browse extracurricular activities and sign up for them. It is deliberately simple: activities are kept in memory, and there is no database and no login. The point of this repository is to show how a school team can work on one codebase safely.

## Run the site

You need Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.app:app --reload
```

Then open http://127.0.0.1:8000. Activities and sign-ups are lost when the server restarts.

## Run the tests

With the virtual environment active:

```bash
python -m pytest
```
````

- [ ] **Step 8: Check that the documented run command works**

Run:

```bash
"$VENV/bin/uvicorn" src.app:app --port 8765 &
SERVER_PID=$!
curl -s --retry 10 --retry-connrefused --retry-delay 1 http://127.0.0.1:8765/activities | head -c 120; echo
kill "$SERVER_PID"
```

Expected: uvicorn's own log lines, then JSON beginning `{"Chess Club":{"description":"Learn strategies and compete`.

- [ ] **Step 9: Commit**

```bash
git add .gitignore requirements.txt src/app.py tests/test_app.py README.md
git commit -m "Add activities API with tests" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Static activities page

**Files:**
- Create: `src/static/index.html`
- Create: `src/static/styles.css`
- Create: `src/static/app.js`
- Modify: `src/app.py` (imports, a root route, and a static mount)
- Modify: `tests/test_app.py` (two new tests at the end)

**Interfaces:**
- Consumes: `app`, `GET /activities` and `POST /activities/{activity_name}/signup?email=<email>` from Task 1.
- Produces: `GET /` redirects (307) to `/static/index.html`; every file in `src/static/` is served under `/static`.
- Produces: the page contract that the frontend team owns: an element with id `activities-list` holding one `article.activity` per activity, and an element with id `message` showing the sign-up result.

- [ ] **Step 1: Write the failing tests**

Append to the end of `tests/test_app.py`:

```python


def test_root_redirects_to_the_static_page():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_page_is_served():
    response = client.get("/static/index.html")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'id="activities-list"' in response.text
```

- [ ] **Step 2: Run the tests to verify the new ones fail**

Run: `"$VENV/bin/python" -m pytest -q`

Expected: `2 failed, 4 passed`, with `assert 404 == 307` for `test_root_redirects_to_the_static_page` and `assert 404 == 200` for `test_static_page_is_served`.

- [ ] **Step 3: Create the static files**

`src/static/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Mergington High School Activities</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <header>
    <h1>Mergington High School</h1>
    <p>Extracurricular activities</p>
  </header>
  <main>
    <p id="message" class="message hidden" role="status"></p>
    <section id="activities-list" aria-live="polite">Loading activities…</section>
  </main>
  <script src="app.js"></script>
</body>
</html>
```

`src/static/styles.css`:

```css
:root {
  --accent: #1b4d89;
  --background: #f6f8fb;
  --text: #1f2933;
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: system-ui, sans-serif;
  line-height: 1.5;
  color: var(--text);
  background: var(--background);
}

header {
  padding: 1.5rem 1rem;
  text-align: center;
  color: #fff;
  background: var(--accent);
}

header h1,
header p {
  margin: 0;
}

main {
  max-width: 60rem;
  margin: 0 auto;
  padding: 1rem;
}

#activities-list {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fill, minmax(18rem, 1fr));
}

.activity {
  padding: 1rem;
  background: #fff;
  border: 1px solid #d5dde8;
  border-radius: 0.5rem;
}

.activity h2 {
  margin-top: 0;
  font-size: 1.25rem;
  color: var(--accent);
}

.activity h3 {
  margin-bottom: 0.25rem;
  font-size: 1rem;
}

.activity ul {
  margin: 0 0 1rem;
  padding-left: 1.25rem;
}

.activity form {
  display: flex;
  gap: 0.5rem;
}

.activity input {
  flex: 1;
  min-width: 0;
  padding: 0.4rem;
}

.activity button {
  padding: 0.4rem 0.8rem;
  color: #fff;
  background: var(--accent);
  border: 0;
  border-radius: 0.25rem;
  cursor: pointer;
}

.schedule {
  font-weight: 600;
}

.message {
  padding: 0.75rem 1rem;
  border-radius: 0.25rem;
}

.message.hidden {
  display: none;
}

.message.success {
  background: #e3f4e6;
  border: 1px solid #8cc9a0;
}

.message.error {
  background: #fde8e8;
  border: 1px solid #e0a0a0;
}
```

`src/static/app.js`:

```javascript
const listEl = document.getElementById("activities-list");
const messageEl = document.getElementById("message");

function showMessage(text, isError) {
  messageEl.textContent = text;
  messageEl.className = isError ? "message error" : "message success";
}

// The page is built with textContent, never innerHTML, so an email typed by a
// student can never inject markup into the page.
function renderActivity(name, activity) {
  const card = document.createElement("article");
  card.className = "activity";

  const title = document.createElement("h2");
  title.textContent = name;

  const description = document.createElement("p");
  description.textContent = activity.description;

  const schedule = document.createElement("p");
  schedule.className = "schedule";
  schedule.textContent = activity.schedule;

  const participantsTitle = document.createElement("h3");
  participantsTitle.textContent = "Signed up";

  const participants = document.createElement("ul");
  for (const email of activity.participants) {
    const item = document.createElement("li");
    item.textContent = email;
    participants.appendChild(item);
  }

  const form = document.createElement("form");
  const input = document.createElement("input");
  input.type = "email";
  input.required = true;
  input.placeholder = "your.email@mergington.edu";
  input.setAttribute("aria-label", "Email address for " + name);
  const button = document.createElement("button");
  button.type = "submit";
  button.textContent = "Sign up";
  form.append(input, button);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    signUp(name, input.value);
  });

  card.append(title, description, schedule, participantsTitle, participants, form);
  return card;
}

async function loadActivities() {
  const response = await fetch("/activities");
  const activities = await response.json();
  listEl.replaceChildren(
    ...Object.entries(activities).map(([name, activity]) => renderActivity(name, activity))
  );
}

async function signUp(name, email) {
  const url = "/activities/" + encodeURIComponent(name) + "/signup?email=" + encodeURIComponent(email);
  const response = await fetch(url, { method: "POST" });
  const result = await response.json();
  if (response.ok) {
    showMessage(result.message, false);
    await loadActivities();
  } else {
    showMessage(typeof result.detail === "string" ? result.detail : "Something went wrong.", true);
  }
}

loadActivities().catch(() => showMessage("Could not load activities. Please try again.", true));
```

- [ ] **Step 4: Serve the page from the app**

Make three edits to `src/app.py`.

Replace the first two lines:

```python
"""Mergington High School extracurricular activities API."""
from fastapi import FastAPI, HTTPException
```

with:

```python
"""Mergington High School extracurricular activities API."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
```

Insert this route immediately before `@app.get("/activities")`, followed by two blank lines:

```python
@app.get("/")
def root():
    """Send visitors to the activities page."""
    return RedirectResponse(url="/static/index.html")
```

Add this line at the very end of the file, after the `signup_for_activity` function and two blank lines:

```python
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `"$VENV/bin/python" -m pytest -v`

Expected: `6 passed` and no warnings.

- [ ] **Step 6: Check the running page**

Run:

```bash
node --check src/static/app.js && echo "app.js: syntax ok"
"$VENV/bin/uvicorn" src.app:app --port 8765 &
SERVER_PID=$!
for path in / /static/index.html /static/styles.css /static/app.js /activities; do
  curl -s --retry 10 --retry-connrefused --retry-delay 1 -o /dev/null -w "$path -> %{http_code}\n" "http://127.0.0.1:8765$path"
done
kill "$SERVER_PID"
```

Expected (plus uvicorn's log lines; skip the first line if Node.js is not installed):

```
app.js: syntax ok
/ -> 307
/static/index.html -> 200
/static/styles.css -> 200
/static/app.js -> 200
/activities -> 200
```

Then check the page in a browser. Start the server again with `"$VENV/bin/uvicorn" src.app:app --port 8765`, open http://127.0.0.1:8765/ and confirm:

1. The address bar shows `/static/index.html` and six activity cards appear, each with its schedule, participants and an email form.
2. Typing `tester@mergington.edu` into the Chess Club form and clicking **Sign up** shows a green message, "Signed up tester@mergington.edu for Chess Club", and the email appears in that card's list.
3. Signing up the same email again shows a red message, "Student is already signed up".

Stop the server with Ctrl+C.

- [ ] **Step 7: Commit**

```bash
git add src/static src/app.py tests/test_app.py
git commit -m "Add static activities page" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Branch ruleset

**Files:**
- Create: `.github/rulesets/protect-main.json`
- Create (outside the repository): `$CHECKS/check_ruleset.py`

**Interfaces:**
- Produces: a ruleset named `protect-main`, imported by hand as described in Task 8. The `pull_request` rule's `require_code_owner_review` relies on `.github/CODEOWNERS` from Task 4.

- [ ] **Step 1: Write the check**

Create `$CHECKS/check_ruleset.py`. The required parameter names come from GitHub's REST API schema for the `pull_request` rule.

```python
import json
import pathlib

ruleset = json.loads(pathlib.Path(".github/rulesets/protect-main.json").read_text())

assert ruleset["name"] == "protect-main"
assert ruleset["target"] == "branch"
assert ruleset["enforcement"] == "active"
assert ruleset["conditions"]["ref_name"]["include"] == ["~DEFAULT_BRANCH"]
assert ruleset["bypass_actors"] == []

rules = {rule["type"]: rule for rule in ruleset["rules"]}
assert set(rules) == {"deletion", "non_fast_forward", "pull_request"}, set(rules)

required = {
    "dismiss_stale_reviews_on_push",
    "require_code_owner_review",
    "require_last_push_approval",
    "required_approving_review_count",
    "required_review_thread_resolution",
}
params = rules["pull_request"]["parameters"]
assert required <= set(params), required - set(params)
assert params["required_approving_review_count"] == 1
assert params["dismiss_stale_reviews_on_push"] is True
assert params["require_code_owner_review"] is True
assert params["required_review_thread_resolution"] is True

print("ruleset ok")
```

- [ ] **Step 2: Run the check to verify it fails**

Run: `python3 -I "$CHECKS/check_ruleset.py"`

Expected: a traceback ending in `FileNotFoundError` for `.github/rulesets/protect-main.json`.

- [ ] **Step 3: Create the ruleset**

Create `.github/rulesets/protect-main.json`:

```json
{
  "name": "protect-main",
  "target": "branch",
  "enforcement": "active",
  "conditions": {
    "ref_name": {
      "include": ["~DEFAULT_BRANCH"],
      "exclude": []
    }
  },
  "bypass_actors": [],
  "rules": [
    { "type": "deletion" },
    { "type": "non_fast_forward" },
    {
      "type": "pull_request",
      "parameters": {
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_code_owner_review": true,
        "require_last_push_approval": false,
        "required_review_thread_resolution": true
      }
    }
  ]
}
```

- [ ] **Step 4: Run the check to verify it passes**

Run: `python3 -I "$CHECKS/check_ruleset.py"`

Expected: `ruleset ok`

- [ ] **Step 5: Commit**

```bash
git add .github/rulesets/protect-main.json
git commit -m "Add branch ruleset for the default branch" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Code owners

**Files:**
- Create: `.github/CODEOWNERS`
- Create (outside the repository): `$CHECKS/check_codeowners.py`

**Interfaces:**
- Consumes: the team names from Global Constraints.
- Produces: `.github/CODEOWNERS` assigning `src/app.py` and `tests/` to `@mergington-high-school/backend`, `src/static/` to `@mergington-high-school/frontend`, and everything else, including `.github/`, `docs/` and `SECURITY.md`, to `@mergington-high-school/maintainers`. Task 8 documents these stand-in names. Task 9 checks that each pattern matches a real path.

- [ ] **Step 1: Write the check**

Create `$CHECKS/check_codeowners.py`:

```python
import pathlib
import re

lines = [
    line.split()
    for line in pathlib.Path(".github/CODEOWNERS").read_text().splitlines()
    if line.strip() and not line.startswith("#")
]
owner = re.compile(r"@mergington-high-school/(maintainers|backend|frontend)")
expected = {
    "*": "maintainers",
    "/src/app.py": "backend",
    "/tests/": "backend",
    "/src/static/": "frontend",
    "/.github/": "maintainers",
    "/docs/": "maintainers",
    "/SECURITY.md": "maintainers",
}

found = {}
for pattern, *owners in lines:
    assert len(owners) == 1 and owner.fullmatch(owners[0]), (pattern, owners)
    found[pattern] = owners[0].split("/")[1]
assert found == expected, found

print("codeowners ok")
```

- [ ] **Step 2: Run the check to verify it fails**

Run: `python3 -I "$CHECKS/check_codeowners.py"`

Expected: a traceback ending in `FileNotFoundError` for `.github/CODEOWNERS`.

- [ ] **Step 3: Create CODEOWNERS**

Create `.github/CODEOWNERS`:

```text
# Each line is a path pattern followed by the team that owns it.
# The last matching pattern wins, so the catch-all comes first.
*             @mergington-high-school/maintainers
/src/app.py   @mergington-high-school/backend
/tests/       @mergington-high-school/backend
/src/static/  @mergington-high-school/frontend

# Maintainers own this file and the ruleset, so the protections cannot be
# changed without them.
/.github/     @mergington-high-school/maintainers
/docs/        @mergington-high-school/maintainers
/SECURITY.md  @mergington-high-school/maintainers
```

- [ ] **Step 4: Run the check to verify it passes**

Run: `python3 -I "$CHECKS/check_codeowners.py"`

Expected: `codeowners ok`

- [ ] **Step 5: Commit**

```bash
git add .github/CODEOWNERS
git commit -m "Add CODEOWNERS" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Contribution procedure and templates

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `.github/pull_request_template.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.md`
- Create: `.github/ISSUE_TEMPLATE/activity_request.md`
- Create: `.github/ISSUE_TEMPLATE/config.yml`
- Create (outside the repository): `$CHECKS/check_contributing.py`

**Interfaces:**
- Consumes: the ownership table from Task 4 and the run and test commands from Task 1.
- Produces: CONTRIBUTING.md, which links to CODE_OF_CONDUCT.md (Task 6), SECURITY.md (Task 7) and docs/github-setup.md (Task 8). Those links resolve once those tasks are done, and Task 9 checks them.

- [ ] **Step 1: Write the check**

PyYAML is installed only for this check and is not added to requirements.txt.

Run: `"$VENV/bin/pip" install -q pyyaml`

Create `$CHECKS/check_contributing.py`:

```python
import pathlib

import yaml

issue_dir = pathlib.Path(".github/ISSUE_TEMPLATE")
for name in ("bug_report.md", "activity_request.md"):
    _, front, body = (issue_dir / name).read_text().split("---", 2)
    meta = yaml.safe_load(front)
    assert {"name", "about", "labels"} <= set(meta), (name, meta)
    assert body.strip(), name

config = yaml.safe_load((issue_dir / "config.yml").read_text())
assert config == {"blank_issues_enabled": False}, config

template = pathlib.Path(".github/pull_request_template.md").read_text()
for heading in ("## Summary", "## Linked issue", "## How it was tested", "## Checklist"):
    assert heading in template, heading

contributing = pathlib.Path("CONTRIBUTING.md").read_text()
for heading in (
    "## Before you start",
    "## Making a change",
    "## Running the site and tests",
    "## Review",
    "## Who owns what",
    "## Getting help",
):
    assert heading in contributing, heading

print("contributing files ok")
```

- [ ] **Step 2: Run the check to verify it fails**

Run: `"$VENV/bin/python" "$CHECKS/check_contributing.py"`

Expected: a traceback ending in `FileNotFoundError` for `.github/ISSUE_TEMPLATE/bug_report.md`.

- [ ] **Step 3: Create CONTRIBUTING.md**

````markdown
# Contributing

Thank you for helping with the Mergington High School activities site. This page explains how to make a change and how it gets reviewed. It takes about five minutes to read.

## Before you start

- Read the [code of conduct](CODE_OF_CONDUCT.md). It applies to everyone who works in this repository.
- Ask a maintainer to add you to the team for the area you will work on (see [Who owns what](#who-owns-what)). You need write access, which comes through your team, to push branches.

## Making a change

1. Open an issue that describes the change, or pick an existing one.
2. Create a branch from `main` named `<your-name>/<short-description>`, for example `ms-rivera/add-art-studio`.
3. Make small, focused commits. A reviewer should be able to read the whole change in one sitting.
4. Open a pull request and fill in the template.
5. Respond to review comments and resolve each conversation once it is addressed. Every conversation must be resolved before the pull request can be merged.
6. Once the pull request is approved, the author squash merges it and deletes the branch.

You cannot push directly to `main`, force push to it, or delete it. The repository ruleset enforces this, so it is not just a convention.

## Running the site and tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.app:app --reload   # the site, at http://127.0.0.1:8000
python -m pytest               # the tests
```

Run the tests before you open a pull request.

## Review

- Every pull request needs at least one approval. Authors cannot approve their own pull request.
- GitHub asks the owning team of each area you changed to review. A pull request that touches several areas needs an approval from an owner of each one.
- Pushing new commits dismisses earlier approvals, so finish your changes before you ask for a final review.

## Who owns what

[.github/CODEOWNERS](.github/CODEOWNERS) assigns each part of the code to a team:

| Area | Team |
|---|---|
| `src/app.py`, `tests/` | backend |
| `src/static/` | frontend |
| Everything else, including `.github/`, `docs/` and SECURITY.md | maintainers |

## Getting help

Ask in your pull request or issue, or ask a maintainer. To report a security problem, follow [SECURITY.md](SECURITY.md) instead of opening a public issue. Maintainers can find how the repository's settings are configured in [docs/github-setup.md](docs/github-setup.md).
````

- [ ] **Step 4: Create the pull request template**

`.github/pull_request_template.md`:

```markdown
## Summary

<!-- What does this change do, and why? -->

## Linked issue

Closes #

<!-- Add the issue number after the #, for example: Closes #12 -->

## How it was tested

<!-- For example: "python -m pytest passes" or "signed up for Chess Club in the browser". -->

## Checklist

- [ ] The tests pass (`python -m pytest`)
- [ ] Documentation is updated if behavior changed
- [ ] No secrets or personal data are committed
```

- [ ] **Step 5: Create the issue templates**

`.github/ISSUE_TEMPLATE/bug_report.md`:

```markdown
---
name: Bug report
about: Something on the activities site is not working as expected
title: ""
labels: bug
assignees: ""
---

## What happened

## What you expected

## Steps to reproduce

1.
2.
3.

## Anything else
```

`.github/ISSUE_TEMPLATE/activity_request.md`:

```markdown
---
name: Activity request
about: Ask for a new extracurricular activity or a change to an existing one
title: "Activity: "
labels: enhancement
assignees: ""
---

## Activity name

## Description

## Schedule

## Supervising teacher
```

`.github/ISSUE_TEMPLATE/config.yml`:

```yaml
blank_issues_enabled: false
```

- [ ] **Step 6: Run the check to verify it passes**

Run: `"$VENV/bin/python" "$CHECKS/check_contributing.py"`

Expected: `contributing files ok`

- [ ] **Step 7: Commit**

```bash
git add CONTRIBUTING.md .github/pull_request_template.md .github/ISSUE_TEMPLATE
git commit -m "Add contribution procedure and templates" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Code of conduct

**Files:**
- Create: `CODE_OF_CONDUCT.md`
- Create (outside the repository): `$CHECKS/check_conduct.py`

**Interfaces:**
- Consumes: the conduct contact `conduct@mergington-high-school.example` from Global Constraints.
- Produces: CODE_OF_CONDUCT.md, the Contributor Covenant 2.1 with that contact filled in. Task 8 documents the stand-in contact.

- [ ] **Step 1: Write the check**

Create `$CHECKS/check_conduct.py`:

```python
import pathlib

text = pathlib.Path("CODE_OF_CONDUCT.md").read_text()

assert text.startswith("# Contributor Covenant Code of Conduct"), text[:40]
assert "INSERT CONTACT METHOD" not in text
assert "conduct@mergington-high-school.example" in text
assert "version 2.1" in text
for heading in ("## Our Pledge", "## Our Standards", "## Enforcement Guidelines", "## Attribution"):
    assert heading in text, heading

print("code of conduct ok")
```

- [ ] **Step 2: Run the check to verify it fails**

Run: `python3 -I "$CHECKS/check_conduct.py"`

Expected: a traceback ending in `FileNotFoundError` for `CODE_OF_CONDUCT.md`.

- [ ] **Step 3: Download the official text into a fresh directory outside the repository**

Downloaded files are untrusted data. Keep this one in its own new directory, read it, and only then copy it in.

Run:

```bash
DL=$(mktemp -d "$CHECKS/covenant.XXXXXX")
curl -fsSL -o "$DL/code_of_conduct.md" https://www.contributor-covenant.org/version/2/1/code_of_conduct/code_of_conduct.md
grep -c '\[INSERT CONTACT METHOD\]' "$DL/code_of_conduct.md"
grep -c 'version 2.1' "$DL/code_of_conduct.md"
grep -c '^### [1-4]\. ' "$DL/code_of_conduct.md"
echo "$DL"
```

Expected: `1`, `1`, `4` and then the directory path. The three counts are: one contact placeholder, one attribution line naming version 2.1, and the four enforcement guideline headings. If any count differs, the upstream text has changed: stop and read the file before using it.

- [ ] **Step 4: Create CODE_OF_CONDUCT.md with the contact filled in**

Use the directory path printed in Step 3 as `$DL`. The `sed` call fills in the contact and drops the file's leading blank line.

Run:

```bash
sed -e 's/\[INSERT CONTACT METHOD\]/conduct@mergington-high-school.example/' -e '1{/^$/d}' "$DL/code_of_conduct.md" > CODE_OF_CONDUCT.md
```

- [ ] **Step 5: Run the check to verify it passes**

Run: `python3 -I "$CHECKS/check_conduct.py"`

Expected: `code of conduct ok`

- [ ] **Step 6: Commit**

```bash
git add CODE_OF_CONDUCT.md
git commit -m "Add code of conduct (Contributor Covenant 2.1)" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Security policy and Dependabot

**Files:**
- Create: `SECURITY.md`
- Create: `.github/dependabot.yml`
- Create (outside the repository): `$CHECKS/check_security.py`

**Interfaces:**
- Consumes: the security contact and the 3 and 5 business day response times from Global Constraints, and the maintainers' ownership of `requirements.txt` through the default rule in `.github/CODEOWNERS` (Task 4).
- Produces: SECURITY.md, which links to docs/github-setup.md (Task 8), and a Dependabot configuration for pip. Task 8 documents the stand-in contact and response times.

- [ ] **Step 1: Write the check**

PyYAML is installed only for this check and is not added to requirements.txt.

Run: `"$VENV/bin/pip" install -q pyyaml`

Create `$CHECKS/check_security.py`:

```python
import pathlib

import yaml

config = yaml.safe_load(pathlib.Path(".github/dependabot.yml").read_text())
assert config == {
    "version": 2,
    "updates": [
        {
            "package-ecosystem": "pip",
            "directory": "/",
            "schedule": {"interval": "weekly"},
        }
    ],
}, config

text = pathlib.Path("SECURITY.md").read_text()
for heading in (
    "## Supported versions",
    "## Reporting a vulnerability",
    "## What to expect",
    "## How security updates are handled",
):
    assert heading in text, heading
for value in ("security@mergington-high-school.example", "3 business days", "5 business days"):
    assert value in text, value

print("security files ok")
```

- [ ] **Step 2: Run the check to verify it fails**

Run: `"$VENV/bin/python" "$CHECKS/check_security.py"`

Expected: a traceback ending in `FileNotFoundError` for `.github/dependabot.yml`.

- [ ] **Step 3: Create dependabot.yml**

`.github/dependabot.yml`:

```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
```

- [ ] **Step 4: Create SECURITY.md**

```markdown
# Security policy

## Supported versions

Only the latest commit on `main` is supported. Security fixes are made there.

## Reporting a vulnerability

Please do not open a public issue for a security problem.

- If the repository's **Security** tab shows a **Report a vulnerability** button under **Advisories**, use it. That sends a private report to the maintainers.
- Otherwise, email security@mergington-high-school.example.

Include what you found, where you found it, and the steps to reproduce it if you can.

## What to expect

- We acknowledge your report within 3 business days.
- We keep you informed while we work on a fix, and tell you when it is released.

## How security updates are handled

1. **Version updates.** Dependabot checks the Python dependencies in `requirements.txt` every week and opens a pull request for each available update (see `.github/dependabot.yml`).
2. **Security updates.** When a dependency has a known vulnerability and a fix is available, Dependabot security updates open a pull request automatically. This is a repository setting; see [docs/github-setup.md](docs/github-setup.md).
3. **Review.** These pull requests follow the same rules as every other change. The repository ruleset applies, and the maintainers team reviews them because it owns `requirements.txt`.
4. **Testing.** There is no automated CI, so the reviewer checks out the Dependabot branch, runs `python -m pytest`, and merges only if the tests pass.
5. **Timing.** Security update pull requests are reviewed within 5 business days.
```

- [ ] **Step 5: Run the check to verify it passes**

Run: `"$VENV/bin/python" "$CHECKS/check_security.py"`

Expected: `security files ok`

- [ ] **Step 6: Commit**

```bash
git add SECURITY.md .github/dependabot.yml
git commit -m "Add security policy and Dependabot configuration" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 8: GitHub setup guide

**Files:**
- Create: `docs/github-setup.md`
- Create (outside the repository): `$CHECKS/check_setup_doc.py`

**Interfaces:**
- Consumes: every stand-in value from Tasks 4, 6 and 7 (organization and team names, the two contacts, the 3 and 5 business day response times), and the ruleset file from Task 3.
- Produces: docs/github-setup.md, which README.md links to in Task 9.

- [ ] **Step 1: Write the check**

Create `$CHECKS/check_setup_doc.py`:

```python
import pathlib

text = pathlib.Path("docs/github-setup.md").read_text()

for heading in (
    "## Values to replace before pushing",
    "## One-time setup",
    "## Check that it works",
    "## Personal vs organization repositories",
    "## Sources",
):
    assert heading in text, heading

# Every stand-in value must be documented here and really appear in the file it names.
stand_ins = {
    "mergington-high-school": ".github/CODEOWNERS",
    "maintainers": ".github/CODEOWNERS",
    "backend": ".github/CODEOWNERS",
    "frontend": ".github/CODEOWNERS",
    "conduct@mergington-high-school.example": "CODE_OF_CONDUCT.md",
    "security@mergington-high-school.example": "SECURITY.md",
    "3 business days": "SECURITY.md",
    "5 business days": "SECURITY.md",
}
for value, name in stand_ins.items():
    assert value in text, f"{value!r} is not documented"
    assert value in pathlib.Path(name).read_text(), f"{value!r} is missing from {name}"

print("setup guide ok")
```

- [ ] **Step 2: Run the check to verify it fails**

Run: `python3 -I "$CHECKS/check_setup_doc.py"`

Expected: a traceback ending in `FileNotFoundError` for `docs/github-setup.md`.

- [ ] **Step 3: Create docs/github-setup.md**

````markdown
# GitHub setup

Some of this repository's protections live in GitHub settings, not in files. This page covers those settings, the stand-in values to replace before you push, and how personal and organization repositories differ.

## Values to replace before pushing

The files use stand-in values so they work as examples. Replace each one with the real value.

| Stand-in | Appears in | Replace with |
|---|---|---|
| `mergington-high-school` | .github/CODEOWNERS | The name of your GitHub organization |
| `maintainers`, `backend`, `frontend` | .github/CODEOWNERS | The slugs of your three teams |
| `conduct@mergington-high-school.example` | CODE_OF_CONDUCT.md | The address that receives conduct reports |
| `security@mergington-high-school.example` | SECURITY.md | The address that receives security reports |
| 3 business days | SECURITY.md | How quickly you can acknowledge a report |
| 5 business days | SECURITY.md | How quickly you can review a security update |

Do this before you push. GitHub skips a code owner that does not exist or lacks access, so with the stand-in names nobody is assigned and Code Owner review protects nothing. The `.example` addresses can never receive mail, so a report sent to one is lost.

## One-time setup

Do these steps in order. Creating teams needs an organization owner. The rest needs admin access to the repository.

1. **Create the repository** in your organization on GitHub and push `main` to it.
2. **Create three teams** named `maintainers`, `backend` and `frontend`. Click your profile picture, then **Organizations**, choose your organization, click **Teams**, then **New team**. Under **Team visibility**, choose the visible option, because a team can only be a code owner if it is visible. Put at least two people in each team: authors cannot approve their own pull requests, so a team of one cannot get its own changes merged.
3. **Give each team Write access.** In the repository, open **Settings**, click **Collaborators & teams** in the Access section of the sidebar, click **Add teams**, pick the team, choose the **Write** role under "Choose a role" and add it. GitHub requires the team itself to have write permission, even if its members already have it.
4. **Import the ruleset.** In the repository, open **Settings**, then **Rules** and **Rulesets** in the sidebar (GitHub's documentation has used both "Rules" and "Rulesets" for the top-level menu). Click **New ruleset**, then **Import a ruleset**, choose `.github/rulesets/protect-main.json`, review it and click **Create**. Confirm it is listed as active. Rulesets are available in public repositories on every plan, and in private repositories on GitHub Pro, GitHub Team and GitHub Enterprise Cloud. A private repository on the Free plan cannot use them.
5. **Turn on Dependabot.** In **Settings**, open **Advanced Security** (under "Security and quality" in the sidebar). Click **Enable** next to **Dependabot alerts**, then next to **Dependabot security updates**. Security updates need alerts to be on first. Weekly version updates need no setting: they start once `.github/dependabot.yml` is on the default branch.
6. **Turn on private vulnerability reporting.** On the same page, click **Enable** next to **Private vulnerability reporting**. GitHub documents this feature for public repositories. If your repository is private, skip this step: reporters use the email address in SECURITY.md instead. Once it is on, reporters see a **Report a vulnerability** button on the repository's **Advisories** page.
7. **Check CODEOWNERS.** Open `.github/CODEOWNERS` on GitHub. Any invalid line is highlighted as an error. There should be none.

## Check that it works

Once the ruleset is active, confirm each protection with a throwaway branch:

- A direct push to `main` is rejected.
- A force push to `main` is rejected.
- A pull request that changes only a file in `src/static/` asks the frontend team for review and cannot be merged until a frontend owner approves.
- A pull request with an unresolved review conversation cannot be merged.
- Anyone with read access can see the active rules by adding `/rules` to the repository URL, for example `https://github.com/<organization>/<repository>/rules`.

The ruleset has no bypass list, so these rules apply to organization owners and administrators too, and nobody can rename or delete `main` while the ruleset is active. If you ever need to, set the ruleset to disabled in its settings first and turn it back on afterwards.

## Personal vs organization repositories

This repository is set up for an organization. If it stayed in a personal account, these things would be different:

| | Personal account | Organization |
|---|---|---|
| Access levels | Two: the owner and collaborators. Collaborators cannot have read-only access to a private repository. | Five roles, from least to most access: Read, Triage, Write, Maintain and Admin. |
| Adding people | Invite each person as an individual collaborator. | Add people to teams and give each team a role on the repository. |
| CODEOWNERS | Can name individual users and email addresses. | Can also name teams, such as `@mergington-high-school/backend`. |
| Rulesets | Per repository. | Per repository, plus organization-level rulesets that cover several repositories at once (on plans that include them). |
| When someone leaves | The repository belongs to one person. | Organization owners have admin access to every repository, so nothing depends on one person. |

GitHub also limits how many people can be invited to a repository within 24 hours, and suggests creating an organization to collaborate with more people.

## Sources

Checked against GitHub's documentation on 2026-10-06:

- [About rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [Managing rulesets for a repository](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository)
- [Available rules for rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [REST API: rules](https://docs.github.com/en/rest/repos/rules) (the ruleset JSON fields)
- [About code owners](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
- [Approving a pull request with required reviews](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/approving-a-pull-request-with-required-reviews)
- [Creating an organization team](https://docs.github.com/en/organizations/organizing-members-into-teams/creating-a-team)
- [Managing teams and people with access to your repository](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/managing-teams-and-people-with-access-to-your-repository)
- [Repository roles for an organization](https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/repository-roles-for-an-organization)
- [Permission levels for a personal account repository](https://docs.github.com/en/account-and-profile/setting-up-and-managing-your-personal-account-on-github/managing-user-account-settings/permission-levels-for-a-personal-account-repository)
- [Configuring Dependabot alerts](https://docs.github.com/en/code-security/dependabot/dependabot-alerts/configuring-dependabot-alerts)
- [Configuring Dependabot security updates](https://docs.github.com/en/code-security/dependabot/dependabot-security-updates/configuring-dependabot-security-updates)
- [Dependabot options reference](https://docs.github.com/en/code-security/dependabot/working-with-dependabot/dependabot-options-reference)
- [Configuring private vulnerability reporting for a repository](https://docs.github.com/en/code-security/security-advisories/working-with-repository-security-advisories/configuring-private-vulnerability-reporting-for-a-repository)
````

- [ ] **Step 4: Run the check to verify it passes**

Run: `python3 -I "$CHECKS/check_setup_doc.py"`

Expected: `setup guide ok`

- [ ] **Step 5: Commit**

```bash
git add docs/github-setup.md
git commit -m "Add GitHub setup guide" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

---

### Task 9: README links and whole-repository checks

**Files:**
- Modify: `README.md` (add a "Collaborating" section at the end)
- Create (outside the repository): `$CHECKS/check_repo.py`

**Interfaces:**
- Consumes: CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md and docs/github-setup.md from Tasks 5 to 8, and `.github/CODEOWNERS` from Task 4.
- Produces: the finished repository. This task also runs the checks that only make sense across files.

- [ ] **Step 1: Write the whole-repository check**

Create `$CHECKS/check_repo.py`:

```python
import pathlib
import re

# 1. Relative links in the top-level Markdown files resolve.
files = [
    "README.md",
    "CONTRIBUTING.md",
    "CODE_OF_CONDUCT.md",
    "SECURITY.md",
    "docs/github-setup.md",
    ".github/pull_request_template.md",
]
link = re.compile(r"\]\(([^)\s#]+)(?:#[^)\s]*)?\)")
broken = []
for name in files:
    path = pathlib.Path(name)
    for target in link.findall(path.read_text()):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (path.parent / target).exists():
            broken.append(f"{name} -> {target}")
assert not broken, broken

# 2. Every CODEOWNERS pattern matches a path that exists.
for line in pathlib.Path(".github/CODEOWNERS").read_text().splitlines():
    if not line.strip() or line.startswith("#"):
        continue
    pattern = line.split()[0]
    if pattern != "*":
        assert pathlib.Path(pattern.strip("/")).exists(), f"CODEOWNERS pattern matches nothing: {pattern}"

# 3. The Contributor Covenant's contact placeholder was replaced.
assert "INSERT CONTACT METHOD" not in pathlib.Path("CODE_OF_CONDUCT.md").read_text()

# 4. README.md links to every collaboration document.
readme = pathlib.Path("README.md").read_text()
for name in ("CONTRIBUTING.md", "CODE_OF_CONDUCT.md", "SECURITY.md", "docs/github-setup.md"):
    assert f"]({name})" in readme, f"README.md does not link to {name}"

print("repository checks ok")
```

- [ ] **Step 2: Run the check to verify it fails**

Run: `python3 -I "$CHECKS/check_repo.py"`

Expected: an `AssertionError` saying `README.md does not link to CONTRIBUTING.md`. Steps 1 to 3 of the check pass because every other file exists after Tasks 1 to 8.

- [ ] **Step 3: Add the Collaborating section to README.md**

Append to the end of `README.md`:

```markdown

## Collaborating

- [CONTRIBUTING.md](CONTRIBUTING.md) explains how to make and review a change.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) sets the ground rules for everyone who works here.
- [SECURITY.md](SECURITY.md) explains how to report a vulnerability and how security updates are handled.
- [docs/github-setup.md](docs/github-setup.md) lists the GitHub settings maintainers need to configure, and how personal and organization repositories differ.
```

- [ ] **Step 4: Run the whole-repository check and the test suite**

Run:

```bash
python3 -I "$CHECKS/check_repo.py"
"$VENV/bin/python" -m pytest -q
```

Expected: `repository checks ok`, then `6 passed`.

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "Link the collaboration documents from the README" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 6: Confirm the working tree is clean**

Run: `git status --short && git log --oneline`

Expected: no output from `git status --short`, then the commit list, with the newest commit being "Link the collaboration documents from the README".

---

### Task 10: Page footer (added at the user's request during execution)

**Files:**
- Modify: `src/static/index.html` (add a footer element)
- Modify: `src/static/styles.css` (keep the footer at the bottom of the page, and style it)
- Modify: `tests/test_app.py` (one new test at the end)
- Modify: `docs/superpowers/specs/2026-10-06-mergington-collab-repo-design.md` (record the change)

**Interfaces:**
- Consumes: `client` and the static page from Tasks 1 and 2.
- Produces: a `<footer>` in `/static/index.html` reading "Developed by Open source © 2026. All rights reserved."

- [ ] **Step 1: Write the failing test**

Append to the end of `tests/test_app.py`:

```python


def test_static_page_has_a_footer():
    response = client.get("/static/index.html")

    assert "<footer>" in response.text
    assert "Developed by Open source &copy; 2026. All rights reserved." in response.text
```

- [ ] **Step 2: Run the tests to verify the new one fails**

Run: `"$VENV/bin/python" -m pytest -q`

Expected: `1 failed, 6 passed`, with `assert '<footer>' in ...` for `test_static_page_has_a_footer`.

- [ ] **Step 3: Add the footer to the page**

In `src/static/index.html`, replace:

```html
  </main>
  <script src="app.js"></script>
```

with:

```html
  </main>
  <footer>
    <p>Developed by Open source &copy; 2026. All rights reserved.</p>
  </footer>
  <script src="app.js"></script>
```

- [ ] **Step 4: Style the footer**

Make three edits to `src/static/styles.css`.

Replace the start of the `body` rule:

```css
body {
  margin: 0;
  font-family: system-ui, sans-serif;
```

with:

```css
body {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin: 0;
  font-family: system-ui, sans-serif;
```

Replace the `main` rule:

```css
main {
  max-width: 60rem;
  margin: 0 auto;
  padding: 1rem;
}
```

with (the `width: 100%` keeps the card grid full width inside the flex column):

```css
main {
  flex: 1;
  width: 100%;
  max-width: 60rem;
  margin: 0 auto;
  padding: 1rem;
}
```

Insert this after the `header h1, header p` rule:

```css
footer {
  padding: 1rem;
  text-align: center;
  color: #fff;
  background: var(--accent);
}

footer p {
  margin: 0;
}
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `"$VENV/bin/python" -m pytest -v`

Expected: `7 passed` and no warnings.

- [ ] **Step 6: Check the page in a browser**

Start the server with `"$VENV/bin/uvicorn" src.app:app --port 8765`, open http://127.0.0.1:8765/ and confirm the footer reads "Developed by Open source © 2026. All rights reserved." at the bottom of the page, and the activity cards are still laid out in a multi-column grid. Stop the server with Ctrl+C.

- [ ] **Step 7: Record the change in the spec**

At the end of `docs/superpowers/specs/2026-10-06-mergington-collab-repo-design.md`, add:

```markdown

## Changes requested during implementation

- The activities page has a footer reading "Developed by Open source © 2026. All rights reserved." It was requested on 2026-10-06 after the design was approved.
```

- [ ] **Step 8: Commit**

```bash
git add src/static tests/test_app.py docs/superpowers/specs/2026-10-06-mergington-collab-repo-design.md
git commit -m "Add page footer" -m "Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>"
```
