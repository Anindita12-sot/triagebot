---
name: triage-rule-authoring
description: >-
  Add or modify TriageBot's issue-triage rules (severity, label, and owner
  keyword tables) safely and consistently. Use when adding a new keyword,
  severity bucket, label, or owner-routing rule to app/triage.py, or when the
  user asks to change how issues are classified or routed.
---

# Triage Rule Authoring

This skill governs safe changes to TriageBot's classification engine in
`app/triage.py`. The engine is intentionally rule-based and explainable — keep
it that way.

## Where rules live

All behaviour is driven by three ordered keyword tables in `app/triage.py`:

- `SEVERITY_KEYWORDS` — most-severe first; **first match wins**.
- `LABEL_KEYWORDS` — **all matches attach** (an issue can have several labels).
- `OWNER_KEYWORDS` — first match wins; falls back to `LABEL_DEFAULT_OWNER`,
  then `DEFAULT_OWNER`.

## Workflow

Copy this checklist and track progress:

```
- [ ] 1. Identify which table the change belongs in (severity / label / owner)
- [ ] 2. Add keyword(s) as lowercase strings in the correct ordered bucket
- [ ] 3. Keep ordering intent (severity/owner are first-match-wins)
- [ ] 4. Add a test in tests/test_triage.py proving the new behaviour
- [ ] 5. Run: ruff check . && pytest  (both must pass)
```

**Step 1 — Pick the table.** Severity = how urgent. Label = what kind of work.
Owner = which team. If unsure, ask which of the three the user means.

**Step 2 — Add keywords.** Keywords are matched with a lowercase substring test
against `"{title} {body}"`. So `"api"` also matches `"apixyz"` — prefer
distinctive terms. Add to the bucket that already exists rather than creating a
new one, unless a genuinely new category is needed.

**Step 3 — Respect ordering.** In `SEVERITY_KEYWORDS` and `OWNER_KEYWORDS`,
earlier buckets beat later ones. Put more-specific/more-severe buckets first.

**Step 4 — Always add a test.** This is non-negotiable (see `constitution.md`).

```python
def test_owner_routing_new_mobile_team():
    result = triage("App freezes on Android", "the mobile client hangs")
    assert result.owner == "mobile-team"
```

**Step 5 — Verify.** Run `ruff check .` then `pytest`. Do not finish on red.

## Rules of the road

- Never add I/O (DB, network, `os`, `fastapi`) imports to `app/triage.py`.
- Never remove the `reason` from a result — every decision stays explainable.
- New owner teams should also get a sensible entry in `LABEL_DEFAULT_OWNER`
  when they map cleanly to a label.

## Example: adding a "performance → urgent" escalation

Input request: "Treat memory leaks as urgent."

1. Table: severity.
2. Add `"memory leak"` to the `"urgent"` bucket in `SEVERITY_KEYWORDS`.
3. Add a test:

```python
def test_memory_leak_is_urgent():
    assert triage("Memory leak in worker").severity == "urgent"
```

4. `ruff check . && pytest` → green.
