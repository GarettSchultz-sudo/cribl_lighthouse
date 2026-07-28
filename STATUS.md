# Cribl Lighthouse — Status Update

_As of 2026-06-26_

## Summary

Lighthouse has moved from a single-page static dashboard to a three-piece toolkit:
two browser tools (dashboard + gap analysis) and a local-first FastAPI backend
that runs the intake → classify → review → ticket loop end-to-end with zero
credentials. The dashboard's posture view is now reframed around the real Cribl
LogStream Cloud — Gov FedRAMP **Moderate** ATO. The gap tool now ships DoD IL2/IL4/IL5/IL6
overlays plus three printable report exports, and the catalog layer has been
refactored to accept additional frameworks (SOC 2, ISO, etc.) without engine
changes.

## Shipped since the initial release (2026-06-09)

| Date | Change |
|------|--------|
| 2026-06-22 | Gap analysis report exports + dashboard live-data shim (`CONTROLS_API`) |
| 2026-06-23 | DoD IL2/IL4/IL5/IL6 baselines added to gap analysis |
| 2026-06-23 | Baseline selector added to the Posture tab |
| 2026-06-23 | Posture tab reframed around the real Moderate ATO |
| 2026-06-26 | `gap.html` refactored to a parallel-catalog architecture |

Diff stats vs. initial release: **`dashboard.html` +279/-49**, **`gap.html` +869/-49**.

## Component status

### Browser tools

- **`dashboard.html`** — Posture / Intake / Impact / Action Board / Sources / Controls / Review tabs. Posture defaults to High readiness toward the next ATO; Low/Moderate/High chips reframe the view. Live-data shim wired via `CONTROLS_API`.
- **`gap.html`** — Parallel-catalog architecture (`CATALOGS` + `MAPPINGS` registries). Active catalog is `FEDRAMP`; baselines available are Greenfield / Low / Moderate / High plus advisory IL2/IL4/IL5/IL6 overlays. Exports: CSV, Executive Brief, Implementation Plan, Markdown.
- **`index.html`** — Launcher; unchanged.

### Backend (`backend/`)

Local-first FastAPI service. **~1,875 lines of Python**, runs end-to-end with no AWS/Slack/Jira/LLM credentials.

| Module | Lines | Status |
|--------|------:|--------|
| `api/app.py` | 491 | FastAPI surface — 9 endpoints |
| `pipeline/classify.py` | 239 | Claude classifier + structured schema; deterministic mock fallback |
| `pipeline/poll.py` | 96 | Fetch → normalize → dedupe orchestrator |
| `pipeline/dedupe.py` | 25 | Stable hash + amendment detection |
| `integrations/slack.py` | 150 | Real client or filesystem outbox |
| `integrations/jira.py` | 98 | Real client or filesystem outbox |
| `store.py` | 150 | SQLite-backed repository |
| `models.py` | 110 | Normalized records + DB schema |
| `config.py` | 72 | Env-driven settings, all optional |
| `sources/*` | 315 | Five sources: FedRAMP Changelog, Notices, Community, FRMR, Federal Register |

**Runtime evidence:** `backend/data/lighthouse.db` (672 KB), `backend/outbox/slack/` (77 drafts), `backend/outbox/jira/` (27 epic/story files). The full loop has fired on real notices including **NTC-0014**.

**Tests:** `test_api_smoke.py`, `test_classify_mock.py`, `test_dedupe.py`, `test_store.py`.

## Open items before commit

- **`backend/` is untracked** — needs an initial commit, a `.gitignore` for `data/lighthouse.db`, `outbox/`, `.venv/`, `__pycache__/`, and the seeded `.env.example`.
- **`dashboard.html` has a local-dev override** — `CONTROLS_API='http://localhost:8787'` is in the working tree. Revert to `''` before pushing to Pages.
- **`README.md` has staged content updates** — the new IL baselines, exports, and backend sections are written but not committed.

## Honest limitations

- DoD IL overlays are **hand-curated** from CC SRG v1r4 / CNSSI 1253, **not OSCAL-authoritative**. Classified annexes are excluded from IL6.
- Dashboard posture/POA&M data is **illustrative** until the backend is connected.
- Cross-framework crosswalks are **advisory**; `gap.html`'s `MAPPINGS` table is wired through but empty.
- Implementation language in expanded control rows is **starter draft only** — needs 3PAO validation before going near an SSP.

## What's next (no commitments)

- Land the backend on `main`; first push will need a `backend/.gitignore`.
- Wire the dashboard's Intake / Action Board / Review tabs to real backend data (the live shim is in place; the rest of the data plumbing still reads from hardcoded arrays).
- Configure the Slack bot and Anthropic API key prereqs so the classifier and review queue stop being mocks.
- Add a second catalog (SOC 2 or ISO 27001) to exercise the parallel-catalog architecture in earnest.
