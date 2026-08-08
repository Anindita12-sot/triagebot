"""Explainable, rule-based issue-triage engine.

This is the heart of TriageBot (Track B: Developer Productivity Tools). Given
the free-text ``title`` and ``body`` of an incoming issue, it suggests:

  * a ``severity``  (low / medium / high / urgent)
  * one or more ``labels`` (bug / feature / docs / chore / ...)
  * a ``likely owner`` / team to route the issue to

It is intentionally rule-based rather than LLM-backed so the tool runs with
**no API keys or network access** — which keeps it fully demoable and testable
in CI. Every suggestion returns a human-readable ``reason`` so the behaviour is
transparent, auditable, and easy to unit test.

The rule tables below are the single place to tune behaviour; adding a keyword
is a one-line change with an accompanying test.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# --- Severity -------------------------------------------------------------
# Ordered most-severe first; the first matching bucket wins so "urgent"
# always beats "high", etc.
SEVERITY_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("urgent", ("urgent", "asap", "immediately", "critical", "outage", "data loss",
                "security", "vulnerability", "cve", "production down", "p0")),
    ("high", ("crash", "crashes", "error", "exception", "fails", "failing", "broken",
              "blocker", "regression", "cannot", "can't", "500", "deadline")),
    ("medium", ("bug", "issue", "slow", "performance", "improve", "refactor",
                "unexpected", "incorrect")),
    ("low", ("typo", "nit", "minor", "someday", "nice to have", "cosmetic", "cleanup")),
]

# --- Labels ---------------------------------------------------------------
# All matching labels are attached (an issue can be both "bug" and "docs").
LABEL_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("bug", ("bug", "crash", "error", "exception", "fails", "failing", "broken",
             "regression", "500", "stack trace", "traceback")),
    ("documentation", ("doc", "docs", "documentation", "readme", "typo", "comment",
                        "example", "tutorial")),
    ("enhancement", ("add", "feature", "implement", "support", "request", "would be nice",
                     "new", "enhancement")),
    ("performance", ("slow", "performance", "latency", "timeout", "memory", "cpu")),
    ("security", ("security", "vulnerability", "cve", "xss", "sql injection", "csrf",
                  "auth", "token leak")),
    ("chore", ("refactor", "cleanup", "upgrade", "bump", "dependency", "chore", "ci",
               "build")),
]

# --- Ownership routing ----------------------------------------------------
# Keyword -> owning team. First match wins; falls back to a per-label default,
# then to a global default. Mimics a lightweight CODEOWNERS-style router.
OWNER_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("frontend-team", ("ui", "css", "html", "button", "page", "layout", "react",
                        "frontend", "browser", "responsive")),
    ("backend-team", ("api", "server", "endpoint", "database", "db", "query", "500",
                      "backend", "migration")),
    ("security-team", ("security", "vulnerability", "cve", "xss", "csrf", "auth",
                       "token", "injection")),
    ("infra-team", ("ci", "pipeline", "deploy", "docker", "kubernetes", "infra",
                    "build", "workflow")),
    ("docs-team", ("doc", "docs", "documentation", "readme", "tutorial")),
]

LABEL_DEFAULT_OWNER = {
    "bug": "backend-team",
    "documentation": "docs-team",
    "enhancement": "product-team",
    "performance": "backend-team",
    "security": "security-team",
    "chore": "infra-team",
}

DEFAULT_SEVERITY = "medium"
DEFAULT_LABEL = "triage"
DEFAULT_OWNER = "maintainers"

VALID_SEVERITIES = ("low", "medium", "high", "urgent")


@dataclass(frozen=True)
class TriageResult:
    """The outcome of triaging a single issue."""

    severity: str
    labels: list[str] = field(default_factory=list)
    owner: str = DEFAULT_OWNER
    reason: str = ""


def _first_match(text: str, table: list[tuple[str, tuple[str, ...]]]) -> tuple[str, str] | None:
    """Return ``(label, matched_keyword)`` for the first bucket that matches."""
    for label, keywords in table:
        for keyword in keywords:
            if keyword in text:
                return label, keyword
    return None


def _all_matches(text: str, table: list[tuple[str, tuple[str, ...]]]) -> list[tuple[str, str]]:
    """Return every bucket that matches, preserving table order."""
    matches: list[tuple[str, str]] = []
    for label, keywords in table:
        for keyword in keywords:
            if keyword in text:
                matches.append((label, keyword))
                break
    return matches


def triage(title: str, body: str | None = None) -> TriageResult:
    """Triage a single incoming issue.

    Args:
        title: The issue title (required).
        body: Optional issue body / description.

    Returns:
        A :class:`TriageResult` with severity, labels, likely owner, and a
        short human-readable reason explaining each choice.
    """
    text = f"{title} {body or ''}".lower()

    severity_match = _first_match(text, SEVERITY_KEYWORDS)
    severity = severity_match[0] if severity_match else DEFAULT_SEVERITY

    label_matches = _all_matches(text, LABEL_KEYWORDS)
    labels = [label for label, _ in label_matches] or [DEFAULT_LABEL]

    owner_match = _first_match(text, OWNER_KEYWORDS)
    if owner_match:
        owner = owner_match[0]
        owner_reason = f"owner={owner} (matched '{owner_match[1]}')"
    else:
        owner = LABEL_DEFAULT_OWNER.get(labels[0], DEFAULT_OWNER)
        owner_reason = f"owner={owner} (routed by label '{labels[0]}')"

    reasons: list[str] = []
    if severity_match:
        reasons.append(f"severity={severity} (matched '{severity_match[1]}')")
    else:
        reasons.append(f"severity={severity} (default, no keyword matched)")
    if label_matches:
        joined = ", ".join(f"{lbl} ('{kw}')" for lbl, kw in label_matches)
        reasons.append(f"labels: {joined}")
    else:
        reasons.append(f"labels: {DEFAULT_LABEL} (default, no keyword matched)")
    reasons.append(owner_reason)

    return TriageResult(
        severity=severity,
        labels=labels,
        owner=owner,
        reason="; ".join(reasons),
    )
