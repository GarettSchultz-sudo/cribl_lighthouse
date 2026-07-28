from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Kind(str, Enum):
    NOTICE = "NOTICE"
    RFC = "RFC"
    REG = "REG"
    CHANGELOG = "CHANGELOG"
    OTHER = "OTHER"


class State(str, Enum):
    OPEN = "open"
    SOON = "soon"
    OVERDUE = "overdue"
    CLOSED = "closed"


class Item(BaseModel):
    """One normalized record. Matches the dashboard's ITEMS shape, with
    extra backend-only fields (content_hash, source_id, raw)."""

    id: str
    kind: Kind
    title: str
    summary: str = ""
    published: Optional[date] = None
    deadline: Optional[date] = None
    state: State = State.OPEN
    impact_areas: list[str] = Field(default_factory=list)
    url: str = ""
    needs_action: bool = True

    source_id: str
    content_hash: str
    first_seen: datetime
    last_seen: datetime
    raw: dict[str, Any] = Field(default_factory=dict)

    def to_dashboard(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind.value,
            "title": self.title,
            "summary": self.summary,
            "published": self.published.isoformat() if self.published else None,
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "state": self.state.value,
            "impactAreas": self.impact_areas,
            "url": self.url,
            "needsAction": self.needs_action,
        }


class StoryDraft(BaseModel):
    summary: str
    description: str
    acceptance_criteria: list[str]
    priority: str  # Highest | High | Medium | Low
    labels: list[str]
    due_date: Optional[date] = None
    phase: str  # Immediate | Short-Term | Full Implementation | Grace Period


class EpicDraft(BaseModel):
    summary: str
    description: str
    labels: list[str]
    due_date: Optional[date] = None
    priority: str = "Highest"


class Briefing(BaseModel):
    plain_summary: str
    consequences: str
    phase_briefings: dict[str, str]


class Draft(BaseModel):
    """LLM output for one item — what would become a Jira Epic + Stories."""

    item_id: str
    epic: EpicDraft
    stories: list[StoryDraft]
    briefing: Briefing
    classifier: str  # "claude" | "mock"
    created_at: datetime


class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    SKIPPED = "skipped"
    AMENDED = "amended"


class ReviewRecord(BaseModel):
    item_id: str
    draft: Draft
    status: ReviewStatus = ReviewStatus.PENDING
    slack_ts: Optional[str] = None
    jira_epic_key: Optional[str] = None
    jira_story_keys: list[str] = Field(default_factory=list)
    updated_at: datetime
