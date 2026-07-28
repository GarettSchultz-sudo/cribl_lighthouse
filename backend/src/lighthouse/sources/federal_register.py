from __future__ import annotations

from ..models import Item, Kind
from ._common import http_client, make_item, parse_date

SOURCE_ID = "federal_register"
DASHBOARD_ABBR = "FR"
DASHBOARD_NAME = "Federal Register API"
DASHBOARD_URL = "federalregister.gov/api/v1 · term=FedRAMP"
MODE = "ok"

API_URL = "https://www.federalregister.gov/api/v1/documents.json"


def _is_fedramp_relevant(title: str, abstract: str) -> bool:
    """Drop Privacy Act / system-of-records hits that mention FedRAMP only
    incidentally. Keep entries where FedRAMP shows up prominently."""
    blob = f"{title}\n{abstract}".lower()
    if "fedramp" not in blob:
        return False
    # Easy reject: Privacy Act SORN entries where FedRAMP is a passing reference.
    title_l = title.lower()
    if "privacy act" in title_l or "system of records" in title_l:
        # Keep only if FedRAMP is in the title itself.
        return "fedramp" in title_l
    # Otherwise: keep if FedRAMP appears in title OR multiple times in abstract.
    if "fedramp" in title_l:
        return True
    return blob.count("fedramp") >= 2


async def fetch() -> list[Item]:
    params = {
        "conditions[term]": "FedRAMP",
        "per_page": 100,
        "order": "newest",
    }
    async with http_client() as cx:
        r = await cx.get(API_URL, params=params)
        r.raise_for_status()
        data = r.json()

    out: list[Item] = []
    for d in data.get("results", []):
        title = (d.get("title") or "").strip()
        abstract = d.get("abstract") or ""
        if not _is_fedramp_relevant(title, abstract):
            continue
        doc_num = d.get("document_number") or d.get("citation") or ""
        out.append(
            make_item(
                source_id=SOURCE_ID,
                item_id=f"FR-{doc_num}",
                kind=Kind.REG,
                title=title,
                summary=abstract,
                url=d.get("html_url", ""),
                published=parse_date(d.get("publication_date")),
                deadline=parse_date(d.get("comments_close_on")) or parse_date(d.get("effective_on")),
                needs_action=bool(d.get("comments_close_on")),
                raw={
                    "agencies": [a.get("name") for a in d.get("agencies", [])],
                    "type": d.get("type"),
                    "effective_on": d.get("effective_on"),
                },
            )
        )
    return out
