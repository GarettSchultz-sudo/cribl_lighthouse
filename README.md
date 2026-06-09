# Cribl Lighthouse

FedRAMP compliance tooling over the authoritative **FedRAMP Rev5** control set,
built on the full **High (410-control)** baseline. Two browser tools, no build
step, no server required to run them.

- **Lighthouse Dashboard** — change intake, control mapping, RFC blast radius, an
  SME review queue, and compliance posture across the High baseline.
- **Baseline Gap Analysis** — pick a current baseline and a target; see the exact
  control gap, family-by-family coverage, and a starter implementation response
  for every control.

Both are single self-contained HTML files (inline CSS/JS), so they run on any
static host — this repo is set up for **GitHub Pages**.

---

## Contents

| File | What it is |
|------|------------|
| `index.html` | Launcher / entry page — links to both tools |
| `dashboard.html` | Lighthouse dashboard |
| `gap.html` | Baseline Gap Analysis |
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

A compliance-operations view over the full FedRAMP High baseline. Tabs:

- **Posture** — implementation status across all 410 controls (status, owner,
  evidence link, last/next review) with a coverage summary.
- **Intake Feed** — FedRAMP RFCs, public notices, and regulatory changes as a
  normalized feed with deadlines and action flags.
- **Impact & Integration** — how a change maps to affected control families.
- **Action Board** — a kanban of work items derived from intake.
- **Data Sources** — the upstream feeds the tool is modeled on, with live/proxy
  status.
- **Controls** — the full 410-control catalog, filterable by family and baseline.
- **Review** — an SME review queue for proposed control mappings.

The dashboard reads `CONTROLS_API` (a constant near the bottom of the file). Left
blank, it runs entirely on the bundled catalog with illustrative posture data. Set
it to your backend's base URL to load live posture, status, and POA&M data.

### Baseline Gap Analysis (`gap.html`)

Pick a **From** (current state) and **To** (target) baseline — Greenfield, Low,
Moderate, or High — and the tool computes the exact set difference:

- **Gap to implement** — controls in the target not in the source.
- **Already covered** — the overlap.
- **Beyond target** — controls in the source the target drops (for downgrades; use
  the swap button).

It shows summary stats, a coverage-by-family breakdown (sorted by gap size), a
filterable/searchable control table with a view toggle, and **CSV export** of the
current view. **Click any control row** to expand it and read:

- the authoritative **NIST SP 800-53 Rev5 statement** (parameters resolved to
  readable placeholders),
- NIST's **discussion**, and
- **example implementation language** — a family-tailored starter response you can
  copy and adapt.

---

## Data & methodology

### Baselines

The control universe is FedRAMP High; each control is tagged with the lower
baselines that also include it.

| Baseline | Controls |
|----------|---------:|
| FedRAMP Rev5 **High** | **410** |
| FedRAMP Rev5 **Moderate** | 323 |
| FedRAMP Rev5 **Low** | 156 |

Relationships hold as expected: **Low ⊆ Moderate ⊆ High**. Key transitions:

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
- **Gaps** are exact set differences over baseline membership — not fuzzy
  crosswalks.

---

## Optional backend

The tools run fully client-side, but a small backend unlocks live data. It is
packaged separately (`lighthouse-controls`) and provides:

- A **controls / posture API** (FastAPI) the dashboard reads when `CONTROLS_API`
  is set — frameworks, controls, crosswalks, RFC blast radius, review queue,
  control status, and POA&Ms.
- A **feeds endpoint** (`/feeds`) that polls the FedRAMP Changelog and Public
  Notices RSS **server-side** and re-serves them as JSON with CORS enabled.

Why the feeds need a backend: `fedramp.gov` serves its RSS without CORS headers,
so a browser can't read it directly. The backend (or a Google Apps Script
`getFeeds()` function) fetches it server-to-server and hands it to the page. GitHub
Pages is static-only, so this doesn't change when you host the UI here — Pages
serves the interface, your API serves the live data.

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
- **Dashboard posture/POA&M data is illustrative** until you connect a backend via
  `CONTROLS_API`. The seeded statuses and owners are placeholders, not your real
  compliance state.
- **Crosswalks are advisory.** Any cross-framework mapping shown in the dashboard
  is advisory reference data, not an authoritative equivalence.
- **Gaps are FedRAMP-baseline-only.** The gap tool does exact set differences over
  FedRAMP Rev5 baselines. It does **not** do cross-framework gaps (e.g.
  FedRAMP → SOC 2 / ISO 27001) — that needs advisory crosswalks, which is out of
  scope here.
- **LI-SaaS is not included.** Only Low, Moderate, and High are loaded. The tools
  are data-driven, so adding a fourth baseline tag would surface it automatically;
  it was left out rather than approximated.
- **Verify against the source of truth.** FedRAMP and NIST update their baselines
  and catalog. Re-pull from the upstream OSCAL sources to confirm currency before
  relying on these counts.

---

## Data sources & attribution

- **FedRAMP Rev5 baselines** — GSA `fedramp-automation` (OSCAL profiles). U.S.
  Government work, public domain.
- **NIST SP 800-53 Rev5 catalog** — `usnistgov/oscal-content`. U.S. Government
  work, public domain.
- **Crosswalk reference data** (dashboard, advisory) — myctrl.tools
  (© hackIDLE / Ethan Troy), licensed **CC BY 4.0**.

This project is an independent tool and is not affiliated with or endorsed by
FedRAMP, the GSA, or NIST.
