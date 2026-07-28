from datetime import date, datetime

from lighthouse.models import Item, Kind, State
from lighthouse.pipeline.dedupe import diff_items


def _item(**overrides):
    base = dict(
        id="NTC-0014",
        kind=Kind.NOTICE,
        title="FedRAMP Response to CISA BOD 26-04",
        summary="original",
        published=date(2026, 6, 16),
        deadline=date(2026, 12, 7),
        state=State.SOON,
        impact_areas=["Vuln Management"],
        url="https://www.fedramp.gov/notices/0014",
        needs_action=True,
        source_id="fedramp_notices",
        content_hash="aaaa",
        first_seen=datetime(2026, 6, 16),
        last_seen=datetime(2026, 6, 16),
    )
    base.update(overrides)
    return Item(**base)


def test_diff_detects_deadline_change():
    a = _item()
    b = _item(deadline=date(2027, 3, 7), content_hash="bbbb")
    diff = diff_items(a, b)
    assert "deadline" in diff
    assert diff["deadline"]["from"] == "2026-12-07"
    assert diff["deadline"]["to"] == "2027-03-07"


def test_diff_detects_summary_change():
    a = _item()
    b = _item(summary="amended", content_hash="bbbb")
    diff = diff_items(a, b)
    assert "summary" in diff


def test_diff_empty_when_unchanged():
    a = _item()
    b = _item()
    assert diff_items(a, b) == {}


def test_diff_detects_impact_areas():
    a = _item()
    b = _item(impact_areas=["Vuln Management", "Incident Response"])
    diff = diff_items(a, b)
    assert "impact_areas" in diff
