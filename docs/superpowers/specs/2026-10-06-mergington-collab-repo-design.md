# Mergington activities repo: collaboration setup

Date: 2026-10-06
Status: Approved for implementation (see "Changes made while planning" at the end)

## Goal

Prepare the Mergington High School extracurricular activities website repository so that additional teachers can collaborate on it safely. The objectives come from [starter.md](../../../starter.md) (GitHub Skills: Intro to Repository Management). The repository will live in a GitHub organization.

## Decisions

| Question | Decision |
|---|---|
| What is delivered? | A small runnable site plus the collaboration files. The site exists so the ruleset and CODEOWNERS have real code to protect and assign. |
| Where does the repo live? | An organization. docs/github-setup.md also explains what changes for a personal repository. |
| How far does it go? | Files only. No CI, no setup scripts, nothing that changes GitHub settings. Settings that cannot be files are documented as manual steps. |
| Site stack | Python with FastAPI, plus a static HTML/JS page. This gives two ownership zones (backend and frontend) and one dependency ecosystem (pip) for Dependabot to watch. |
| Version control | `git init -b main`, local only, no remote. |

## Objectives and the files that satisfy them

| Objective in starter.md | Artifact |
|---|---|
| Add a simple ruleset and configuration to restrict repository content | .github/rulesets/protect-main.json |
| Communicate procedures to guide collaborators | CONTRIBUTING.md, .github/pull_request_template.md, .github/ISSUE_TEMPLATE/ |
| Assign responsibility for parts of the code to particular collaborators | .github/CODEOWNERS |
| Learn the difference between personal and organization repositories | docs/github-setup.md (comparison section) |
| Establish ground rules for a healthy collaboration environment | CODE_OF_CONDUCT.md |
| Establish a process for managing security updates | SECURITY.md, .github/dependabot.yml |

## Layout

```
intro-repo/
├── README.md
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── starter.md
├── requirements.txt
├── .gitignore
├── src/
│   ├── app.py
│   └── static/
│       ├── index.html
│       ├── app.js
│       └── styles.css
├── tests/
│   └── test_app.py
├── docs/
│   ├── github-setup.md
│   └── superpowers/specs/          (this design doc)
└── .github/
    ├── CODEOWNERS
    ├── dependabot.yml
    ├── pull_request_template.md
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   ├── activity_request.md
    │   └── config.yml
    └── rulesets/
        └── protect-main.json
```

## Component specs

### Site (src/, tests/, requirements.txt, README.md)

Deliberately minimal. The repository is the subject, not the app.

- Data: an in-memory dictionary keyed by activity name. Each activity has a description, a schedule and a list of participant emails. Six sample activities are seeded.
- `GET /activities` returns all activities as JSON.
- `POST /activities/{activity_name}/signup?email=<email>` adds the email to the activity. An unknown activity returns 404. An email that is already signed up returns 400.
- `GET /` redirects to `/static/index.html`. Files in src/static/ are served under `/static`.
- The static page fetches `/activities` and shows each activity with its schedule and participants. Each activity has a sign-up form (one email field) that posts to the sign-up endpoint, shows the result message, and refreshes the list.
- No database, no authentication, no persistence across restarts.
- Tests (pytest with FastAPI's TestClient): listing returns the seeded activities; signing up adds the participant; a duplicate sign-up returns 400; an unknown activity returns 404; `/` redirects to the page; the page is served. A fixture restores the seed data before each test.
- requirements.txt lists fastapi, uvicorn, httpx2 (the package Starlette's TestClient now expects; plain httpx only produces a deprecation warning) and pytest, each pinned to an exact version that passes the tests. Exact pins matter because Dependabot updates pinned versions.
- README.md says what the site is, how to run it and test it, and links to CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md and docs/github-setup.md.

### .github/rulesets/protect-main.json

A branch ruleset in GitHub's ruleset JSON format, importable from the repository's Rules settings.

- Name `protect-main`, target branch, enforcement active, applies to the default branch (`~DEFAULT_BRANCH`).
- Rules: restrict deletions; block force pushes; require a pull request with 1 approving review, Code Owner review required, stale approvals dismissed when new commits are pushed, and all review conversations resolved before merge.
- Bypass list: empty. The rules apply to everyone, including organization admins.
- The exact JSON fields come from GitHub's current REST API documentation for repository rulesets, fetched when the file is built, not written from memory.

### CONTRIBUTING.md and templates

CONTRIBUTING.md is short enough to read in a few minutes. Sections:

1. Before you start: read the code of conduct; ask a maintainer to add you to the team for the area you will work on.
2. Making a change: open or pick an issue; branch from `main` using `<your-name>/<short-description>`; keep commits small and focused; open a pull request using the template; address review comments; once approved, the author squash merges and deletes the branch.
3. Running the site and tests locally (the same commands as README.md).
4. Review: a pull request needs 1 approval, and an approval from the owning team of each area it touches. A table of areas and their owning teams, matching CODEOWNERS, sits here. Authors cannot approve their own pull requests.
5. Getting help, and where to report security problems (SECURITY.md).

Pull request template: summary; linked issue (`Closes #`); how it was tested; checklist (tests pass, docs updated if behavior changed, no secrets or personal data committed).

Issue templates: `bug_report.md` (what happened, what was expected, steps to reproduce), `activity_request.md` (a new or changed activity: name, description, schedule, supervising teacher), and `config.yml` setting `blank_issues_enabled: false`.

### .github/CODEOWNERS

```
# The last matching pattern wins.
*                    @mergington-high-school/maintainers
/src/app.py          @mergington-high-school/backend
/tests/              @mergington-high-school/backend
/src/static/         @mergington-high-school/frontend
/.github/            @mergington-high-school/maintainers
/docs/               @mergington-high-school/maintainers
/SECURITY.md         @mergington-high-school/maintainers
```

The organization is `mergington-high-school` and the teams are `maintainers`, `backend` and `frontend`. Each team needs Write access to the repository for its ownership to count. requirements.txt falls under the default rule, so the maintainers review dependency updates.

### CODE_OF_CONDUCT.md

Contributor Covenant 2.1, taken from the official source (contributor-covenant.org) with its attribution kept. The enforcement contact is `conduct@mergington-high-school.example`. The `.example` domain is reserved and cannot deliver mail, so it is clearly a stand-in until replaced.

### SECURITY.md and .github/dependabot.yml

SECURITY.md sections:

- Supported versions: the latest commit on `main`.
- Reporting a vulnerability: use GitHub's private vulnerability reporting (the repository's Security tab), or write to `security@mergington-high-school.example`. Never open a public issue for a vulnerability.
- What to expect: acknowledgment within 3 business days, and updates until the problem is fixed.
- How security updates are handled:
  - Dependabot version updates run weekly for pip (configured in dependabot.yml).
  - Dependabot security updates open a pull request when a pinned dependency has a known vulnerability with a fix available (a repository setting, see docs/github-setup.md).
  - These pull requests follow the same rules as any other change: the ruleset applies and the maintainers team reviews them.
  - There is no CI, so the reviewer checks out the branch, runs the tests, and merges only if they pass.
  - Security update pull requests are reviewed within 5 business days.

dependabot.yml: `version: 2`, one `pip` entry for directory `/` with a weekly schedule.

### docs/github-setup.md

1. **Values to replace before pushing.** A table of each stand-in, what it defaults to, and where it appears: organization name and team slugs (CODEOWNERS), the conduct contact (CODE_OF_CONDUCT.md), the security contact and response times (SECURITY.md).
2. **One-time setup, in order.** Create the repository and push. Create the three teams with at least two members each, visible so they can be code owners (authors cannot approve their own pull requests, so a one-person team cannot merge its own changes). Give each team Write access to the repository. Import the ruleset and confirm it shows as active. Enable Dependabot alerts and Dependabot security updates. Enable private vulnerability reporting (GitHub documents it for public repositories only; for a private repository the email contact in SECURITY.md is the route). Confirm GitHub shows no errors on CODEOWNERS.
3. **Check that it works.** A direct push to `main` is rejected. A force push is rejected. A pull request changing src/static/ requests review from the frontend team and cannot merge without it.
4. **Personal vs organization.** A comparison covering permission levels, teams in CODEOWNERS, organization-level rulesets, and what happens to ownership when a teacher leaves.

Menu paths in step 2 and the facts in step 4 are checked against GitHub's current documentation when the file is written.

## Verification plan

- Run the tests in a throwaway virtualenv outside the repository. Start the app and confirm `/` serves the page and `/activities` returns JSON.
- Parse protect-main.json and dependabot.yml and compare their fields with GitHub's current documentation.
- Check that every CODEOWNERS pattern matches a path that exists.
- Check that relative links between the Markdown files resolve.
- Check that the Contributor Covenant's bracketed contact-method placeholder has been replaced with the conduct contact.

## Limitations

- Nothing here can be exercised against a real GitHub organization from the build machine. Ruleset and CODEOWNERS behavior rest on GitHub's documentation, and docs/github-setup.md lists the checks to run after the ruleset is imported.
- With no CI, status checks cannot be required and dependency update pull requests are tested by hand. Adding a test workflow later is the natural next step.
- The organization name, team slugs, contacts and response times are stand-ins, all listed in docs/github-setup.md.

## Out of scope

CI workflows, setup scripts, creating the organization or teams, pushing to a remote, persistence or authentication in the site, and styling beyond a basic readable page.

## Changes made while planning

These differ from the version reviewed on 2026-10-06. Each came from checking a fact the design depends on.

- .gitignore is added to the layout so virtualenvs and caches stay out of git.
- requirements.txt uses httpx2 instead of httpx. The installed Starlette marks httpx as deprecated for its TestClient and asks for httpx2. Starlette's own dependency metadata lists httpx2, and PyPI shows it is published by the author of httpx.
- The site has six tests, not three. The 404 for an unknown activity, the root redirect and the static page are covered too, because the design requires those behaviors.
- CONTRIBUTING.md includes a table of areas and owning teams.
- docs/github-setup.md creates the repository first, because teams cannot be given access to a repository that does not exist. It also says that private vulnerability reporting is documented for public repositories only, that rulesets in private repositories need a paid plan, and that with no bypass list nobody can rename or delete `main`. It lists the GitHub documentation pages it was checked against.
