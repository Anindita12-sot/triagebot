# TriageBot Project Constitution

This constitution defines the non-negotiable principles that guide every human
and AI contribution to TriageBot. It is the highest-level agent rules file for
the project. When any other instruction conflicts with this document, this
document wins.

## 1. Purpose

TriageBot is a **developer-productivity tool** (Hackathon Track B). It reads an
incoming issue and suggests a **severity**, one or more **labels**, and a
**likely owner**, always with a human-readable explanation. It exists to make
issue triage faster and more consistent for software teams.

## 2. Core Principles

1. **Explainability over magic.** Every triage decision must return a `reason`.
   No decision may be a black box. This is why the engine is rule-based, not an
   opaque model.
2. **Runs anywhere, no secrets.** The tool must run offline with no API keys.
   Never introduce a hard dependency on an external paid service.
3. **Deterministic and testable.** The same input always yields the same
   output. Every behavioural change to the engine ships with a test.
4. **Small, focused changes.** Make the smallest change that fully solves the
   problem. Avoid unrelated refactors in the same change.
5. **The gate is sacred.** Code only merges when lint passes and all tests are
   green in CI. A red pipeline is a broken build.

## 3. Architecture Rules

- Keep the layering clean: `triage` (pure logic) → `repository` (data access)
  → `main` (HTTP). Business rules live in `app/triage.py`, never in routes.
- `app/triage.py` must remain free of I/O, framework, and network imports so it
  stays trivially unit-testable.
- All triage tuning happens by editing the keyword tables in `app/triage.py`,
  and every new keyword rule gets a matching test.

## 4. Quality Bar

- Validate inputs at the API boundary (Pydantic schemas); fail with clear 4xx
  errors, never a 500 for user error.
- Public functions have docstrings explaining intent, not mechanics.
- No commented-out code, no debug prints in committed code.

## 5. Definition of Done

A change is done only when:

- [ ] `ruff check .` passes with no findings.
- [ ] `pytest` passes (100% of tests green).
- [ ] New/changed behaviour is covered by a test.
- [ ] Docstrings and `README.md` reflect any new behaviour.
