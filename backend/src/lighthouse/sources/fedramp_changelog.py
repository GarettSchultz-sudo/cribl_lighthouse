from __future__ import annotations

import re

import feedparser

from ..models import Item, Kind
from ._common import http_client, make_item, parse_date

SOURCE_ID = "fedramp_changelog"
DASHBOARD_ABBR = "CHG"
DASHBOARD_NAME = "FedRAMP Changelog"
DASHBOARD_URL = "fedramp.gov/changelog/rss.xml"
MODE = "api"

FEED_URL = "https://www.fedramp.gov/changelog/rss.xml"

_CHG_ID_RE = re.compile(r"/changelog/([0-9]+)")


async def fetch() -> list[Item]:
    async with http_client() as cx:
        r = await cx.get(FEED_URL)
        r.raise_for_status()
        body = r.text

    parsed = feedparser.parse(body)
    out: list[Item] = []
    for e in parsed.entries:
        link = e.get("link", "")
        m = _CHG_ID_RE.search(link)
        cid = f"CHG-{m.group(1).zfill(4)}" if m else f"CHG-{abs(hash(link)) % 10_000:04d}"
        out.append(
            make_item(
                source_id=SOURCE_ID,
                item_id=cid,
                kind=Kind.CHANGELOG,
                title=e.get("title", "").strip(),
                summary=e.get("summary", "") or e.get("description", ""),
                url=link,
                published=parse_date(e.get("published") or e.get("updated")),
                raw={"feed_id": e.get("id", "")},
            )
        )
    return out
