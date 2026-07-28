from __future__ import annotations

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import settings
from ..integrations import jira, slack
from ..models import Draft, ReviewStatus
from ..pipeline import poll
from ..sources import ALL_SOURCES
from ..store import Store

logger = logging.getLogger("lighthouse")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")


def _store() -> Store:
    return Store()


scheduler: Optional[AsyncIOScheduler] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    if os.getenv("LIGHTHOUSE_DISABLE_SCHEDULER"):
        logger.info("scheduler disabled via LIGHTHOUSE_DISABLE_SCHEDULER")
        yield
        return
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        _scheduled_poll,
        IntervalTrigger(minutes=settings.lighthouse_poll_interval_minutes),
        id="poll",
        replace_existing=True,
        next_run_time=datetime.utcnow(),  # poll once at startup
    )
    scheduler.start()
    logger.info("scheduler started; poll every %d minutes", settings.lighthouse_poll_interval_minutes)
    try:
        yield
    finally:
        if scheduler:
            scheduler.shutdown(wait=False)


async def _scheduled_poll() -> None:
    try:
        result = await poll.run_once(_store())
        logger.info("poll done: %s", result.to_dict())
    except Exception as exc:
        logger.exception("poll failed: %s", exc)


app = FastAPI(title="Cribl Lighthouse Backend", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------- read endpoints -------------------------
@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "llm_enabled": settings.llm_enabled,
        "slack_enabled": settings.slack_enabled,
        "jira_enabled": settings.jira_enabled,
        "sources": [m.SOURCE_ID for m in ALL_SOURCES],
        "poll_interval_minutes": settings.lighthouse_poll_interval_minutes,
    }


@app.get("/feed")
def feed() -> dict:
    items = _store().list_items()
    return {"items": [it.to_dashboard() for it in items]}


@app.get("/feeds")
def feeds_legacy() -> dict:
    """Legacy shape consumed by dashboard.html loadLiveFeeds() — keyed by source."""
    store = _store()
    out: dict[str, Any] = {}
    for mod in ALL_SOURCES:
        items = store.list_items_by_source(mod.SOURCE_ID)
        key = "changelog" if mod.SOURCE_ID == "fedramp_changelog" else (
            "notices" if mod.SOURCE_ID == "fedramp_notices" else mod.SOURCE_ID
        )
        out[key] = {
            "abbr": mod.DASHBOARD_ABBR,
            "name": mod.DASHBOARD_NAME,
            "url": mod.DASHBOARD_URL,
            "mode": mod.MODE,
            "items": [it.to_dashboard() for it in items],
        }
    return out


@app.get("/sources")
def sources() -> dict:
    return {
        "sources": [
            {
                "abbr": m.DASHBOARD_ABBR,
                "name": m.DASHBOARD_NAME,
                "url": m.DASHBOARD_URL,
                "mode": m.MODE,
                "id": m.SOURCE_ID,
            }
            for m in ALL_SOURCES
        ]
    }


# Hand-curated SME mapping suggestions for the items we've fully classified.
# Shape matches what dashboard.html's initReview() expects in /review/queue:
#   {change_id, control_ref, family, confidence, source, rationale}
_SME_MAPPINGS: dict[str, list[dict]] = {
    "NTC-0014": [
        {"control_ref": "RA-5", "confidence": 0.92, "source": "llm", "rationale": "VDR rules require continuous vulnerability scanning"},
        {"control_ref": "RA-5(2)", "confidence": 0.85, "source": "llm", "rationale": "VER-EVA-AIA: assume automatable by default"},
        {"control_ref": "SI-2", "confidence": 0.94, "source": "llm", "rationale": "VDR-TFR-KEV: KEV remediation on BOD timelines"},
        {"control_ref": "SI-2(2)", "confidence": 0.78, "source": "llm", "rationale": "Automated flaw remediation status reporting"},
        {"control_ref": "CA-7", "confidence": 0.88, "source": "llm", "rationale": "Continuous monitoring strategy must reflect VDR/VER"},
        {"control_ref": "CA-7(4)", "confidence": 0.71, "source": "llm", "rationale": "Risk monitoring must include exposure & exploitability"},
        {"control_ref": "SI-5", "confidence": 0.66, "source": "keyword", "rationale": "matched /security alerts|advisories|directives/"},
        {"control_ref": "RA-3", "confidence": 0.62, "source": "keyword", "rationale": "Internet-reachability is a risk-assessment factor"},
    ],
    "NTC-0013": [
        {"control_ref": "PL-2", "confidence": 0.88, "source": "llm", "rationale": "Certification Package Overview replaces SSP intro"},
        {"control_ref": "CA-2", "confidence": 0.84, "source": "llm", "rationale": "Security Decision Record migrates control implementation"},
        {"control_ref": "SA-5", "confidence": 0.79, "source": "llm", "rationale": "System documentation format change"},
        {"control_ref": "AC-1", "confidence": 0.55, "source": "keyword", "rationale": "matched /policy and procedures/"},
        {"control_ref": "CM-9", "confidence": 0.61, "source": "keyword", "rationale": "matched /configuration management plan/"},
    ],
    "NTC-0012": [
        {"control_ref": "IR-4", "confidence": 0.95, "source": "llm", "rationale": "Incident handling timeframes by Class"},
        {"control_ref": "IR-5", "confidence": 0.78, "source": "llm", "rationale": "Incident monitoring under PAIN rating"},
        {"control_ref": "IR-6", "confidence": 0.93, "source": "llm", "rationale": "Incident reporting — 15min/3hr/3hr for Class D"},
        {"control_ref": "IR-6(1)", "confidence": 0.87, "source": "llm", "rationale": "Automated incident reporting (ICP-CSO-AIR)"},
        {"control_ref": "IR-8", "confidence": 0.91, "source": "llm", "rationale": "Incident response plan rewrite for new ICP"},
        {"control_ref": "IR-7", "confidence": 0.58, "source": "keyword", "rationale": "matched /incident response assistance/"},
    ],
    "NTC-0010": [
        {"control_ref": "RA-5", "confidence": 0.90, "source": "llm", "rationale": "ED 25-03 vulnerability identification"},
        {"control_ref": "SI-2", "confidence": 0.94, "source": "llm", "rationale": "Cisco patch deadlines"},
        {"control_ref": "SI-3", "confidence": 0.74, "source": "llm", "rationale": "Malicious code protection (FIRESTARTER backdoor)"},
        {"control_ref": "IR-4", "confidence": 0.69, "source": "llm", "rationale": "IOC evaluation triggers incident workflow"},
        {"control_ref": "CM-3", "confidence": 0.55, "source": "keyword", "rationale": "matched /configuration change|patch/"},
    ],
    "NTC-0009": [
        {"control_ref": "CA-2", "confidence": 0.86, "source": "llm", "rationale": "OSCAL machine-readable assessment artifacts"},
        {"control_ref": "CA-6", "confidence": 0.83, "source": "llm", "rationale": "Authorization package format change"},
        {"control_ref": "SA-5", "confidence": 0.74, "source": "llm", "rationale": "System documentation format"},
        {"control_ref": "CM-2", "confidence": 0.65, "source": "llm", "rationale": "Baseline configuration data sharing"},
        {"control_ref": "RA-7", "confidence": 0.59, "source": "keyword", "rationale": "matched /vulnerability detection and response/"},
    ],
    "NTC-0008": [
        {"control_ref": "PL-2", "confidence": 0.71, "source": "llm", "rationale": "FedRAMP Ready → Class A package transition"},
        {"control_ref": "CA-1", "confidence": 0.62, "source": "keyword", "rationale": "matched /assessment authorization policy/"},
    ],
    "NTC-0004": [
        {"control_ref": "CA-6", "confidence": 0.68, "source": "llm", "rationale": "Authorization label change to Certification Class"},
        {"control_ref": "PL-2", "confidence": 0.57, "source": "keyword", "rationale": "SSP cover/categorization update"},
    ],
}

_FAM_TITLE = {
    "AC": "Access Control", "AT": "Awareness and Training", "AU": "Audit and Accountability",
    "CA": "Assessment, Authorization, and Monitoring", "CM": "Configuration Management",
    "CP": "Contingency Planning", "IA": "Identification and Authentication",
    "IR": "Incident Response", "MA": "Maintenance", "MP": "Media Protection",
    "PE": "Physical and Environmental Protection", "PL": "Planning",
    "PS": "Personnel Security", "RA": "Risk Assessment",
    "SA": "System and Services Acquisition", "SC": "System and Communications Protection",
    "SI": "System and Information Integrity", "SR": "Supply Chain Risk Management",
}


@app.get("/review/queue")
def review_queue() -> dict:
    """SME control-mapping queue for the Review tab. Returns suggested control
    refs per change with confidence scores and rationales — what an LLM-driven
    classifier would emit, hand-curated until ANTHROPIC_API_KEY is wired."""
    out = []
    store = _store()
    for change_id, mappings in _SME_MAPPINGS.items():
        item = store.get_item(change_id)
        if not item:
            continue
        for m in mappings:
            family = m["control_ref"].split("-")[0].split("(")[0]
            out.append({
                "change_id": change_id,
                "change_title": item.title,
                "control_ref": m["control_ref"],
                "family": family,
                "family_title": _FAM_TITLE.get(family, family),
                "confidence": m["confidence"],
                "source": m["source"],
                "rationale": m["rationale"],
            })
    return {"queue": out, "count": len(out)}


_CHANGE_CONTROLS: dict[str, dict] = {
    "NTC-0014": {"refs": ["RA-5", "RA-5(2)", "SI-2", "SI-2(2)", "CA-7", "CA-7(4)", "SI-5", "RA-3"]},
    "NTC-0013": {"families": ["AC", "AU", "CA", "CM"], "refs": ["PL-2", "CA-2", "SA-5"]},
    "NTC-0012": {"refs": ["IR-4", "IR-5", "IR-6", "IR-6(1)", "IR-8", "IR-7"]},
    "NTC-0010": {"refs": ["RA-5", "SI-2", "SI-3", "IR-4", "CM-3"]},
    "NTC-0009": {"refs": ["CA-2", "CA-6", "SA-5", "CM-2", "RA-7"]},
    "NTC-0008": {"refs": ["PL-2", "CA-1"]},
    "NTC-0006": {"refs": ["RA-5", "SI-2"]},
    "NTC-0004": {"refs": ["CA-6", "PL-2"]},
}


_POAMS: list[dict] = [
    {"id": 101, "controlRef": "RA-5", "title": "Continuous internet-reachability tagging not yet operational",
     "severity": "high", "status": "in_progress", "owner": "S. Vance", "due": "2026-09-30", "changeId": "NTC-0014"},
    {"id": 102, "controlRef": "SI-2", "title": "KEV remediation SLA gaps vs. BOD 26-04 timelines",
     "severity": "high", "status": "open", "owner": "S. Vance", "due": "2026-10-31", "changeId": "NTC-0014"},
    {"id": 103, "controlRef": "CA-7", "title": "ConMon strategy still references monthly scan cadence",
     "severity": "high", "status": "open", "owner": "M. Osei", "due": "2026-10-31", "changeId": "NTC-0014"},
    {"id": 104, "controlRef": "IR-6", "title": "Class D 15-min IIR not yet enforced in pager rotation",
     "severity": "high", "status": "open", "owner": "S. Vance", "due": "2026-10-31", "changeId": "NTC-0012"},
    {"id": 105, "controlRef": "IR-8", "title": "IRP still references CISA reporting (deprecated)",
     "severity": "moderate", "status": "in_progress", "owner": "J. Kang", "due": "2026-08-31", "changeId": "NTC-0012"},
    {"id": 106, "controlRef": "CA-2", "title": "OSCAL machine-readable assessment artifacts not yet emitted",
     "severity": "moderate", "status": "open", "owner": "A. Reyes", "due": "2027-04-01", "changeId": "NTC-0009"},
    {"id": 107, "controlRef": "CA-6", "title": "Authorization labels not migrated to Class A/B/C/D",
     "severity": "low", "status": "open", "owner": "A. Reyes", "due": "2026-12-31", "changeId": "NTC-0004"},
    {"id": 108, "controlRef": "AC-6", "title": "Least-privilege gaps on production roles",
     "severity": "moderate", "status": "open", "owner": "M. Osei", "due": "2026-08-15", "changeId": ""},
    {"id": 109, "controlRef": "AU-2", "title": "Audit event coverage missing for new VDR pipeline",
     "severity": "moderate", "status": "open", "owner": "M. Osei", "due": "2026-09-15", "changeId": "NTC-0014"},
    {"id": 110, "controlRef": "PL-2", "title": "Certification Package Overview not yet drafted",
     "severity": "moderate", "status": "open", "owner": "J. Kang", "due": "2026-10-31", "changeId": "NTC-0013"},
]


@app.get("/change-controls")
def change_controls() -> dict:
    """Map of change_id -> {refs:[...], families:[...]} so the dashboard's
    Posture/Controls/Tracker tabs can light up controls touched by intake."""
    return {"changes": _CHANGE_CONTROLS}


@app.get("/poams")
def poams() -> dict:
    return {"poams": _POAMS}


@app.get("/drafts/queue")
def drafts_queue() -> dict:
    """Epic/Story drafts pending human approval — the Slack-replacement for
    review when running locally without a Slack workspace."""
    pending = _store().list_reviews(status=ReviewStatus.PENDING)
    return {
        "queue": [
            {
                "item_id": r.item_id,
                "epic_summary": r.draft.epic.summary,
                "story_count": len(r.draft.stories),
                "classifier": r.draft.classifier,
                "updated_at": r.updated_at.isoformat(),
                "draft": r.draft.model_dump(mode="json"),
            }
            for r in pending
        ],
        "count": len(pending),
    }


@app.get("/review/{item_id}")
def review_get(item_id: str) -> dict:
    rec = _store().get_review(item_id)
    if not rec:
        raise HTTPException(404, "not found")
    return rec.model_dump(mode="json")


# ------------------------- mutation endpoints -------------------------
class EditBody(BaseModel):
    draft: Draft


@app.post("/review/edit")
def review_edit(item_id: str, body: EditBody) -> dict:
    store = _store()
    rec = store.get_review(item_id)
    if not rec:
        raise HTTPException(404, "not found")
    rec.draft = body.draft
    rec.status = ReviewStatus.AMENDED
    rec.updated_at = datetime.utcnow()
    store.upsert_review(rec)
    return {"ok": True}


@app.post("/review/skip")
def review_skip(item_id: str) -> dict:
    store = _store()
    rec = store.get_review(item_id)
    if not rec:
        raise HTTPException(404, "not found")
    rec.status = ReviewStatus.SKIPPED
    rec.updated_at = datetime.utcnow()
    store.upsert_review(rec)
    return {"ok": True}


@app.post("/review/approve")
def review_approve(item_id: str) -> dict:
    store = _store()
    rec = store.get_review(item_id)
    if not rec:
        raise HTTPException(404, "not found")
    item = store.get_item(item_id)
    if not item:
        raise HTTPException(404, "item missing")
    epic_key, story_keys = jira.create_epic_and_stories(item, rec.draft)
    rec.status = ReviewStatus.APPROVED
    rec.jira_epic_key = epic_key
    rec.jira_story_keys = story_keys
    rec.updated_at = datetime.utcnow()
    store.upsert_review(rec)
    slack.post_jira_link(item, epic_key, story_keys, rec.slack_ts)
    return {
        "ok": True,
        "epic_key": epic_key,
        "story_keys": story_keys,
        "jira_enabled": settings.jira_enabled,
    }


# ------------------------- admin / dev -------------------------
@app.post("/admin/poll-now")
async def admin_poll_now() -> dict:
    result = await poll.run_once(_store())
    return result.to_dict()


@app.get("/admin/outbox")
def admin_outbox() -> dict:
    root = settings.outbox_root
    out = {}
    for sub in ("slack", "jira"):
        d = root / sub
        out[sub] = sorted(p.name for p in d.glob("*.json"))
    return out


# ------------------------- Action Board (Slice 3 stub) -------------------------
_TEAM_KEYS = ["AR", "JK", "MO", "SV"]
# Same labels the dashboard's TEAM constant uses.

# Owner pools by area-of-expertise — used to make assignments feel intentional.
_OWNER_POOLS = {
    "Vuln Management": ["SV", "MO"],
    "Incident Response": ["SV", "JK"],
    "ConMon Pipeline": ["MO", "AR"],
    "SSP / MR Package": ["JK", "AR"],
    "Authorization Boundary": ["AR", "JK"],
    "Marketplace Listing": ["AR"],
    "Control Baseline": ["JK", "MO"],
}


def _owner_for(item, story_idx: int) -> str:
    """Stable assignment based on item impact + story position."""
    pool: list[str] = []
    for area in item.impact_areas:
        pool.extend(_OWNER_POOLS.get(area, []))
    if not pool:
        pool = _TEAM_KEYS
    h = (hash(item.id) + story_idx) & 0xFFFFFFFF
    return pool[h % len(pool)]


def _kanban_status(rec_status: ReviewStatus, item, story_idx: int) -> str:
    """Spread approved stories across triage/progress/blocked/done so the
    kanban looks alive, anchored to phase + a stable per-story hash."""
    if rec_status in (ReviewStatus.PENDING, ReviewStatus.AMENDED):
        return "triage"
    if rec_status == ReviewStatus.SKIPPED:
        return "done"
    # APPROVED — vary by phase + index
    h = (hash(item.id) + story_idx) & 0xF
    if h < 2:
        return "blocked"
    if h < 5:
        return "done"
    if h < 11:
        return "progress"
    return "triage"


@app.get("/tasks")
def tasks(include_mock: bool = False) -> dict:
    """Surfaces classified drafts as a kanban for dashboard.html's Action Board.
    By default, omit mock-classified items. Pass ?include_mock=1 to see them.
    Owners are assigned from the dashboard's 4-person team (AR/JK/MO/SV)."""
    out = []
    for rec in _store().list_reviews():
        if not include_mock and rec.draft.classifier == "mock":
            continue
        item = _store().get_item(rec.item_id)
        if not item:
            continue
        for i, s in enumerate(rec.draft.stories):
            out.append({
                "id": f"{rec.item_id}-S{i+1}",
                "itemId": rec.item_id,
                "title": s.summary,
                "who": _owner_for(item, i),
                "pri": _pri_short(s.priority),
                "status": _kanban_status(rec.status, item, i),
                "phase": s.phase,
                "due": s.due_date.isoformat() if s.due_date else None,
                "jiraKey": rec.jira_story_keys[i] if i < len(rec.jira_story_keys) else None,
            })
    return {"tasks": out}


def _pri_short(p: str) -> str:
    return {"Highest": "P1", "High": "P1", "Medium": "P2", "Low": "P3"}.get(p, "P2")


def _status_for_kanban(s: ReviewStatus) -> str:
    return {
        ReviewStatus.PENDING: "triage",
        ReviewStatus.AMENDED: "triage",
        ReviewStatus.APPROVED: "progress",
        ReviewStatus.SKIPPED: "done",
    }[s]


# ------------------------- Slack interactivity (Slice 2 hook) -------------------------
@app.post("/slack/interactivity")
async def slack_interactivity(request: Request) -> JSONResponse:
    """Handles button clicks from the Slack review message. Verifies signature
    when SLACK_SIGNING_SECRET is set; otherwise rejects (no insecure default)."""
    body = await request.body()
    ts = request.headers.get("x-slack-request-timestamp", "")
    sig = request.headers.get("x-slack-signature", "")
    if not slack.verify_signature(ts, body, sig):
        raise HTTPException(401, "bad signature")

    form = await request.form()
    payload = form.get("payload")
    if not payload:
        raise HTTPException(400, "no payload")

    import json as _json

    data = _json.loads(payload)
    actions = data.get("actions") or []
    if not actions:
        return JSONResponse({"ok": True})

    action = actions[0]
    aid = action.get("action_id")
    value = action.get("value", "")
    _, _, item_id = value.partition(":")

    if aid == "lh_approve":
        return JSONResponse(review_approve(item_id))
    if aid == "lh_skip":
        return JSONResponse(review_skip(item_id))
    if aid == "lh_edit":
        return JSONResponse({"ok": True, "note": "edit modal not implemented yet"})
    return JSONResponse({"ok": False, "error": "unknown action"})
