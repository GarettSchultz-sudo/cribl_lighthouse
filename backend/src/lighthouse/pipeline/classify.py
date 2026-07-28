from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from typing import Any

from ..config import settings
from ..models import Briefing, Draft, EpicDraft, Item, StoryDraft

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are a compliance and project-management assistant for a FedRAMP CSP.
Given one regulatory item (FedRAMP notice, RFC, Federal Register entry, or repo change),
produce Jira-ready Epic + Stories grouped by urgency phase.

Rules:
- Phases must be one of: Immediate, Short-Term, Full Implementation, Grace Period.
- Acceptance criteria: 3-5 specific, verifiable bullets per Story.
- Priority must be one of: Highest, High, Medium, Low.
- Labels are lowercase kebab-case.
- Due dates must be ISO YYYY-MM-DD and chronologically reasonable given today's date and the item's deadline.
- Keep language action-oriented and non-technical enough for cross-functional teams.
- Do NOT invent dates not implied by the source. If unknown, omit the due_date field.
- Output ONLY valid JSON conforming to the schema below. No prose, no markdown fences."""


SCHEMA = {
    "type": "object",
    "required": ["epic", "stories", "briefing"],
    "properties": {
        "epic": {
            "type": "object",
            "required": ["summary", "description", "labels"],
            "properties": {
                "summary": {"type": "string"},
                "description": {"type": "string"},
                "labels": {"type": "array", "items": {"type": "string"}},
                "due_date": {"type": "string"},
                "priority": {"type": "string"},
            },
        },
        "stories": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["summary", "description", "acceptance_criteria", "priority", "labels", "phase"],
                "properties": {
                    "summary": {"type": "string"},
                    "description": {"type": "string"},
                    "acceptance_criteria": {"type": "array", "items": {"type": "string"}},
                    "priority": {"type": "string"},
                    "labels": {"type": "array", "items": {"type": "string"}},
                    "due_date": {"type": "string"},
                    "phase": {"type": "string"},
                },
            },
        },
        "briefing": {
            "type": "object",
            "required": ["plain_summary", "consequences", "phase_briefings"],
            "properties": {
                "plain_summary": {"type": "string"},
                "consequences": {"type": "string"},
                "phase_briefings": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                },
            },
        },
    },
}


def _user_prompt(item: Item) -> str:
    return (
        f"Today is {date.today().isoformat()}.\n\n"
        f"Source: {item.source_id}\n"
        f"ID: {item.id}\n"
        f"Kind: {item.kind.value}\n"
        f"Title: {item.title}\n"
        f"Published: {item.published.isoformat() if item.published else 'unknown'}\n"
        f"Deadline: {item.deadline.isoformat() if item.deadline else 'unknown'}\n"
        f"URL: {item.url}\n\n"
        f"Body:\n{item.summary}\n\n"
        "Produce the JSON object now."
    )


async def classify(item: Item) -> Draft:
    if settings.llm_enabled:
        try:
            return await _classify_claude(item)
        except Exception as exc:  # pragma: no cover - exercised live only
            logger.warning("Claude classify failed, falling back to mock: %s", exc)
    return _classify_mock(item)


async def _classify_claude(item: Item) -> Draft:
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    msg = await client.messages.create(
        model=settings.anthropic_model,
        max_tokens=4096,
        system=SYSTEM_PROMPT + "\n\nJSON Schema:\n" + json.dumps(SCHEMA),
        messages=[{"role": "user", "content": _user_prompt(item)}],
    )
    text = "".join(block.text for block in msg.content if getattr(block, "type", None) == "text")
    payload = _extract_json(text)
    return _to_draft(item, payload, classifier="claude")


def _classify_mock(item: Item) -> Draft:
    """Deterministic stub. Shape matches a real classifier; content is templated
    from the item itself so the dashboard demo is plausible without an API key."""
    today = date.today()
    deadline = item.deadline
    epic_due = deadline or (today + timedelta(days=90))

    phases = []
    if deadline:
        days = (deadline - today).days
        if days <= 30:
            phases.append(("Immediate", today + timedelta(days=14)))
        if days <= 90:
            phases.append(("Short-Term", deadline - timedelta(days=14) if deadline else today + timedelta(days=60)))
        phases.append(("Full Implementation", deadline))
        phases.append(("Grace Period", deadline + timedelta(days=90) if deadline else None))
    else:
        phases.append(("Short-Term", today + timedelta(days=60)))
        phases.append(("Full Implementation", today + timedelta(days=120)))

    stories: list[StoryDraft] = []
    base_labels = ["fedramp", item.kind.value.lower(), item.id.lower()]
    for phase, due in phases:
        stories.append(
            StoryDraft(
                summary=f"[{phase}] Action plan for {item.id}",
                description=(
                    f"Stub story produced by the LLM-mock classifier (no Anthropic API key configured).\n\n"
                    f"Source: {item.url}\n\n"
                    f"Item summary:\n{item.summary[:400]}"
                ),
                acceptance_criteria=[
                    f"Owner assigned for {item.id} {phase.lower()} workstream",
                    f"Gap identified between current state and {item.id} requirements",
                    "Status reviewed in weekly compliance sync",
                ],
                priority="Highest" if phase == "Immediate" else "High",
                labels=base_labels + [phase.lower().replace(" ", "-")],
                due_date=due,
                phase=phase,
            )
        )

    epic = EpicDraft(
        summary=f"Compliance response: {item.title[:120]}",
        description=(
            f"Auto-generated by Lighthouse (mock classifier).\n\n"
            f"Item: {item.id}\nKind: {item.kind.value}\nURL: {item.url}\n\n"
            f"Summary:\n{item.summary[:1200]}"
        ),
        labels=base_labels + ["compliance"],
        due_date=epic_due,
        priority="Highest" if item.state.value in ("soon", "overdue") else "High",
    )
    briefing = Briefing(
        plain_summary=item.summary[:300] or item.title,
        consequences="Mock consequences — wire ANTHROPIC_API_KEY for real analysis.",
        phase_briefings={p: f"Mock briefing for {p} phase of {item.id}." for p, _ in phases},
    )
    return Draft(
        item_id=item.id,
        epic=epic,
        stories=stories,
        briefing=briefing,
        classifier="mock",
        created_at=datetime.utcnow(),
    )


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"no JSON object in response: {text[:200]}")
    return json.loads(text[start : end + 1])


def _to_draft(item: Item, payload: dict[str, Any], classifier: str) -> Draft:
    def _date(d: Any) -> date | None:
        if not d:
            return None
        try:
            return date.fromisoformat(str(d)[:10])
        except ValueError:
            return None

    epic_p = payload["epic"]
    epic = EpicDraft(
        summary=epic_p["summary"],
        description=epic_p["description"],
        labels=epic_p.get("labels", []),
        due_date=_date(epic_p.get("due_date")),
        priority=epic_p.get("priority", "High"),
    )
    stories = [
        StoryDraft(
            summary=s["summary"],
            description=s["description"],
            acceptance_criteria=s.get("acceptance_criteria", []),
            priority=s.get("priority", "Medium"),
            labels=s.get("labels", []),
            due_date=_date(s.get("due_date")),
            phase=s["phase"],
        )
        for s in payload["stories"]
    ]
    briefing = Briefing(
        plain_summary=payload["briefing"]["plain_summary"],
        consequences=payload["briefing"]["consequences"],
        phase_briefings=payload["briefing"]["phase_briefings"],
    )
    return Draft(
        item_id=item.id,
        epic=epic,
        stories=stories,
        briefing=briefing,
        classifier=classifier,
        created_at=datetime.utcnow(),
    )
