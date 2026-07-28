from datetime import date, datetime

from lighthouse.models import Item, Kind, State
from lighthouse.store import Store


def _item(content_hash="aaaa", deadline=date(2026, 12, 7)):
    return Item(
        id="NTC-0014",
        kind=Kind.NOTICE,
        title="FedRAMP Response to CISA BOD 26-04",
        summary="x",
        published=date(2026, 6, 16),
        deadline=deadline,
        state=State.SOON,
        impact_areas=[],
        url="https://www.fedramp.gov/notices/0014",
        needs_action=True,
        source_id="fedramp_notices",
        content_hash=content_hash,
        first_seen=datetime(2026, 6, 16, 12, 0, 0),
        last_seen=datetime(2026, 6, 16, 12, 0, 0),
    )


def test_upsert_marks_first_insert_as_new():
    s = Store()
    is_new, prev_hash = s.upsert_item(_item())
    assert is_new is True
    assert prev_hash is None


def test_upsert_returns_prev_hash_on_amendment():
    s = Store()
    s.upsert_item(_item())
    is_new, prev_hash = s.upsert_item(_item(content_hash="bbbb"))
    assert is_new is False
    assert prev_hash == "aaaa"


def test_upsert_preserves_first_seen_on_amendment():
    s = Store()
    s.upsert_item(_item())
    s.upsert_item(_item(content_hash="bbbb"))
    stored = s.get_item("NTC-0014")
    assert stored.first_seen == datetime(2026, 6, 16, 12, 0, 0)


def test_upsert_no_op_when_hash_unchanged():
    s = Store()
    s.upsert_item(_item())
    is_new, prev_hash = s.upsert_item(_item())
    assert is_new is False
    assert prev_hash is None
