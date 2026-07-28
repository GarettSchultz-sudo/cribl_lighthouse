from __future__ import annotations

import re

from ..models import Item, Kind
from ._common import http_client, make_item, parse_date

SOURCE_ID = "fedramp_community"
DASHBOARD_ABBR = "GH"
DASHBOARD_NAME = "FedRAMP Community (RFC threads)"
DASHBOARD_URL = "api.github.com · FedRAMP/community"
MODE = "ok"

ISSUES_URL = "https://api.github.com/repos/FedRAMP/community/issues"

_RFC_LABEL = re.compile(r"^\s*RFC[-\s]?(\d{2,4})", re.I)


async def fetch() -> list[Item]:
    params = {"state": "all", "per_page": 100, "sort": "updated"}
    async with http_client() as cx:
        r = await cx.get(ISSUES_URL, params=params)
        r.raise_for_status()
        issues = r.json()

    out: list[Item] = []
    for it in issues:
        if "pull_request" in it:
            continue
        title = it.get("title") or ""
        m = _RFC_LABEL.search(title)
        labels = [l.get("name", "") for l in it.get("labels", [])]
        m_label = next((_RFC_LABEL.search(l) for l in labels if _RFC_LABEL.search(l)), None)
        rfc_num = (m or m_label).group(1) if (m or m_label) else None
        rfc_id = f"RFC-{rfc_num.zfill(4)}" if rfc_num else f"GH-{it.get('number')}"

        out.append(
            make_item(
                source_id=SOURCE_ID,
                item_id=rfc_id,
                kind=Kind.RFC,
                title=title,
                summary=(it.get("body") or "")[:3000],
                url=it.get("html_url", ""),
                published=parse_date(it.get("created_at")),
                raw={
                    "gh_number": it.get("number"),
                    "labels": labels,
                    "state": it.get("state"),
                    "comments": it.get("comments"),
                },
            )
        )
    return out
