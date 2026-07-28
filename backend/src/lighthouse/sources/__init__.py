"""Source pollers. Each module exposes:

    SOURCE_ID: str        # short id used in URLs/storage
    DASHBOARD_ABBR: str   # abbr expected by dashboard.html SOURCES array
    DASHBOARD_NAME: str
    DASHBOARD_URL: str    # display URL string (matches dashboard.html)
    MODE: str             # 'api' (needs proxy) | 'ok' (CORS-friendly)
    async fetch() -> list[Item]

The poller imports this list and iterates."""

from . import (
    fedramp_changelog,
    fedramp_community,
    fedramp_notices,
    federal_register,
    frmr,
)

ALL_SOURCES = [
    fedramp_changelog,
    fedramp_notices,
    fedramp_community,
    frmr,
    federal_register,
]
