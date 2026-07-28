from __future__ import annotations

from ..models import Item, Kind
from ._common import http_client, make_item, parse_date

SOURCE_ID = "frmr"
DASHBOARD_ABBR = "FRMR"
DASHBOARD_NAME = "Machine-Readable Standards"
DASHBOARD_URL = "github.com/FedRAMP/docs (FRMR JSON)"
MODE = "ok"

# Latest commits to FedRAMP/docs is a stable signal that the FRMR JSON changed.
COMMITS_URL = "https://api.github.com/repos/FedRAMP/docs/commits"


async def fetch() -> list[Item]:
    params = {"per_page": 50}
    async with http_client() as cx:
        r = await cx.get(COMMITS_URL, params=params)
        r.raise_for_status()
        commits = r.json()

    out: list[Item] = []
    for c in commits:
        sha = c.get("sha", "")[:8]
        msg = (c.get("commit", {}).get("message") or "").strip()
        if not msg:
            continue
        # Only surface commits that look like rule/standard changes.
        first_line = msg.splitlines()[0]
        if not any(k in first_line.lower() for k in ("frmr", "rule", "standard", "vdr", "ver", "ksi", "control")):
            continue
        out.append(
            make_item(
                source_id=SOURCE_ID,
                item_id=f"FRMR-{sha}",
                kind=Kind.OTHER,
                title=first_line[:200],
                summary=msg,
                url=c.get("html_url", ""),
                published=parse_date(c.get("commit", {}).get("author", {}).get("date")),
                needs_action=False,
                raw={"sha": c.get("sha"), "author": c.get("commit", {}).get("author", {}).get("name")},
            )
        )
    return out
