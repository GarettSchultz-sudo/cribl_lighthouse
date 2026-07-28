# Lighthouse — Demo Intro (3 slides)

Three-slide opener before tomorrow's demo. Hierarchy: **What it is →
Dashboard (the operator surface) → Gap analysis (the planning surface)**. Each
slide has one screenshot and ~60–90 seconds of speaker notes.

---

## Slide 1 — What Lighthouse is

**Title:** Cribl Lighthouse — FedRAMP compliance ops
**Subtitle:** A toolkit for staying current with FedRAMP changes and planning the next ATO.

**Screenshot:** `screenshots/01-launcher.png`
**How to capture:** open `index.html` in the browser. Full window grab (Cmd-Shift-4, then space, click the window). Ideal size: 1600×1000.

**One-line framing:**
> Lighthouse turns FedRAMP from "PDFs and tribal knowledge" into operational state: posture today, the next ATO gap, and a live intake loop for regulatory changes.

**Speaker notes (~75 sec):**
- The problem: FedRAMP Moderate ATO drift is invisible until it's expensive. NTC-0014 was the canary — a public notice we should have caught the day it dropped.
- Three pieces, increasing depth:
  1. **Dashboard** — operator surface: posture, intake feed, review queue, action board.
  2. **Gap Analysis** — planning surface: exact control delta between any two baselines, with starter implementation language.
  3. **Backend** (optional, local-first) — the intake → Claude classify → Slack review → Jira create loop.
- All static HTML except the backend. Runs on GitHub Pages today; the backend slots in when you want live data.
- Built on **authoritative** sources: FedRAMP Rev5 OSCAL profiles + NIST SP 800-53 Rev5 catalog. DoD IL overlays are advisory, hand-curated from CC SRG / CNSSI 1253 — clearly labeled in the UI.

**Action items to land here (say out loud):**
- We need an **owner for the intake loop** — someone whose pager goes off when FedRAMP drops a notice, not "whoever sees the email first." NTC-0014 is the example we keep pointing at.
- The federal landscape doesn't stop moving: CC SRG, CNSSI 1253, and FedRAMP Rev5 baselines all update on their own clocks. We need a **quarterly refresh cadence** for the OSCAL pulls and the IL overlays.

**Hierarchy element to call out:** the three pieces are nested in depth, not parallel. Dashboard is the daily surface; gap analysis is when planning a baseline change; backend is the engine behind the dashboard.

---

## Slide 2 — Dashboard: the operator surface

**Title:** The Dashboard — compliance state, live
**Subtitle:** Cribl LogStream Cloud — Gov · Current ATO: FedRAMP Moderate · Readiness toward: High

**Screenshot:** `screenshots/02-dashboard-posture.png`
**How to capture:** open `dashboard.html`, land on the Posture tab (default). Make sure the **High** chip is selected so the readiness gap is visible. Capture the full posture view including the Low/Moderate/High chips, the coverage summary, and the family bars.

**Speaker notes (~80 sec):**
- Default view is Posture, framed around the **real** current ATO (Moderate). The High chip shows the readiness gap toward the next ATO; switching to Moderate reframes as "current ATO baseline — no gap"; Low scopes down.
- The other tabs run the operating loop:
  - **Intake Feed** — FedRAMP Changelog, Public Notices, Community RFCs, FRMR, Federal Register. Five sources, deduped, normalized.
  - **Impact & Integration** — when a change drops, which control families does it touch?
  - **Action Board** — kanban of work items derived from intake.
  - **Review** — SME queue for proposed mappings.
  - **Controls** — full Rev5 catalog, filterable.
- The dashboard reads a `CONTROLS_API` constant. Left blank, it runs on bundled illustrative data; pointed at the backend (`http://localhost:8787`), it goes live.
- This is the surface compliance + eng look at daily.

**Action items to land here (say out loud):**
- **Wire the dashboard to the backend.** Intake / Action Board / Review tabs still read from hardcoded arrays. The shim is in place; the data plumbing isn't. This is the gate to "live" — without it, the daily surface stays a demo.
- **Stand up Slack + Anthropic credentials.** Until those land, classification is a deterministic mock and the review queue writes to `outbox/` instead of a channel. Both are prereq tickets that need owners.
- **Set the review SLA.** The pipeline is human-in-the-loop by design. We need a stated turnaround on review-queue items (e.g. 1 business day for FedRAMP notices, 5 for community RFCs) so nothing rots in the queue while the federal calendar keeps moving.

**Hierarchy element to call out:** Posture is the headline. Everything else feeds Posture — intake creates work, work closes controls, controls roll up to readiness.

---

## Slide 3 — Gap Analysis: the planning surface

**Title:** Baseline Gap Analysis — exact deltas, starter language
**Subtitle:** FedRAMP Low / Moderate / High + DoD IL2 / IL4 / IL5 / IL6 · Exports: Executive Brief, Implementation Plan, Markdown, CSV

**Screenshot:** `screenshots/03-gap-moderate-to-high.png`
**How to capture:** open `gap.html`. Set **From: Moderate (323)**, **To: High (410)**. This shows the headline 87-control gap. Capture: top stats, family coverage bars, and the toolbar showing the four export buttons. A second optional screenshot — `03b-gap-control-detail.png` — expands one control row (e.g. AC-2(5)) to show the NIST statement + starter implementation language.

**Speaker notes (~80 sec):**
- Pick a **From** (current) and **To** (target) baseline; the tool computes the exact set difference. Not fuzzy crosswalks — set differences over authoritative OSCAL membership.
- Three views: **Gap** (what to add), **Covered** (overlap), **Beyond target** (drops on a downgrade).
- Coverage by family, sorted by gap size — tells you where the lift is concentrated. Moderate → High is heavy in CP, IR, SC, SI.
- Click any control to expand: authoritative **NIST statement**, **discussion**, and **starter implementation language** — family-tailored draft, explicitly labeled as a draft needing 3PAO validation.
- DoD IL2/IL4/IL5/IL6 overlays available — advisory only (CC SRG v1r4 + CNSSI 1253), with an in-page banner that makes that explicit.
- **Four exports** of the current view: CSV (triage), Executive Brief (printable one-pager for leadership / 3PAO kickoff), Implementation Plan (printable per-family work plan with starter language), Markdown (Confluence/Notion paste).

**Action items to land here (say out loud):**
- **Pick the next-ATO target and date.** Moderate → High is the obvious next step (87 controls). We need an explicit "by when" so this isn't a forever-aspirational plan.
- **Export the Implementation Plan into Jira this week** and assign family-leads (AC, AU, CM, CP, IR, SC, SI carry most of the lift). The plan is generated; it just needs owners.
- **3PAO check on starter language.** The implementation drafts are starter text, not control responses — get our 3PAO contact to review one family (suggest CP, which is heavy on policy) end-to-end before we scale the pattern.
- **Decide on IL overlays.** If DoD IL4/IL5 is on the roadmap, flag it now so we start tracking those deltas alongside FedRAMP; otherwise we de-scope the IL banner.

**Hierarchy element to call out:** this is the tool that turns "we want a High ATO" into "here are the 87 controls, grouped by family, with draft language and an exportable plan."

---

## Capture checklist (do before the call)

- [ ] `01-launcher.png` — `index.html`, full window
- [ ] `02-dashboard-posture.png` — `dashboard.html`, Posture tab, High chip selected
- [ ] `03-gap-moderate-to-high.png` — `gap.html`, Moderate → High, top of page through family bars
- [ ] `03b-gap-control-detail.png` (optional) — expanded control row showing the implementation language

Run `dashboard.html` and `gap.html` locally with a clean window (no devtools, no bookmarks bar) for clean grabs.

## Demo flow after the slides

After Slide 3, switch to the live tools in this order:
1. `dashboard.html` — flip the Posture chips, hit Intake Feed, show one control card in the Controls tab.
2. `gap.html` — same Moderate → High setup, expand a control, click **Implementation Plan** to open the printable report in a new tab.
3. (Optional) `backend/` — `curl http://localhost:8787/review/queue | jq` if the backend is running, to show the loop end-to-end.

---

## Action Items — keep this on a backup slide (Slide 4 or speaker-notes wrap)

The federal landscape doesn't sit still: FedRAMP Rev5 baselines, DoD CC SRG, CNSSI 1253, OMB memos, and Federal Register rules all move on their own clocks. The tool only matters if the **operating cadence** behind it is real. These are the asks coming out of this demo.

### Now (this week)

| # | Item | Owner | Why it can't wait |
|---|------|-------|-------------------|
| 1 | Land `backend/` on `main` (with `.gitignore` for `data/`, `outbox/`, `.venv/`) | Eng | Currently untracked; not reviewable by anyone but me |
| 2 | Revert the `CONTROLS_API='http://localhost:8787'` override in `dashboard.html` before next Pages deploy | Eng | Local-dev string would break the public site |
| 3 | Provision **Anthropic API key** + **Slack bot** (with scoped permissions) | IT / Sec | Classifier is mocked and review queue writes to disk until these land |
| 4 | Name an **intake-loop owner** + on-call rotation | Compliance | Without a name, "we should have caught NTC-0014" repeats |

### Near (next 2–4 weeks)

| # | Item | Owner | Outcome |
|---|------|-------|---------|
| 5 | Wire Intake Feed / Action Board / Review tabs to the live backend (not hardcoded arrays) | Eng | Dashboard goes from demo to daily-use |
| 6 | Define **review SLAs**: FedRAMP notices 1 business day, community RFCs 5, Federal Register triaged weekly | Compliance | Items don't rot in the queue |
| 7 | Export Moderate → High **Implementation Plan** into Jira; assign family-leads (AC, AU, CM, CP, IR, SC, SI) | Compliance + Eng | Plan stops being a PDF and starts having owners |
| 8 | 3PAO walkthrough of one family's starter implementation language (suggest CP) | Compliance | Validate the draft pattern before scaling |
| 9 | Pick & publish the **next-ATO target + date** (Moderate → High?) | Leadership | Without a date, the gap tool is decoration |

### Ongoing (operating cadence)

| # | Item | Cadence | Why |
|---|------|---------|-----|
| 10 | Re-pull FedRAMP OSCAL profiles + NIST 800-53 catalog | Quarterly | Upstream changes happen; tool must reflect them |
| 11 | Re-validate DoD IL overlay deltas vs. current CC SRG + CNSSI 1253 | Quarterly | Hand-curated; explicitly advisory until reverified |
| 12 | Audit `outbox/` (or Slack archive once wired) for items that bypassed review | Monthly | Confirms the human-in-the-loop invariant is holding |
| 13 | Review POA&M aging on Posture tab | Bi-weekly | Open POA&Ms are the long pole on the next ATO |
| 14 | Triage Federal Register hits relevant to FedRAMP scope | Weekly | Most federal-space change shows up here first |

### Decision gates (need a yes/no in this meeting)

- **DoD IL roadmap** — do we track IL4/IL5 alongside FedRAMP, or de-scope the IL overlay tab? Affects how much CC SRG / CNSSI 1253 effort we put on the calendar.
- **Backend hosting** — local + on-demand for now, or commit to the AWS shape (Lambda + EventBridge + DynamoDB) this quarter?
- **Cross-framework catalogs** — `gap.html`'s parallel-catalog architecture is ready for SOC 2 / ISO 27001. Worth doing, or pure FedRAMP focus through the next ATO?

### How to read this list

Most of the federal-space risk is in the **cadence** rows, not the **build** rows. The tool's value compounds only if the quarterly OSCAL refresh, the weekly Federal Register triage, and the named intake owner are all in place. Without them, Lighthouse becomes another well-intentioned dashboard that drifts six months out of date.
