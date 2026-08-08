"""FastAPI application entry point for TriageBot.

Wires together the persistence layer, the triage engine, and the HTTP API,
and serves a tiny static web UI at ``/``.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import __version__, repository, triage
from app.database import init_db
from app.schemas import (
    BatchTriageItem,
    Issue,
    IssueIn,
    IssueUpdate,
    TriageSuggestion,
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Ensure the database schema exists before serving requests."""
    init_db()
    yield


app = FastAPI(
    title="TriageBot API",
    version=__version__,
    description=(
        "An incoming-issue triage assistant: suggests severity, labels, and "
        "the likely owner for developer issues (Track B: Developer Productivity)."
    ),
    lifespan=lifespan,
)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe used by CI and by anyone bringing the app up."""
    return {"status": "ok", "version": __version__}


@app.post("/triage", response_model=TriageSuggestion, tags=["triage"])
def triage_preview(payload: IssueIn) -> TriageSuggestion:
    """Triage an issue *without* saving it — the core assistant feature."""
    result = triage.triage(payload.title, payload.body)
    return TriageSuggestion(
        severity=result.severity,
        labels=result.labels,
        owner=result.owner,
        reason=result.reason,
    )


@app.post("/triage/batch", response_model=list[BatchTriageItem], tags=["triage"])
def triage_batch(payload: list[IssueIn]) -> list[BatchTriageItem]:
    """Triage many incoming issues at once (e.g. a backlog import)."""
    items: list[BatchTriageItem] = []
    for issue in payload:
        result = triage.triage(issue.title, issue.body)
        items.append(
            BatchTriageItem(
                title=issue.title,
                severity=result.severity,
                labels=result.labels,
                owner=result.owner,
                reason=result.reason,
            )
        )
    return items


@app.post("/issues", response_model=Issue, status_code=201, tags=["issues"])
def create_issue(payload: IssueIn) -> Issue:
    """Triage an issue and persist it."""
    result = triage.triage(payload.title, payload.body)
    issue = repository.create_issue(
        title=payload.title,
        body=payload.body,
        severity=result.severity,
        labels=result.labels,
        owner=result.owner,
        reason=result.reason,
    )
    return Issue(**issue)


@app.get("/issues", response_model=list[Issue], tags=["issues"])
def list_issues() -> list[Issue]:
    """Return all stored issues, newest first."""
    return [Issue(**row) for row in repository.list_issues()]


@app.get("/issues/{issue_id}", response_model=Issue, tags=["issues"])
def get_issue(issue_id: int) -> Issue:
    issue = repository.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=404, detail="Issue not found")
    return Issue(**issue)


@app.patch("/issues/{issue_id}", response_model=Issue, tags=["issues"])
def update_issue(issue_id: int, payload: IssueUpdate) -> Issue:
    """Update an issue. If title/body change, re-run triage automatically."""
    existing = repository.get_issue(issue_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Issue not found")

    severity = labels = owner = reason = None
    if payload.title is not None or payload.body is not None:
        new_title = payload.title if payload.title is not None else existing["title"]
        new_body = payload.body if payload.body is not None else existing["body"]
        result = triage.triage(new_title, new_body)
        severity, labels, owner, reason = (
            result.severity,
            result.labels,
            result.owner,
            result.reason,
        )

    updated = repository.update_issue(
        issue_id,
        title=payload.title,
        body=payload.body,
        severity=severity,
        labels=labels,
        owner=owner,
        reason=reason,
        status=payload.status,
    )
    return Issue(**updated)  # type: ignore[arg-type]


@app.delete("/issues/{issue_id}", status_code=204, response_class=Response, tags=["issues"])
def delete_issue(issue_id: int) -> Response:
    if not repository.delete_issue(issue_id):
        raise HTTPException(status_code=404, detail="Issue not found")
    return Response(status_code=204)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    """Serve the single-page web UI."""
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
