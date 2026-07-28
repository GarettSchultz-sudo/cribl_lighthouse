from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx

from ..config import settings
from ..models import Draft, Item, ReviewRecord
from ..store import Store

logger = logging.getLogger(__name__)


def _outbox_dir() -> Path:
    return settings.outbox_root / "slack"


def _write_outbox(name: str, body: dict[str, Any]) -> str:
    p = _outbox_dir() / f"{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}_{name}.json"
    p.write_text(json.dumps(body, indent=2, default=str))
    return str(p)


def _build_review_blocks(item: Item, draft: Draft) -> list[dict]:
    phases = sorted({s.phase for s in draft.stories})
    story_lines = []
    for phase in phases:
        story_lines.append(f"*{phase}*")
        for s in draft.stories:
            if s.phase == phase:
                due = s.due_date.isoformat() if s.due_date else "—"
                story_lines.append(f"  • {s.summary}  _({s.priority}, due {due})_")

    state_emoji = {"overdue": ":rotating_light:", "soon": ":warning:", "open": ":memo:", "closed": ":white_check_mark:"}.get(item.state.value, ":memo:")

    return [
        {"type": "header", "text": {"type": "plain_text", "text": f"{state_emoji} {item.id}: review draft"}},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*<{item.url}|{item.title}>*\n{draft.briefing.plain_summary[:500]}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Source*\n{item.source_id}"},
                {"type": "mrkdwn", "text": f"*Deadline*\n{item.deadline.isoformat() if item.deadline else '—'}"},
                {"type": "mrkdwn", "text": f"*Classifier*\n{draft.classifier}"},
                {"type": "mrkdwn", "text": f"*Stories*\n{len(draft.stories)}"},
            ],
        },
        {"type": "section", "text": {"type": "mrkdwn", "text": "\n".join(story_lines)[:2900]}},
        {
            "type": "actions",
            "block_id": f"lh:{item.id}",
            "elements": [
                {"type": "button", "style": "primary", "text": {"type": "plain_text", "text": "Approve → Jira"}, "value": f"approve:{item.id}", "action_id": "lh_approve"},
                {"type": "button", "text": {"type": "plain_text", "text": "Edit"}, "value": f"edit:{item.id}", "action_id": "lh_edit"},
                {"type": "button", "style": "danger", "text": {"type": "plain_text", "text": "Skip"}, "value": f"skip:{item.id}", "action_id": "lh_skip"},
            ],
        },
    ]


def post_draft_for_review(item: Item, draft: Draft, store: Store) -> None:
    body = {
        "channel": settings.slack_review_channel,
        "text": f"{item.id}: review draft",
        "blocks": _build_review_blocks(item, draft),
    }
    if not settings.slack_enabled:
        path = _write_outbox(f"draft_{item.id}", body)
        logger.info("Slack disabled — wrote draft to %s", path)
        return

    with httpx.Client(timeout=10.0) as cx:
        r = cx.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {settings.slack_bot_token}", "Content-Type": "application/json; charset=utf-8"},
            json=body,
        )
    data = r.json()
    if not data.get("ok"):
        logger.error("Slack postMessage failed: %s", data)
        _write_outbox(f"failed_draft_{item.id}", {"request": body, "response": data})
        return
    rec = store.get_review(item.id)
    if rec:
        rec.slack_ts = data.get("ts")
        store.upsert_review(rec)


def post_amendment(item: Item, diff: dict, store: Store) -> None:
    rec = store.get_review(item.id)
    body = {
        "channel": settings.slack_review_channel,
        "text": f"{item.id} amended",
        "thread_ts": rec.slack_ts if rec and rec.slack_ts else None,
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f":pencil2: *{item.id}* was amended at the source."}},
            {"type": "section", "text": {"type": "mrkdwn", "text": "```" + json.dumps(diff, indent=2, default=str)[:2800] + "```"}},
        ],
    }
    if not settings.slack_enabled:
        _write_outbox(f"amend_{item.id}", body)
        return
    with httpx.Client(timeout=10.0) as cx:
        cx.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
            json=body,
        )


def post_jira_link(item: Item, epic_key: str, story_keys: list[str], thread_ts: Optional[str]) -> None:
    body = {
        "channel": settings.slack_review_channel,
        "text": f"{item.id} → Jira",
        "thread_ts": thread_ts,
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f":white_check_mark: *{item.id}* approved → Jira *{epic_key}* with {len(story_keys)} stories."}},
        ],
    }
    if not settings.slack_enabled:
        _write_outbox(f"jiralink_{item.id}", body)
        return
    with httpx.Client(timeout=10.0) as cx:
        cx.post(
            "https://slack.com/api/chat.postMessage",
            headers={"Authorization": f"Bearer {settings.slack_bot_token}"},
            json=body,
        )


def verify_signature(timestamp: str, body: bytes, signature: str) -> bool:
    """Slack request signature check. Used by the interactivity endpoint."""
    import hashlib
    import hmac
    import time

    if not settings.slack_signing_secret:
        return False  # never accept signed requests when not configured
    if abs(time.time() - int(timestamp)) > 60 * 5:
        return False
    base = f"v0:{timestamp}:".encode() + body
    digest = hmac.new(settings.slack_signing_secret.encode(), base, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"v0={digest}", signature)
