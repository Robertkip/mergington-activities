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
