"""Pydantic request/response models (the API contract)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class IssueIn(BaseModel):
    """An incoming issue to triage or store."""

    title: str = Field(..., min_length=1, max_length=200)
    body: str = Field(default="", max_length=5000)


class IssueUpdate(BaseModel):
    """Partial update. Any field left as ``None`` is unchanged."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    body: str | None = Field(default=None, max_length=5000)
    status: str | None = Field(default=None, pattern="^(open|closed)$")


class TriageSuggestion(BaseModel):
    """The triage engine's suggestion for an issue (no persistence)."""

    severity: str
    labels: list[str]
    owner: str
    reason: str


class Issue(BaseModel):
    """A triaged issue as returned by the API."""

    id: int
    title: str
    body: str
    severity: str
    labels: list[str]
    owner: str
    reason: str
    status: str
    created_at: str


class BatchTriageItem(TriageSuggestion):
    """One result within a batch-triage response."""

    title: str
