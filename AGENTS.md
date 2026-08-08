# AGENTS.md

Operational instructions for AI agents (and humans) working in this repository.
Read this together with [`constitution.md`](constitution.md), which holds the
higher-level principles. Custom agents and skills are documented in
[`AGENTS_AND_SKILLS.md`](AGENTS_AND_SKILLS.md).

## Project summary

TriageBot — an incoming-issue triage assistant (Hackathon Track B: Developer
Productivity Tools). FastAPI + SQLite + a rule-based triage engine, with a small
static web UI. No external services or API keys are required.

## Repository map

| Path | What it is |
|------|-----------|
| `app/triage.py` | Pure, rule-based triage engine (severity, labels, owner). **Business logic lives here.** |
| `app/repository.py` | SQLite data-access functions for issues. |
| `app/database.py` | Connection + schema management. |
| `app/schemas.py` | Pydantic request/response models (the API contract). |
| `app/main.py` | FastAPI app, routes, static UI mount. |
| `static/index.html` | Single-page web UI. |
| `tests/` | pytest suite (`test_triage.py` = engine, `test_api.py` = HTTP). |
| `.cursor/` | Cursor rules, custom skill, and custom agent. |

## Environment setup

```bash
python -m venv .venv
# Windows:  .\.venv\Scripts\activate
# Unix:     source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Everyday commands

```bash
# Run the app locally (then open http://127.0.0.1:8000)
uvicorn app.main:app --reload

# Run the test suite
pytest

# Lint (must be clean before committing)
ruff check .

# Auto-fix trivial lint issues
ruff check . --fix
```

## Rules for making changes

1. **Follow the constitution.** Explainability, no secrets, deterministic,
   tested. See [`constitution.md`](constitution.md).
2. **Change triage behaviour only in `app/triage.py`** by editing the keyword
   tables, and add a test in `tests/test_triage.py` for the new behaviour.
3. **Keep `app/triage.py` I/O-free** — no `sqlite3`, `fastapi`, `os`, or network
   imports. It must stay a pure module.
4. **Update the API contract deliberately.** If you change a Pydantic schema in
   `app/schemas.py`, update the tests and the README.
5. **Before you finish:** run `ruff check .` and `pytest`; both must pass.

## What "green CI" means here

The GitHub Actions workflow in `.github/workflows/ci.yml` installs
`requirements-dev.txt`, runs `ruff check .`, then runs `pytest`. A change is not
complete until that workflow would pass.
