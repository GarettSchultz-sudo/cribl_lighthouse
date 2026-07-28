# Cribl Lighthouse

FedRAMP compliance tooling over the authoritative **FedRAMP Rev5** control set,
built on the full **High (410-control)** baseline, with **DoD Impact Level**
overlays (IL2/IL4/IL5/IL6) layered on top. Two browser tools plus an optional
local-first backend.

- **Lighthouse Dashboard** — Cribl LogStream Cloud — Gov compliance posture
  (current FedRAMP **Moderate** ATO, with readiness toggles for Low/Moderate/High),
  change intake, RFC blast radius, an SME review queue, and the full Rev5 catalog.
- **Baseline Gap Analysis** — pick a current baseline and a target; see the exact
  control gap, family-by-family coverage, and a starter implementation response
  for every control. Export the result as an **Executive Brief**, an **Implementation
  Plan**, a Markdown report, or CSV.
- **Backend** (`backend/`, optional) — local-first FastAPI service that polls the
  five regulatory sources, classifies new items with Claude, queues drafts for
  Slack review, and creates Jira tickets on approval. Runs end-to-end with zero
  credentials (mock LLM + filesystem outbox).

The two browser tools are single self-contained HTML files (inline CSS/JS), so
they run on any static host — this repo is set up for **GitHub Pages**.

---

## Contents

| Path | What it is |
|------|------------|
| `index.html` | Launcher / entry page — links to both tools |
| `dashboard.html` | Lighthouse dashboard |
| `gap.html` | Baseline Gap Analysis |
| `backend/` | Optional local-first FastAPI backend (intake → classify → Slack → Jira) |
| `.nojekyll` | Tells GitHub Pages to serve files as-is (no Jekyll step) |
| `README.md` | This file |

Each tool has a small **⌂ Lighthouse home** link (bottom-left) back to the launcher.

---

## Quick start — deploy on GitHub Pages

### Option A — web UI (no command line)

1. Create a new repository (e.g. `cribl-lighthouse`). Public is simplest; Pages on
   a private repo requires a paid GitHub plan.
2. **Add file → Upload files**, then drag in `index.html`, `dashboard.html`,
   `gap.html`, `.nojekyll`, and `README.md`. Commit.
3. **Settings → Pages**.
4. Under **Build and deployment → Source**, choose **Deploy from a branch**.
5. Set **Branch: `main`**, **Folder: `/ (root)`**, then **Save**.
6. Wait ~1 minute, refresh, and open the published URL.

> `.nojekyll` is a hidden dotfile and may not show in your file picker. It's
> optional here (no filenames start with `_`), but it's a safe default. If the
> upload skips it, create it on GitHub with **Add file → Create new file**, name
> it `.nojekyll`, and commit it empty.

### Option B — git command line

```bash
git init
git add .
git commit -m "Cribl Lighthouse: dashboard + gap analysis"
git branch -M main
git remote add origin https://github.com/<you>/<repo>.git
git push -u origin main
```

Then enable Pages once (Settings → Pages → Deploy from a branch → `main` / `/root`),
or with the GitHub CLI:

```bash
gh repo create <repo> --public --source=. --push
gh api -X POST repos/<you>/<repo>/pages -f source[branch]=main -f source[path]=/
```

### Resulting URLs

| Page | URL |
|------|-----|
| Launcher | `https://<you>.github.io/<repo>/` |
| Dashboard | `https://<you>.github.io/<repo>/dashboard.html` |
| Gap analysis | `https://<you>.github.io/<repo>/gap.html` |

---

## The tools

### Lighthouse Dashboard (`dashboard.html`)

A compliance-operations view framed around the **current Cribl LogStream Cloud — Gov
ATO (FedRAMP Moderate)**, with readiness toggles for any FedRAMP baseline. Tabs:

- **Posture** — implementation status across the selected baseline. Defaults to
  the High readiness view (gap to the next ATO); switch the **Low / Moderate / High**
  chips to reframe as "current ATO baseline" (Moderate) or to scope down to Low.
  Shows status, owner, evidence link, last/next review, and a coverage summary.
- **Intake Feed** — FedRAMP RFCs, public notices, and regulatory changes as a
  normalized feed with deadlines and action flags.
- **Impact & Integration** — how a change maps to affected control families.
- **Action Board** — a kanban of work items derived from intake.
- **Data Sources** — the upstream feeds the tool is modeled on, with live/proxy
  status.
- **Controls** — the full 410-control catalog, filterable by family and baseline.
- **Review** — an SME review queue for proposed control mappings.

The dashboard reads `CONTROLS_API` (a constant near the top of the controls
section). Left blank, it runs entirely on the bundled catalog with illustrative
posture data. Set it to your backend's base URL (e.g. `http://localhost:8787` for
the bundled backend) to load live feed, review-queue, and POA&M data.

### Baseline Gap Analysis (`gap.html`)

Pick a **From** (current state) and **To** (target) baseline and the tool computes
the exact set difference. Baselines available:

- **Greenfield** (nothing implemented)
- **FedRAMP Rev5 Low / Moderate / High** — OSCAL-authoritative.
- **DoD IL2 / IL4 / IL5 / IL6** — advisory overlays on top of the matching FedRAMP
  base (IL2≈Low, IL4≈Moderate, IL5≈High, IL6=High + classified additions). These
  are hand-curated from DoD CC SRG v1r4 and CNSSI 1253 and **not OSCAL-authoritative**
  — a top-of-page banner makes that explicit when an IL baseline is selected.

The tool produces three views:

- **Gap to implement** — controls in the target not in the source.
- **Already covered** — the overlap.
- **Beyond target** — controls in the source the target drops (for downgrades; use
  the swap button).

It shows summary stats, a coverage-by-family breakdown (sorted by gap size), and a
filterable/searchable control table with view toggles. **Click any control row** to
expand it and read:

- the authoritative **NIST SP 800-53 Rev5 statement** (parameters resolved to
  readable placeholders),
- NIST's **discussion**, and
- **example implementation language** — a family-tailored starter response you can
  copy and adapt.

#### Exports

The toolbar above the control table produces four artifacts from the current
view (respecting From/To, search, family filter, and view toggle):

- **Export CSV** — flat row dump for spreadsheet triage.
- **Executive Brief** — a printable one-pager (opens in a new tab) covering the
  size of the gap, family-by-family coverage, and the headline numbers, suitable
  for leadership or a 3PAO kickoff.
- **Implementation Plan** — a printable operational document grouping the gap
  controls by family with their statements and starter implementation language,
  intended as the seed of an SSP gap-remediation plan.
- **Markdown** — downloads the same content in Markdown for paste into
  Confluence / Notion / a PR description.

Reports include an explicit advisory footer when either baseline is a DoD IL.

---

## Data & methodology

### Baselines

The control universe is FedRAMP High; each control is tagged with the lower
baselines that also include it. DoD IL membership is computed as
`FedRAMP-base ∪ overlay-additions` from the curated CC SRG / CNSSI 1253 lists.

| Baseline | Controls | Source |
|----------|---------:|--------|
| FedRAMP Rev5 **High** | **410** | OSCAL (GSA `fedramp-automation`) |
| FedRAMP Rev5 **Moderate** | 323 | OSCAL |
| FedRAMP Rev5 **Low** | 156 | OSCAL |
| DoD **IL2** | = Low | Advisory (CC SRG §5.1 — no additions over Low) |
| DoD **IL4** | Moderate + ~20 overlay refs | Advisory (CC SRG §5.2) |
| DoD **IL5** | High + ~45 overlay refs | Advisory (CC SRG §5.3 + CNSSI 1253 NSS) |
| DoD **IL6** | IL5 set + classified additions | Advisory (CC SRG §5.4 + CNSSI 1253; classified annexes excluded) |

FedRAMP relationships hold as expected: **Low ⊆ Moderate ⊆ High**. Key transitions:

| From → To | Gap (controls to add) |
|-----------|----------------------:|
| Moderate → High | **87** |
| Low → High | 254 |
| Low → Moderate | 167 |
| Greenfield → High | 410 |

High-baseline controls by family (sums to 410):

```
AC 50  AT  6  AU 27  CA 16  CM 34  CP 35  IA 30  IR 24  MA 12
MP 10  PE 26  PL  7  PS 11  RA 13  SA 25  SC 35  SI 35  SR 14
```

### How it was built

- **Baseline membership** comes from the authoritative FedRAMP Rev5 OSCAL baseline
  profiles (GSA `fedramp-automation`, `master`). The control-ID lists were pulled,
  normalized (`ac-2.1` → `AC-2(1)`), and validated against published counts.
- **Control titles, statements, discussion, and parameters** come from the NIST
  SP 800-53 Rev5 OSCAL catalog (`usnistgov/oscal-content`). Parameter inserts are
  resolved to readable placeholders (e.g. `[organization-defined personnel]`).
- **DoD IL overlays** are hand-curated from CC SRG v1r4 and CNSSI 1253. A small
  set of overlay-only controls (refs in 800-53 Rev5 that aren't in any FedRAMP
  baseline) are injected as catalog stubs so they can be counted and listed; their
  implementation language is marked as an overlay starter, not authoritative.
- **Gaps** are exact set differences over baseline membership — not fuzzy
  crosswalks.

### Catalog architecture (`gap.html`)

`gap.html` is organized as a **parallel catalog** registry. The active framework
(default: `FEDRAMP`) determines the control universe, the available baselines,
the family taxonomy, and the report headers. Adding a new framework (SOC 2, ISO
27001, ISM, etc.) means registering a new entry in `CATALOGS` with its own
controls array and baseline filter — the gap engine, filters, and report exports
work over it unchanged. A `MAPPINGS` array is wired through for future
cross-framework references but is empty today.

---

## Backend (`backend/`)

The browser tools run fully client-side; the backend turns the dashboard from a
mockup into a live intake → review → ticket loop. It is **local-first** — the
entire pipeline runs end-to-end on a laptop with no AWS, no Slack, no Jira, and
no LLM credentials, with stubbed integrations writing to `backend/outbox/`.

### What it does

1. **Polls** five upstream sources on a schedule: FedRAMP Changelog RSS, FedRAMP
   Public Notices RSS, FedRAMP Community RFCs (GitHub), FRMR (GitHub), Federal
   Register API.
2. **Dedupes** new items against a local SQLite store (stable hash + amendment
   detection).
3. **Classifies** each new item with Claude into Jira-ready **Epic + Stories**
   drafts using a structured schema. Falls back to a deterministic mock when no
   Anthropic API key is configured — drafts still look shape-real, no API call.
4. **Posts** drafts to a Slack review queue for human Approve / Edit / Skip. No
   Slack token → posts are written to `backend/outbox/slack/<id>.json`.
5. **Creates Jira tickets** only on approval. No Jira creds → tickets are written
   to `backend/outbox/jira/<id>.json`.

Human-in-the-loop is invariant: the LLM never writes to Jira directly. Slack
review gates every ticket creation.

### Run it

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env       # all values optional — leave blank to run in outbox mode
uvicorn lighthouse.api.app:app --reload --port 8787
```

Kick a one-shot poll and inspect the queue:

```bash
curl -X POST http://localhost:8787/admin/poll-now
curl     http://localhost:8787/feed         | jq '.items | length'
curl     http://localhost:8787/review/queue | jq
```

Then point the dashboard at it by setting `CONTROLS_API='http://localhost:8787'`
near the top of the controls section in `dashboard.html`.

### API surface

| Method | Path | Purpose |
|--------|------|---------|
| GET  | `/feed`           | Combined normalized feed across all five sources, deduped |
| GET  | `/feeds`          | Legacy per-source shape the dashboard expects |
| GET  | `/review/queue`   | Drafts pending Slack review |
| POST | `/review/approve` | Approve a draft → create Jira ticket |
| POST | `/review/skip`    | Archive a draft |
| POST | `/review/edit`    | Replace a draft's payload before approval |
| GET  | `/tasks`          | Jira-mirrored kanban for the Action Board |
| POST | `/admin/poll-now` | Force a poll cycle (dev only) |
| GET  | `/admin/outbox`   | List files written to `outbox/` |

### Why the feeds need this at all

`fedramp.gov` serves its RSS **without CORS headers**, so a browser can't read it
directly. The backend fetches it server-side and re-serves as JSON with CORS
enabled. GitHub Pages is static-only, so this doesn't change when you host the
UI there — Pages serves the interface, your backend serves the live data.

### Designed for AWS

The package has no AWS dependencies in the core pipeline — sources, dedupe,
classification, and the outbox integrations all run as plain Python. The
intended production shape is **Lambda + EventBridge + DynamoDB + Slack/Jira**,
matching the architecture diagram in the dashboard's Data Sources tab. The
local SQLite store and filesystem outbox are drop-in replacements for the AWS
flavors.

See `backend/README.md` for the module layout and development details.

---

## Other hosting options

These same files work on any static host. Besides GitHub Pages:

- **Google Apps Script** — a `doGet` router can serve both tools from one web app
  (`…/exec` and `…/exec?app=gap`); Apps Script's `UrlFetchApp` can also act as the
  RSS proxy. (See the `lighthouse-appsscript` package.)
- **Netlify / Cloudflare Pages / Firebase Hosting / Cloud Storage bucket** — drop
  the files in; all give nicer URLs than Apps Script.

---

## Updating

Replace a file and push again (or re-upload in the UI). Pages rebuilds in about a
minute and the URLs stay the same. If you regenerate a tool, keep the filenames
(`dashboard.html`, `gap.html`) and re-add the **⌂ Lighthouse home** link after
`<body>` if you replaced the whole file.

---

## Limitations & honesty

Read this before anyone treats output as authoritative.

- **Implementation language is a draft, not a control response.** The starter text
  in the gap tool is generated from the control statement and family patterns. It
  must be tailored to how your system actually works and validated by your 3PAO
  before it goes near an SSP — an assessor will reject generic boilerplate. The
  control **statement** and **discussion** are authoritative NIST text; only the
  implementation block is generated.
- **DoD IL baselines are advisory, not OSCAL-authoritative.** IL2/IL4/IL5/IL6
  membership is hand-curated from public DoD CC SRG v1r4 and CNSSI 1253 references.
  Classified annexes of CNSSI 1253 are deliberately excluded — the rendered IL6
  set is the publicly defensible subset, not a full IL6 lift. Validate with a
  DCSA assessor before using any IL output in an authorization package. The tool
  shows an in-page advisory banner whenever an IL baseline is selected.
- **Dashboard posture/POA&M data is illustrative** until you connect the backend
  via `CONTROLS_API`. The current ATO framing (FedRAMP Moderate for Cribl
  LogStream Cloud — Gov) is hard-coded; statuses are seeded so Moderate-baseline
  controls are "implemented" and High-only controls are "planned" — placeholders,
  not your real compliance state.
- **Crosswalks are advisory.** The dashboard's cross-framework references are
  advisory reference data, not authoritative equivalences. `gap.html`'s
  cross-framework mapping table is wired through but empty today.
- **Gaps are within-catalog set differences.** The gap tool does exact set
  differences over baselines **inside a single catalog** (FedRAMP+IL today). It
  does **not** do cross-framework gaps (e.g. FedRAMP → SOC 2 / ISO 27001) — that
  needs advisory crosswalks, which are out of scope until additional catalogs ship.
- **LI-SaaS is not included.** Only Low, Moderate, and High are loaded from
  FedRAMP. The tools are data-driven, so adding a fourth baseline tag would
  surface it automatically; it was left out rather than approximated.
- **Verify against the source of truth.** FedRAMP, NIST, and DoD update their
  baselines and overlays. Re-pull from the upstream OSCAL sources (and re-read
  the current CC SRG / CNSSI 1253) to confirm currency before relying on these
  counts.

---

## Data sources & attribution

- **FedRAMP Rev5 baselines** — GSA `fedramp-automation` (OSCAL profiles). U.S.
  Government work, public domain.
- **NIST SP 800-53 Rev5 catalog** — `usnistgov/oscal-content`. U.S. Government
  work, public domain.
- **DoD CC SRG v1r4** and **CNSSI 1253** — publicly released DoD / CNSS
  references for the IL2/IL4/IL5/IL6 overlays. U.S. Government work.
- **Crosswalk reference data** (dashboard, advisory) — myctrl.tools
  (© hackIDLE / Ethan Troy), licensed **CC BY 4.0**.

This project is an independent tool and is not affiliated with or endorsed by
FedRAMP, the GSA, NIST, or the DoD.
