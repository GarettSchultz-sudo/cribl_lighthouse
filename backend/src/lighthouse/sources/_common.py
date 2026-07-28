from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, timezone
from typing import Optional

import httpx
from dateutil import parser as dateparser

from ..models import Item, Kind, State

DEFAULT_TIMEOUT = httpx.Timeout(20.0, connect=10.0)
USER_AGENT = "cribl-lighthouse/0.1 (+https://github.com/)"


def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        timeout=DEFAULT_TIMEOUT,
        headers={"User-Agent": USER_AGENT, "Accept": "*/*"},
        follow_redirects=True,
    )


def parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    try:
        return dateparser.parse(s).date()
    except (ValueError, TypeError):
        return None


def now_utc() -> datetime:
    return datetime.now(tz=timezone.utc).replace(tzinfo=None)


def content_hash(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update((p or "").encode("utf-8", errors="replace"))
        h.update(b"\x1e")
    return h.hexdigest()[:16]


_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(s: str) -> str:
    return _TAG_RE.sub("", s or "").strip()


def derive_state(deadline: Optional[date], today: Optional[date] = None) -> State:
    if not deadline:
        return State.OPEN
    today = today or date.today()
    days = (deadline - today).days
    if days < 0:
        return State.OVERDUE
    if days <= 21:
        return State.SOON
    return State.OPEN


def make_item(
    *,
    source_id: str,
    item_id: str,
    kind: Kind,
    title: str,
    summary: str,
    url: str,
    published: Optional[date],
    deadline: Optional[date] = None,
    impact_areas: Optional[list[str]] = None,
    needs_action: bool = True,
    raw: Optional[dict] = None,
    today: Optional[date] = None,
) -> Item:
    now = now_utc()
    h = content_hash(title, summary, url, deadline.isoformat() if deadline else "")
    return Item(
        id=item_id,
        kind=kind,
        title=title.strip(),
        summary=strip_html(summary)[:1500],
        published=published,
        deadline=deadline,
        state=derive_state(deadline, today=today),
        impact_areas=impact_areas or [],
        url=url,
        needs_action=needs_action,
        source_id=source_id,
        content_hash=h,
        first_seen=now,
        last_seen=now,
        raw=raw or {},
    )
