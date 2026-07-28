from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from ..config import settings
from ..integrations import slack
from ..models import Item, ReviewRecord, ReviewStatus
from ..store import Store
from . import classify as classify_mod
from . import dedupe

logger = logging.getLogger(__name__)


@dataclass
class PollResult:
    started_at: datetime
    finished_at: datetime
    sources: dict[str, dict]   # source_id -> {fetched, new, amended, errors}
    drafts_created: int
    amendments: int

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "sources": self.sources,
            "drafts_created": self.drafts_created,
            "amendments": self.amendments,
        }


async def _safe_fetch(mod) -> tuple[str, list[Item], Optional[str]]:
    try:
        items = await mod.fetch()
        return mod.SOURCE_ID, items, None
    except Exception as exc:  # noqa: BLE001 — pollers must never crash the loop
        logger.warning("source %s failed: %s", mod.SOURCE_ID, exc)
        return mod.SOURCE_ID, [], str(exc)


async def run_once(store: Optional[Store] = None) -> PollResult:
    from ..sources import ALL_SOURCES

    store = store or Store()
    started = datetime.utcnow()
    enabled = settings.enabled_source_ids

    selected = [m for m in ALL_SOURCES if (enabled is None or m.SOURCE_ID in enabled)]
    fetched = await asyncio.gather(*(_safe_fetch(m) for m in selected))

    src_stats: dict[str, dict] = {}
    drafts_created = 0
    amendments = 0
    seen_ids: set[str] = set()

    for source_id, items, err in fetched:
        s = {"fetched": len(items), "new": 0, "amended": 0, "errors": err}
        for it in items:
            if it.id in seen_ids:
                continue  # cross-source ID collision — first one wins
            seen_ids.add(it.id)
            prev = store.get_item(it.id)
            is_new, prev_hash = store.upsert_item(it)
            if is_new:
                s["new"] += 1
                draft = await classify_mod.classify(it)
                rec = ReviewRecord(
                    item_id=it.id,
                    draft=draft,
                    status=ReviewStatus.PENDING,
                    updated_at=datetime.utcnow(),
                )
                store.upsert_review(rec)
                slack.post_draft_for_review(it, draft, store)
                drafts_created += 1
            elif prev_hash and prev:
                diff = dedupe.diff_items(prev, it)
                if diff:
                    s["amended"] += 1
                    amendments += 1
                    store.record_amendment(it.id, prev_hash, it.content_hash, diff)
                    slack.post_amendment(it, diff, store)
        src_stats[source_id] = s

    return PollResult(
        started_at=started,
        finished_at=datetime.utcnow(),
        sources=src_stats,
        drafts_created=drafts_created,
        amendments=amendments,
    )
