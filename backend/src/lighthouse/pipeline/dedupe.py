from __future__ import annotations

from typing import Optional

from ..models import Item


def diff_items(prev: Item, new: Item) -> dict:
    """Field-level diff used for amendment comments and Slack threads."""
    out: dict = {}
    for f in ("title", "summary", "deadline", "state", "url", "needs_action"):
        a = getattr(prev, f)
        b = getattr(new, f)
        if a != b:
            out[f] = {
                "from": a.isoformat() if hasattr(a, "isoformat") else a,
                "to": b.isoformat() if hasattr(b, "isoformat") else b,
            }
    if set(prev.impact_areas) != set(new.impact_areas):
        out["impact_areas"] = {"from": prev.impact_areas, "to": new.impact_areas}
    return out


def is_amendment(prev: Optional[Item], new: Item) -> bool:
    return bool(prev and prev.content_hash != new.content_hash)
