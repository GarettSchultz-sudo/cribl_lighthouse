from __future__ import annotations

import base64
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx

from ..config import settings
from ..models import Draft, Item

logger = logging.getLogger(__name__)


def _outbox_dir() -> Path:
    return settings.outbox_root / "jira"


def _write_outbox(name: str, body: dict[str, Any]) -> str:
    p = _outbox_dir() / f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{name}.json"
    p.write_text(json.dumps(body, indent=2, default=str))
    return str(p)


def _auth_header() -> dict[str, str]:
    raw = f"{settings.jira_email}:{settings.jira_api_token}".encode()
    return {"Authorization": "Basic " + base64.b64encode(raw).decode(), "Content-Type": "application/json"}


def _epic_payload(item: Item, draft: Draft) -> dict:
    fields: dict[str, Any] = {
        "project": {"key": settings.jira_project_key},
        "summary": draft.epic.summary[:240],
        "description": draft.epic.description,
        "issuetype": {"name": settings.jira_epic_issue_type},
        "labels": draft.epic.labels,
        "priority": {"name": draft.epic.priority},
    }
    if draft.epic.due_date:
        fields["duedate"] = draft.epic.due_date.isoformat()
    return {"fields": fields}


def _story_payload(item: Item, story, epic_key: str) -> dict:
    description = (
        story.description
        + "\n\n*Acceptance criteria*\n"
        + "\n".join(f"- {ac}" for ac in story.acceptance_criteria)
    )
    fields: dict[str, Any] = {
        "project": {"key": settings.jira_project_key},
        "summary": story.summary[:240],
        "description": description,
        "issuetype": {"name": settings.jira_story_issue_type},
        "labels": story.labels + [f"phase-{story.phase.lower().replace(' ', '-')}"],
        "priority": {"name": story.priority},
    }
    if story.due_date:
        fields["duedate"] = story.due_date.isoformat()
    # Epic link encoded as a parent reference (modern Jira). Real instances
    # may need a custom field id; exposing both forms is intentional.
    fields["parent"] = {"key": epic_key}
    return {"fields": fields}


def create_epic_and_stories(item: Item, draft: Draft) -> tuple[str, list[str]]:
    if not settings.jira_enabled:
        epic_path = _write_outbox(f"epic_{item.id}", _epic_payload(item, draft))
        story_paths = [
            _write_outbox(f"story_{item.id}_{i}", _story_payload(item, s, "STUB-EPIC"))
            for i, s in enumerate(draft.stories)
        ]
        logger.info("Jira disabled — wrote epic to %s and %d stories", epic_path, len(story_paths))
        return f"STUB-{item.id}", [f"STUB-{item.id}-{i}" for i, _ in enumerate(draft.stories)]

    base = settings.jira_base_url.rstrip("/")
    with httpx.Client(timeout=20.0, headers=_auth_header()) as cx:
        r = cx.post(f"{base}/rest/api/3/issue", json=_epic_payload(item, draft))
        r.raise_for_status()
        epic_key = r.json()["key"]

        story_keys: list[str] = []
        for s in draft.stories:
            r = cx.post(f"{base}/rest/api/3/issue", json=_story_payload(item, s, epic_key))
            r.raise_for_status()
            story_keys.append(r.json()["key"])

    return epic_key, story_keys


def get_status_map(epic_keys: list[str]) -> dict[str, str]:
    """For Slice 3: pull current status for each epic + descendants. Stub for now."""
    if not settings.jira_enabled or not epic_keys:
        return {}
    return {}  # implemented in Slice 3
