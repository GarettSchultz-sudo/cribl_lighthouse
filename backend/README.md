# Lighthouse Backend

Local-first backend for the Cribl Lighthouse compliance dashboard. Polls the
five regulatory sources defined in `dashboard.html`, classifies new items with
Claude into Jira-ready Epics + Stories, queues them for Slack review, and (on
approve) creates Jira tickets. Designed to run identically on a laptop and on
AWS Lambda — no AWS dependencies in the core pipeline.

## What works without any credentials

- All five sources poll on the configured interval.
- New items are deduped against a local SQLite database.
- Items are classified by an **LLM-mock** that produces deterministic stub
  Epic/Story drafts (looks shape-real; no API call).
- "Slack" posts are written to `outbox/slack/<id>.json`.
- "Jira" creates are written to `outbox/jira/<id>.json`.
- The HTTP API serves the dashboard.

This means you can run the entire pipeline end-to-end with zero external
services, see what would have been posted, and demo the loop. Add real
credentials when you have them.

## Run

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn lighthouse.api.app:app --reload --port 8787
```

In another terminal, kick a one-shot poll and classify:

```bash
curl -X POST http://localhost:8787/admin/poll-now
curl     http://localhost:8787/feed | jq '.items | length'
curl     http://localhost:8787/review/queue | jq
```

Then open `dashboard.html` (set `CONTROLS_API` to `http://localhost:8787`).

## Endpoints

- `GET  /feed`            — combined normalized feed (all sources, deduped)
- `GET  /feeds`           — legacy shape expected by `dashboard.html` (per-source)
- `GET  /review/queue`    — drafts pending review
- `POST /review/approve`  — approve a draft → Jira create
- `POST /review/skip`     — archive a draft
- `POST /review/edit`     — replace a draft's payload before approval
- `GET  /tasks`           — Jira-mirrored kanban for the Action Board
- `POST /admin/poll-now`  — force a poll cycle (dev only)
- `GET  /admin/outbox`    — list what was written to outbox/

## Layout

```
src/lighthouse/
  config.py            settings (env-driven, all optional)
  models.py            normalized record types + DB schema
  store.py             SQLite-backed repository
  sources/             one module per source: fedramp_changelog, fedramp_notices,
                       fedramp_community, frmr, federal_register
  pipeline/
    poll.py            orchestrates fetch → normalize → dedupe → classify
    classify.py        Claude prompt + schema; falls back to mock if no key
    dedupe.py          stable hash + amendment detection
  integrations/
    slack.py           real or outbox client
    jira.py            real or outbox client
  api/app.py           FastAPI surface
```
