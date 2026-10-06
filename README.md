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
