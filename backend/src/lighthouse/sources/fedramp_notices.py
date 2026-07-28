from __future__ import annotations

import re

import feedparser

from ..models import Item, Kind
from ._common import http_client, make_item, parse_date


_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n+", re.DOTALL)
_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_RE = re.compile(r"\*([^*]+)\*")


def _clean_markdown_for_summary(md: str, max_len: int = 600) -> str:
    """Strip YAML frontmatter and basic markdown so card bodies show real prose,
    not '---\\ntitle:...'."""
    if not md:
        return ""
    body = _FRONTMATTER_RE.sub("", md, count=1)
    body = _HEADING_RE.sub("", body)
    body = _LINK_RE.sub(r"\1", body)
    body = _BOLD_RE.sub(r"\1", body)
    body = _ITALIC_RE.sub(r"\1", body)
    # Take the first 1-2 substantive paragraphs.
    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    out = []
    total = 0
    for p in paragraphs:
        # Skip blockquotes, raw HTML lines, and image-only paragraphs
        if p.startswith(">") or p.startswith("<") or p.startswith("!["):
            continue
        out.append(p)
        total += len(p)
        if total >= max_len:
            break
    text = " ".join(out)
    if len(text) > max_len:
        text = text[: max_len - 1].rsplit(" ", 1)[0] + "…"
    return text

SOURCE_ID = "fedramp_notices"
DASHBOARD_ABBR = "NTC"
DASHBOARD_NAME = "FedRAMP Public Notices"
DASHBOARD_URL = "fedramp.gov/notices/rss.xml"
MODE = "api"

FEED_URL = "https://www.fedramp.gov/notices/rss.xml"
MARKDOWN_TEMPLATE = "https://www.fedramp.gov/notices/markdown/NTC-{n}.md"

_NTC_ID_RE = re.compile(r"/notices/(\d+)")


async def fetch() -> list[Item]:
    async with http_client() as cx:
        r = await cx.get(FEED_URL)
        r.raise_for_status()
        body = r.text

    parsed = feedparser.parse(body)
    out: list[Item] = []
    async with http_client() as cx:
        for e in parsed.entries:
            link = e.get("link", "")
            m = _NTC_ID_RE.search(link)
            n = m.group(1).zfill(4) if m else None
            nid = f"NTC-{n}" if n else f"NTC-{abs(hash(link)) % 10_000:04d}"

            summary = e.get("summary", "") or e.get("description", "")
            # Pull the markdown body for richer LLM input when available.
            md_body = ""
            if n:
                try:
                    mdr = await cx.get(MARKDOWN_TEMPLATE.format(n=n))
                    if mdr.status_code == 200:
                        md_body = mdr.text
                except httpx_error_passthrough():  # pragma: no cover
                    pass

            clean_summary = _clean_markdown_for_summary(md_body) if md_body else summary
            out.append(
                make_item(
                    source_id=SOURCE_ID,
                    item_id=nid,
                    kind=Kind.NOTICE,
                    title=e.get("title", "").strip(),
                    summary=clean_summary,
                    url=link,
                    published=parse_date(e.get("published") or e.get("updated")),
                    raw={"feed_id": e.get("id", ""), "markdown": md_body},
                )
            )
    return out


def httpx_error_passthrough():
    """Return the httpx exception base class without importing at module top
    so this stays a pure stdlib import path during tests that monkeypatch."""
    import httpx

    return httpx.HTTPError
