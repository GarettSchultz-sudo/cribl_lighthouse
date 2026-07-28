import asyncio
from datetime import date, datetime

import pytest

from lighthouse.models import Item, Kind, State
from lighthouse.pipeline.classify import classify


def _item():
    return Item(
        id="NTC-0014",
        kind=Kind.NOTICE,
        title="FedRAMP Response to CISA BOD 26-04 (Prioritizing Security Updates Based on Risk)",
        summary=(
            "FedRAMP is accelerating mandatory adoption of VDR and VER rules to align with "
            "BOD 26-04 by Dec 7 2026. Grace period through Mar 7 2027."
        ),
        published=date(2026, 6, 16),
        deadline=date(2026, 12, 7),
        state=State.SOON,
        impact_areas=["Vuln Management", "Incident Response"],
        url="https://www.fedramp.gov/notices/0014",
        needs_action=True,
        source_id="fedramp_notices",
        content_hash="x",
        first_seen=datetime.utcnow(),
        last_seen=datetime.utcnow(),
    )


@pytest.mark.asyncio
async def test_mock_produces_valid_draft():
    item = _item()
    draft = await classify(item)
    assert draft.classifier == "mock"
    assert draft.epic.summary
    assert draft.stories, "must produce at least one story"
    for s in draft.stories:
        assert s.phase in {"Immediate", "Short-Term", "Full Implementation", "Grace Period"}
        assert s.acceptance_criteria
        assert s.priority in {"Highest", "High", "Medium", "Low"}
    assert "fedramp" in draft.epic.labels
    assert "ntc-0014" in draft.epic.labels


@pytest.mark.asyncio
async def test_mock_includes_full_implementation_phase():
    item = _item()
    draft = await classify(item)
    phases = {s.phase for s in draft.stories}
    assert "Full Implementation" in phases
    assert "Grace Period" in phases


@pytest.mark.asyncio
async def test_mock_adds_immediate_for_close_deadline(monkeypatch):
    # Deadline within 30 days should trigger an Immediate story.
    from datetime import date as _date
    item = _item()
    item.deadline = _date.today().replace(year=_date.today().year)  # noop guard
    item.deadline = (_date.today())
    draft = await classify(item)
    phases = {s.phase for s in draft.stories}
    assert "Immediate" in phases
