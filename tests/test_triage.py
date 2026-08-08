"""Unit tests for the rule-based triage engine."""

from __future__ import annotations

import pytest

from app.triage import (
    DEFAULT_LABEL,
    DEFAULT_OWNER,
    DEFAULT_SEVERITY,
    VALID_SEVERITIES,
    triage,
)


def test_urgent_beats_high():
    result = triage("Critical security outage in production", "everything is down")
    assert result.severity == "urgent"


def test_high_severity_from_crash():
    result = triage("App crashes on startup")
    assert result.severity == "high"
    assert "bug" in result.labels


def test_low_severity_typo():
    result = triage("Fix typo in README")
    assert result.severity == "low"
    assert "documentation" in result.labels


def test_default_severity_when_nothing_matches():
    result = triage("Please look at this when you can")
    assert result.severity == DEFAULT_SEVERITY


def test_default_label_when_nothing_matches():
    result = triage("Random unclassifiable note")
    assert result.labels == [DEFAULT_LABEL]


def test_multiple_labels_attached():
    result = triage("Bug: docs example crashes", "the readme example throws an error")
    assert "bug" in result.labels
    assert "documentation" in result.labels


def test_owner_routing_frontend():
    result = triage("CSS button layout broken on mobile", "the UI page is misaligned")
    assert result.owner == "frontend-team"


def test_owner_routing_backend_from_api():
    result = triage("API endpoint returns 500", "server error on the database query")
    assert result.owner == "backend-team"


def test_owner_falls_back_to_label_default():
    # No owner keyword, but labeled documentation -> docs-team via label default.
    result = triage("Improve tutorial wording")
    assert result.owner in ("docs-team", DEFAULT_OWNER)


def test_reason_is_explainable():
    result = triage("Critical crash in API", "server 500 error")
    assert "severity=" in result.reason
    assert "labels:" in result.reason
    assert "owner=" in result.reason


@pytest.mark.parametrize(
    "title",
    ["", "asdf", "add new feature", "urgent outage", "typo"],
)
def test_severity_always_valid(title):
    assert triage(title or "x").severity in VALID_SEVERITIES
