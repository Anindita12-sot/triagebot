# Agents & Skills

This document catalogs the custom **agent** and custom **skill** committed to
this repository, as required by the hackathon gate. Both are versioned in
`.cursor/` and are used to build and maintain TriageBot itself — this is a
developer-productivity project, so the tooling that maintains it is part of the
deliverable.

---

## Custom Agent: `triage-maintainer`

- **Location:** [`.cursor/agents/triage-maintainer.md`](.cursor/agents/triage-maintainer.md)
- **Role:** A focused maintenance agent that extends and reviews TriageBot's
  rule-based triage engine and API.
- **Why it exists:** TriageBot's value is *consistent, explainable* triage.
  Changes to the engine are easy to get subtly wrong (ordering of severity
  buckets, missing tests, leaking I/O into the pure logic module). This agent
  encodes the exact workflow and guardrails for making those changes safely.

**What it does**
- Reads `constitution.md` + `AGENTS.md` before acting.
- Enforces the layering rule (business logic only in `app/triage.py`, no I/O
  imports there).
- Requires a test for every behavioural change.
- Treats the change as done only when `ruff check .` and `pytest` are both green.

**Tools it may use:** Read, Grep, Glob, StrReplace, Write, Shell.

**How to invoke:** Select the `triage-maintainer` agent in Cursor, or point any
agent at `.cursor/agents/triage-maintainer.md` and follow its workflow.

---

## Custom Skill: `triage-rule-authoring`

- **Location:** [`.cursor/skills/triage-rule-authoring/SKILL.md`](.cursor/skills/triage-rule-authoring/SKILL.md)
- **Purpose:** Teaches an agent how to add or modify the severity/label/owner
  keyword tables in `app/triage.py` **safely and consistently**.
- **When it triggers:** Adding a keyword, a new severity bucket, a new label, or
  an owner-routing rule; or any request to change how issues are classified or
  routed.

**What it encodes**
- Where each rule lives and its matching semantics
  (`SEVERITY_KEYWORDS` = first-match-wins, `LABEL_KEYWORDS` = all-match,
  `OWNER_KEYWORDS` = first-match then label default).
- A step-by-step checklist that ends with "add a test" and "run ruff + pytest".
- Worked examples (e.g. adding a `performance → urgent` escalation).
- Hard rules: no I/O imports in `app/triage.py`, never drop the `reason`.

---

## How the agent and skill work together

1. A request arrives: *"Route anything mentioning 'billing' to the payments team."*
2. The **`triage-maintainer` agent** picks up the task and consults the
   **`triage-rule-authoring` skill**.
3. The skill directs it to `OWNER_KEYWORDS` in `app/triage.py`, to add a test in
   `tests/test_triage.py`, and to run the gate.
4. The agent verifies `ruff check .` and `pytest` pass before finishing.

This mirrors how the project was built and is the recommended way to evolve it.
