"""Seed the DB with classifications produced by Claude-the-chat-LLM.

This is a stand-in for what the live `pipeline.classify` will produce once an
ANTHROPIC_API_KEY is configured. Each entry in CLASSIFICATIONS was produced
by the same model that you talk to in chat, reading the actual notice
markdown — so dates, phases, and acceptance criteria are real.

Run:
    .venv/bin/python scripts/seed_chat_classifications.py

The dashboard will then show fully-populated cards, kanban tasks with real
due dates, and a review queue that looks like the production output.
"""
from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

# Allow running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lighthouse.models import Briefing, Draft, EpicDraft, ReviewRecord, ReviewStatus, StoryDraft
from lighthouse.store import Store


def _D(s: str) -> date:
    return date.fromisoformat(s)


CLASSIFICATIONS: dict[str, dict] = {
    # ====================================================================
    "NTC-0014": {
        "epic": EpicDraft(
            summary="FedRAMP VDR/VER mandatory by 2026-12-07 (CISA BOD 26-04 response)",
            description=(
                "FedRAMP is accelerating mandatory adoption of the Vulnerability Detection and "
                "Response (VDR) and Vulnerability Evaluation and Reporting (VER) rule sets to "
                "align with CISA Binding Operational Directive 26-04, issued 2026-06-10.\n\n"
                "Effective 2026-12-07: VDR and VER are mandatory for any cloud offering obtaining "
                "or maintaining FedRAMP Certification. Grace period through 2027-03-07 with a "
                "corrective action plan and notice to all authorizing agencies. After 2027-03-07, "
                "FedRAMP Certification will be revoked for non-compliant offerings.\n\n"
                "Source: https://fedramp.gov/notices/0014"
            ),
            labels=["fedramp", "compliance", "bod-26-04", "vdr", "ver", "vulnerability-management", "ntc-0014"],
            due_date=_D("2027-03-07"),
            priority="Highest",
        ),
        "stories": [
            StoryDraft(
                summary="Confirm final VDR/VER rule text and distribute internally",
                description="FedRAMP will finalize the Consolidated Rules for 2026 by end of June 2026. Capture final text within 48h of release, diff against preview, and circulate to compliance/security/product/legal.",
                acceptance_criteria=[
                    "Final VDR and VER rules captured within 48 hours of publication",
                    "Diff between preview and final text documented",
                    "Annotated copy circulated to compliance, security engineering, product, and legal",
                    "FedRAMP Security Inbox subscription confirmed",
                ],
                priority="Highest",
                labels=["fedramp", "vdr", "ver", "phase-immediate", "ntc-0014"],
                due_date=_D("2026-07-05"),
                phase="Immediate",
            ),
            StoryDraft(
                summary="VDR/VER gap assessment vs. current ConMon program",
                description="Written assessment comparing current vulnerability management against VER-EVA-EIR, VER-EVA-ELX, VER-EVA-EFA, VER-EVA-AIA, VDR-TFR-KEV, VDR-CSO-RES.",
                acceptance_criteria=[
                    "One-page-per-sub-rule gap matrix produced",
                    "KEV remediation SLA gap quantified against CISA timelines",
                    "Tooling gaps listed with buy/build call for each",
                    "Risk-ranked remediation backlog drafted",
                    "Output reviewed with 3PAO before Phase 2",
                ],
                priority="Highest",
                labels=["fedramp", "vdr", "ver", "gap-analysis", "phase-immediate", "ntc-0014"],
                due_date=_D("2026-07-15"),
                phase="Immediate",
            ),
            StoryDraft(
                summary="Implement continuous vuln detection (replace monthly scan)",
                description="Stand up continuous detection across all in-boundary assets. FedRAMP has explicitly called the legacy monthly cadence insufficient.",
                acceptance_criteria=[
                    "Continuous scanning enabled on 100% of in-boundary hosts/containers/services",
                    "Scan freshness SLA defined and monitored",
                    "Coverage report generated weekly",
                    "Legacy monthly scan job decommissioned only after coverage validated",
                ],
                priority="Highest",
                labels=["fedramp", "vdr", "conmon", "phase-short-term", "ntc-0014"],
                due_date=_D("2026-09-15"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Implement VER-EVA-EIR: internet-reachability evaluation",
                description="Tag every asset with internet-reachability state, refresh daily, propagate to vuln findings and agency reports.",
                acceptance_criteria=[
                    "Every asset tagged daily with reachability state",
                    "Findings inherit reachability state at ingestion",
                    "State surfaced in remediation queue + agency reports",
                    "Test cases verify state changes propagate within SLA",
                ],
                priority="High",
                labels=["fedramp", "ver", "internet-reachability", "phase-short-term", "ntc-0014"],
                due_date=_D("2026-09-30"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Implement VER-EVA-ELX + VER-EVA-EFA + VER-EVA-AIA",
                description="Integrate KEV status, exploit availability, automation indicators, and technical impact into triage. Default automatable=true unless evidence indicates otherwise.",
                acceptance_criteria=[
                    "KEV catalog ingested and refreshed daily",
                    "Each finding enriched with KEV/exploit/automation/impact factors",
                    "Triage queue sorts by combined VER risk signal, not raw CVSS",
                    "Automation override workflow with immutable audit log",
                ],
                priority="High",
                labels=["fedramp", "ver", "kev", "exploitability", "phase-short-term", "ntc-0014"],
                due_date=_D("2026-10-15"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Implement VDR-TFR-KEV: KEV remediation on BOD timelines",
                description="Wire SLAs and automation so KEV-flagged vulns hit BOD-mandated timelines, with documented exception path.",
                acceptance_criteria=[
                    "KEV findings auto-assigned with BOD-aligned due date",
                    "SLA breach alerts route to on-call and service owner",
                    "Technical exception workflow gated on written justification",
                    "Monthly KEV remediation report available for agency consumption",
                ],
                priority="Highest",
                labels=["fedramp", "vdr", "kev", "phase-short-term", "ntc-0014"],
                due_date=_D("2026-10-31"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Implement VDR-CSO-RES: ongoing mitigation workflow",
                description="Allow time-bound mitigations (e.g. 'not internet-reachable', 'not automatable') in addition to full remediation.",
                acceptance_criteria=[
                    "Mitigation states defined and time-bound",
                    "Periodic re-validation enforced",
                    "Mitigation evidence captured and tied to finding",
                    "3PAO confirms workflow satisfies VDR-CSO-RES",
                ],
                priority="High",
                labels=["fedramp", "vdr", "mitigation", "phase-short-term", "ntc-0014"],
                due_date=_D("2026-10-31"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Update SSP and ConMon documentation",
                description="Rewrite SSP control narratives (RA-5, SI-2, CA-7) and ConMon Strategy to reflect VDR + VER instead of monthly scans.",
                acceptance_criteria=[
                    "Affected SSP control narratives updated",
                    "ConMon Strategy versioned and updated",
                    "3PAO review before submission",
                    "Change log references BOD 26-04 and NTC-0014",
                ],
                priority="High",
                labels=["fedramp", "documentation", "ssp", "phase-short-term", "ntc-0014"],
                due_date=_D("2026-10-31"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="End-to-end dry run of VDR/VER pipeline",
                description="30+ days of continuous operation: detection → enrichment → triage → remediation/mitigation → reporting.",
                acceptance_criteria=[
                    "30 days continuous operation with no manual intervention for routine findings",
                    "KEV SLA hit rate at target",
                    "All four VER factors populated on >=99% of findings",
                    "Dry-run sign-off documented",
                ],
                priority="Highest",
                labels=["fedramp", "vdr", "ver", "dry-run", "phase-full-implementation", "ntc-0014"],
                due_date=_D("2026-11-15"),
                phase="Full Implementation",
            ),
            StoryDraft(
                summary="3PAO readiness review",
                description="Pre-mandate readiness review covering VDR, VER, agency reporting, and updated docs.",
                acceptance_criteria=[
                    "3PAO scope/SOW signed",
                    "Readiness review complete with written findings",
                    "All blocking findings resolved before 2026-12-07",
                    "Non-blocking findings logged for post-mandate",
                ],
                priority="Highest",
                labels=["fedramp", "3pao", "audit", "phase-full-implementation", "ntc-0014"],
                due_date=_D("2026-11-30"),
                phase="Full Implementation",
            ),
            StoryDraft(
                summary="Go-live: VDR + VER mandatory",
                description="Formal go-live; offering operates fully under VDR and VER as of 2026-12-07.",
                acceptance_criteria=[
                    "Compliance attestation signed by security and compliance leads",
                    "Go-live announced to authorizing agencies",
                    "Monitoring dashboards green for first 7 days",
                    "Day-1 issues triaged within 24h",
                ],
                priority="Highest",
                labels=["fedramp", "go-live", "phase-full-implementation", "ntc-0014"],
                due_date=_D("2026-12-07"),
                phase="Full Implementation",
            ),
            StoryDraft(
                summary="CAP contingency — activate only if slipping past 2026-12-07",
                description="If by 2026-12-01 we project slip past 2026-12-07, file a corrective action plan and notify all authorizing agencies, preserving cert through grace period.",
                acceptance_criteria=[
                    "Slip risk reviewed weekly starting 2026-11-01",
                    "If activated: CAP drafted with milestones within 5 business days",
                    "CAP submitted to FedRAMP and circulated to agencies",
                    "Weekly progress updates to agencies until CAP closure",
                ],
                priority="High",
                labels=["fedramp", "cap", "contingency", "phase-grace-period", "ntc-0014"],
                due_date=_D("2027-02-15"),
                phase="Grace Period",
            ),
            StoryDraft(
                summary="Final compliance verification before hard deadline",
                description="Pre-2027-03-07 verification that VDR/VER are operational, any CAP items closed, no offering at risk of revocation.",
                acceptance_criteria=[
                    "Independent internal audit complete",
                    "Open CAP items closed and documented",
                    "Written attestation from security and compliance leads",
                    "Compliance posture confirmation sent to agencies",
                ],
                priority="Highest",
                labels=["fedramp", "audit", "phase-grace-period", "ntc-0014"],
                due_date=_D("2027-03-01"),
                phase="Grace Period",
            ),
        ],
        "briefing": Briefing(
            plain_summary=(
                "CISA BOD 26-04 (2026-06-10) reprioritizes vuln remediation by exposure, KEV, automatability, "
                "and impact. FedRAMP responded by accelerating VDR + VER from June 2027 to 2026-12-07 mandatory, "
                "with a grace period through 2027-03-07. After that date, certification is revoked."
            ),
            consequences="Loss of FedRAMP Certification on 2027-03-07, ending federal sales under that authorization.",
            phase_briefings={
                "Immediate": "Final VDR/VER text drops end of June. Lock in a gap assessment by 2026-07-15.",
                "Short-Term": "Build the continuous-detection pipeline + four VER evaluation factors. Update SSP/ConMon by 2026-10-31.",
                "Full Implementation": "Dry run, 3PAO readiness, go-live by 2026-12-07.",
                "Grace Period": "Treat 2027-03-07 as the real deadline. CAP is the safety net, not the plan.",
            },
        ),
    },
    # ====================================================================
    "NTC-0013": {
        "epic": EpicDraft(
            summary="Rev5 baseline overhaul (RFC-0026..0030) — adopt by 2027-01-01 assessment",
            description=(
                "FedRAMP is removing the vast majority of FedRAMP-assigned control parameter values "
                "and most FedRAMP-specific control guidance from Rev5 baselines in the Consolidated "
                "Rules for 2026. New Certification Package (Certification Package Overview, Security "
                "Decision Record, Secure Configuration Guide) replaces SSP/SAR/CIS-CRM.\n\n"
                "Mandatory: all current Rev5 Certified offerings adopt during the first independent "
                "assessment after 2027-01-01. New Rev5 submissions after 2027-01-01 must meet new "
                "rules. New Rev5 submissions stop entirely on 2027-06-11.\n\n"
                "Source: https://fedramp.gov/notices/0013"
            ),
            labels=["fedramp", "rev5", "baseline", "certification-package", "ntc-0013"],
            due_date=_D("2027-01-01"),
            priority="Highest",
        ),
        "stories": [
            StoryDraft(
                summary="Inventory current FedRAMP-assigned control parameters in our SSP",
                description="Identify every control where we've inherited a FedRAMP-assigned value vs. our actual operational reality.",
                acceptance_criteria=[
                    "Every Rev5 control parameter cataloged",
                    "Actual operational value documented per control",
                    "Drift between FedRAMP-assigned and actual flagged",
                    "Output reviewed with 3PAO",
                ],
                priority="High",
                labels=["fedramp", "rev5", "ssp", "phase-immediate", "ntc-0013"],
                due_date=_D("2026-08-31"),
                phase="Immediate",
            ),
            StoryDraft(
                summary="Author Certification Package Overview replacing legacy SSP intro",
                description="Replace traditional SSP narrative with the new Certification Package Overview format per the Public Preview spec.",
                acceptance_criteria=[
                    "Cert Package Overview drafted per preview.fedramp.gov/2026 reference",
                    "Boundary description aligned with Minimum Assessment Scope",
                    "Reviewed by compliance + 3PAO",
                    "Stored in source-controlled doc repo",
                ],
                priority="High",
                labels=["fedramp", "rev5", "certification-package", "phase-short-term", "ntc-0013"],
                due_date=_D("2026-10-31"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Author Security Decision Record replacing control implementations",
                description="Migrate control implementation content into the new Security Decision Record format with rules, Rev5 controls, and KSIs.",
                acceptance_criteria=[
                    "All Rev5 controls migrated into SDR format",
                    "FedRAMP Practices, rules, and KSIs cross-referenced",
                    "Reviewed by control owners and 3PAO",
                ],
                priority="High",
                labels=["fedramp", "rev5", "sdr", "phase-short-term", "ntc-0013"],
                due_date=_D("2026-11-30"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Author Secure Configuration Guide replacing CIS/CRM",
                description="Replace Control Implementation Summary and Customer Responsibility Matrix with the new Secure Configuration Guide.",
                acceptance_criteria=[
                    "SCG drafted per 2026 reference",
                    "Customer responsibilities clearly delimited",
                    "Reviewed with at least one agency customer",
                ],
                priority="Medium",
                labels=["fedramp", "rev5", "scg", "phase-short-term", "ntc-0013"],
                due_date=_D("2026-12-15"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Adopt new baseline at next independent assessment after 2027-01-01",
                description="Confirm that the assessment scoped after 2027-01-01 uses CR2026 baseline (parameters self-assigned, hidden control guidance gone, new package format).",
                acceptance_criteria=[
                    "Assessment kickoff explicitly references CR2026",
                    "All three new docs delivered to assessor",
                    "Assessor signs off on new format",
                ],
                priority="Highest",
                labels=["fedramp", "rev5", "phase-full-implementation", "ntc-0013"],
                due_date=_D("2027-03-31"),
                phase="Full Implementation",
            ),
        ],
        "briefing": Briefing(
            plain_summary="FedRAMP is stripping most FedRAMP-assigned control parameters and FedRAMP-specific guidance from Rev5, replacing the SSP/SAR/CIS-CRM with a new three-document Certification Package. Mandatory at the first assessment after 2027-01-01; new Rev5 cuts off 2027-06-11.",
            consequences="Failure to migrate by next post-2027-01-01 assessment will fail the assessment.",
            phase_briefings={
                "Immediate": "Inventory parameters; we can't migrate what we haven't catalogued.",
                "Short-Term": "Three new documents to author by end of 2026.",
                "Full Implementation": "Land the new format at the next independent assessment.",
            },
        ),
    },
    # ====================================================================
    "NTC-0012": {
        "epic": EpicDraft(
            summary="Updated Incident Communications Procedures — Rev5 mandatory by 2027-01-01",
            description=(
                "Updated FedRAMP Incident Communications Procedures take effect 2026-07-04. "
                "20x certifications: mandatory 2026-07-04. Rev5 and pilot 20x: mandatory 2027-01-01.\n\n"
                "Key changes: 'Potential Adverse Impact' renamed 'Potential Agency Impact' (PAIN); "
                "Adverse Effects renamed Customer Effects (Debilitating/Disruptive/Narrow/Minimal); "
                "report timeframes scale by Certification Class — Class D N5/N4/N3 = 15min IIR, 3hr "
                "OIR, 3hr FIR; CSPs no longer report incidents directly to CISA; automated incident "
                "communication strongly encouraged.\n\nSource: https://fedramp.gov/notices/0012"
            ),
            labels=["fedramp", "incident-response", "rev5", "rfc-0031", "ntc-0012"],
            due_date=_D("2027-01-01"),
            priority="Highest",
        ),
        "stories": [
            StoryDraft(
                summary="Rewrite Incident Response Plan against new ICP terminology",
                description="Replace 'Potential Adverse Impact' with 'Potential Agency Impact' (PAIN), Adverse Effects with Customer Effects, and reflect that incidents are no longer reported directly to CISA.",
                acceptance_criteria=[
                    "IRP terminology updated through every section",
                    "PAIN rating method documented or default-PAIN5 path adopted",
                    "CISA reporting removed from CSP playbook",
                    "Legal reviewed for legacy contract conflicts",
                ],
                priority="High",
                labels=["fedramp", "incident-response", "phase-immediate", "ntc-0012"],
                due_date=_D("2026-08-31"),
                phase="Immediate",
            ),
            StoryDraft(
                summary="Implement Class-based incident report timeframes",
                description="Configure incident management to enforce Class D 15min IIR, 3hr OIR, 3hr FIR (and Class C / B equivalents).",
                acceptance_criteria=[
                    "Per-class timers configured in incident management tool",
                    "Initial Incident Report template captures likely affected agency customers",
                    "Tabletop exercise hits all three timeframes",
                    "Breach alerts route to incident commander + on-call",
                ],
                priority="Highest",
                labels=["fedramp", "incident-response", "phase-short-term", "ntc-0012"],
                due_date=_D("2026-10-31"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Implement automated incident reporting (ICP-CSO-AIR)",
                description="Build automated, status-driven incident notifications to all affected parties — no hand-crafted artisanal emails.",
                acceptance_criteria=[
                    "Automated trigger on incident status transitions",
                    "Notifications include all required fields per IIR/OIR/FIR rules",
                    "Send-to list dynamically resolves affected agency customers",
                    "Audit trail of every send",
                ],
                priority="High",
                labels=["fedramp", "incident-response", "automation", "phase-short-term", "ntc-0012"],
                due_date=_D("2026-11-30"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Go-live: Rev5 ICP mandatory adoption",
                description="Confirm new ICP is live and operational by 2027-01-01.",
                acceptance_criteria=[
                    "Final IRP version published",
                    "All on-call engineers trained on new timeframes",
                    "Quarterly tabletop run against new ICP",
                ],
                priority="Highest",
                labels=["fedramp", "incident-response", "phase-full-implementation", "ntc-0012"],
                due_date=_D("2027-01-01"),
                phase="Full Implementation",
            ),
        ],
        "briefing": Briefing(
            plain_summary="New incident communications procedures effective 2026-07-04 (mandatory for Rev5 by 2027-01-01). PAIN rating replaces PAI; Class D incidents now require 15min initial reports; CSPs stop reporting to CISA; automated comms strongly encouraged.",
            consequences="Misaligned incident reporting risks agency customer exits and FedRAMP corrective action.",
            phase_briefings={
                "Immediate": "IRP rewrite first — terminology drift will block everything downstream.",
                "Short-Term": "Wire Class-based timers and automated comms.",
                "Full Implementation": "Live by 2027-01-01.",
            },
        ),
    },
    # ====================================================================
    "NTC-0010": {
        "epic": EpicDraft(
            summary="CISA ED 25-03 Cisco device emergency response — REPORT BY 2026-04-29",
            description=(
                "CISA Emergency Directive 25-03 requires identification, evaluation, and remediation "
                "of Cisco Firepower 1000/2100/4100/9300 and Secure Firewall 200/1200/3100/4200/6100 "
                "series devices for indicators of compromise.\n\n"
                "REQUIRED ACTIONS: identify in-scope devices; evaluate for IOCs; if no IOCs apply "
                "patches by 2026-04-24 23:59 EST; perform hard reset by 2026-04-29; report status "
                "to FedRAMP by 2026-04-29 17:00 ET.\n\nSource: https://fedramp.gov/notices/0010"
            ),
            labels=["fedramp", "emergency", "cisa-ed-25-03", "vuln-management", "ntc-0010"],
            due_date=_D("2026-04-29"),
            priority="Highest",
        ),
        "stories": [
            StoryDraft(
                summary="Inventory Cisco Firepower / Secure Firewall devices in FedRAMP boundary",
                description="Confirm whether any in-scope Cisco devices exist within the boundary.",
                acceptance_criteria=[
                    "Boundary inventory queried for affected models",
                    "Result (in-scope vs. out-of-scope) documented",
                    "Result attached to FedRAMP response form",
                ],
                priority="Highest",
                labels=["fedramp", "emergency", "phase-immediate", "ntc-0010"],
                due_date=_D("2026-04-24"),
                phase="Immediate",
            ),
            StoryDraft(
                summary="Patch all in-scope devices by 2026-04-24 23:59 EST",
                description="Apply Cisco-provided patches for CVE-2025-20333, CVE-2025-20362, and the persistence patch.",
                acceptance_criteria=[
                    "All in-scope devices patched by deadline",
                    "Patch evidence captured (version, timestamp)",
                    "Hard reset performed by 2026-04-29",
                ],
                priority="Highest",
                labels=["fedramp", "emergency", "patching", "phase-immediate", "ntc-0010"],
                due_date=_D("2026-04-29"),
                phase="Immediate",
            ),
            StoryDraft(
                summary="File ED 25-03 response with FedRAMP by 2026-04-29 17:00 ET",
                description="Complete the FedRAMP V1: ED 25-03 Response Form and upload supplemental info to Incident Response folder.",
                acceptance_criteria=[
                    "Response form submitted before 2026-04-29 17:00 ET",
                    "Supplemental file ED-25-03-V1-Response-[FRID] uploaded",
                    "Agency customer AOs/ISSOs notified",
                ],
                priority="Highest",
                labels=["fedramp", "emergency", "phase-immediate", "ntc-0010"],
                due_date=_D("2026-04-29"),
                phase="Immediate",
            ),
        ],
        "briefing": Briefing(
            plain_summary="CISA Emergency Directive — Cisco Firepower / Secure Firewall hunt + patch + report. Hard deadlines: patch 2026-04-24, hard reset 2026-04-29, FedRAMP report 2026-04-29 17:00 ET.",
            consequences="Public corrective action notice for non-compliance with FedRAMP Security Inbox rules.",
            phase_briefings={
                "Immediate": "All work in this epic is Immediate. The clock is hours, not weeks.",
            },
        ),
    },
    # ====================================================================
    "NTC-0009": {
        "epic": EpicDraft(
            summary="Rev5 Machine-Readable Packages — Class D mandatory by 2027-11-01",
            description=(
                "FedRAMP requires comprehensive machine-readable authorization data for Class D "
                "(High) certifications, with phased mandatory adoption dates:\n"
                "- 2027-01-01: Significant Change Notifications + Minimum Assessment Scope\n"
                "- 2027-04-02: Collaborative Continuous Monitoring\n"
                "- 2027-06-01: Vulnerability Detection and Response\n"
                "- 2027-08-01: Authorization Data Sharing (Connect.gov retired)\n"
                "- 2027-11-01: Class D comprehensive machine-readable data; Class A/B/C "
                "semi-structured text\n\n"
                "Source: https://fedramp.gov/notices/0009"
            ),
            labels=["fedramp", "rev5", "machine-readable", "oscal", "ntc-0009"],
            due_date=_D("2027-11-01"),
            priority="High",
        ),
        "stories": [
            StoryDraft(
                summary="Adopt Significant Change Notifications + Minimum Assessment Scope",
                description="Mandatory for all Rev5 services by 2027-01-01.",
                acceptance_criteria=[
                    "SCN process documented and operational",
                    "Boundary materials migrated to Minimum Assessment Scope",
                    "Old significant-change-request workflow retired",
                ],
                priority="High",
                labels=["fedramp", "rev5", "scn", "mas", "phase-short-term", "ntc-0009"],
                due_date=_D("2027-01-01"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Adopt Collaborative Continuous Monitoring by 2027-04-02",
                description="Replace part of traditional monthly ConMon with the CCM Balance Improvement Release.",
                acceptance_criteria=[
                    "CCM rules implemented",
                    "Evidence cadence updated",
                    "3PAO confirms CCM-compliant",
                ],
                priority="High",
                labels=["fedramp", "rev5", "ccm", "phase-short-term", "ntc-0009"],
                due_date=_D("2027-04-02"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Adopt Authorization Data Sharing by 2027-08-01 (Connect.gov retiring)",
                description="Migrate to Authorization Data Sharing replacing Secure Repository.",
                acceptance_criteria=[
                    "ADS pipeline operational",
                    "Connect.gov dependency removed",
                    "Agency customers confirmed receipt",
                ],
                priority="High",
                labels=["fedramp", "rev5", "ads", "phase-short-term", "ntc-0009"],
                due_date=_D("2027-08-01"),
                phase="Short-Term",
            ),
            StoryDraft(
                summary="Class D comprehensive machine-readable data by 2027-11-01",
                description="If we hold a Class D (High) certification, deliver comprehensive machine-readable authorization data at next assessment after 2027-11-01.",
                acceptance_criteria=[
                    "Per-service authorization materials in machine-readable format",
                    "Significant changes integrated semi-annually",
                    "Initial + ongoing materials covered",
                ],
                priority="Highest",
                labels=["fedramp", "rev5", "machine-readable", "phase-full-implementation", "ntc-0009"],
                due_date=_D("2027-11-01"),
                phase="Full Implementation",
            ),
        ],
        "briefing": Briefing(
            plain_summary="Rev5 services move to machine-readable authorization data on a phased schedule. Class D services bear the largest lift; everyone retires DOCX/XLSX in favor of text-based equivalents.",
            consequences="Progressive corrective action applied quarterly for missed milestones.",
            phase_briefings={
                "Short-Term": "Three Balance Improvement Releases land in 2027 H1.",
                "Full Implementation": "Class D comprehensive machine-readable data due 2027-11-01.",
            },
        ),
    },
    # ====================================================================
    "NTC-0008": {
        "epic": EpicDraft(
            summary="FedRAMP Ready retiring 2026-07-28 — convert or relabel as Legacy",
            description=(
                "FedRAMP Ready retires 2026-07-28. After that date, no new FedRAMP Ready submissions "
                "are accepted. Existing FedRAMP Ready offerings can either convert to a Class A "
                "Certification (light-touch path) or be relabeled 'Legacy FedRAMP Ready'.\n\n"
                "Sponsorless Program Certification path opens for Rev5 Class A/B/C; Class D still "
                "requires an agency sponsor. End of life for legacy program certification is 20x "
                "Phase 5 (FY27 Q3-Q4).\n\nSource: https://fedramp.gov/notices/0008"
            ),
            labels=["fedramp", "ready", "marketplace", "ntc-0008"],
            due_date=_D("2026-07-28"),
            priority="High",
        ),
        "stories": [
            StoryDraft(
                summary="Decide: convert FedRAMP Ready to Class A vs. retain as Legacy Ready",
                description="If we hold FedRAMP Ready status, decide path before 2026-07-28.",
                acceptance_criteria=[
                    "Current Ready status confirmed with marketplace",
                    "Conversion criteria reviewed against our offering",
                    "Decision documented with rationale",
                    "Agency sponsor outreach plan if Class D path chosen",
                ],
                priority="High",
                labels=["fedramp", "ready", "phase-immediate", "ntc-0008"],
                due_date=_D("2026-07-15"),
                phase="Immediate",
            ),
            StoryDraft(
                summary="Execute conversion to Class A Certification (if applicable)",
                description="Submit Class A application before 2026-07-28 retirement of Ready submissions.",
                acceptance_criteria=[
                    "Class A package prepared per Stage 1 requirements",
                    "Submission filed before 2026-07-28",
                    "Marketplace listing updated to Class A",
                ],
                priority="High",
                labels=["fedramp", "ready", "class-a", "phase-immediate", "ntc-0008"],
                due_date=_D("2026-07-28"),
                phase="Immediate",
            ),
        ],
        "briefing": Briefing(
            plain_summary="FedRAMP Ready retires 2026-07-28. Either convert to Class A or accept the 'Legacy FedRAMP Ready' label.",
            consequences="Missing the conversion window forces the Legacy label and limits future options.",
            phase_briefings={
                "Immediate": "Decide path before 2026-07-15, file by 2026-07-28.",
            },
        ),
    },
    # ====================================================================
    "NTC-0006": {
        "epic": EpicDraft(
            summary="CISA ED 26-03 Cisco SD-WAN — closed (informational tracker)",
            description="CISA Emergency Directive 26-03 mitigation deadline was 2026-03-10. Tracking for audit history.",
            labels=["fedramp", "emergency", "cisa-ed-26-03", "ntc-0006"],
            due_date=_D("2026-03-10"),
            priority="Low",
        ),
        "stories": [
            StoryDraft(
                summary="Confirm Cisco SD-WAN ED 26-03 patch evidence is filed",
                description="Verify our response evidence is on file with FedRAMP.",
                acceptance_criteria=[
                    "Response form submission confirmed",
                    "Patch evidence stored in incident response folder",
                ],
                priority="Low",
                labels=["fedramp", "emergency", "phase-grace-period", "ntc-0006"],
                due_date=_D("2026-07-31"),
                phase="Grace Period",
            ),
        ],
        "briefing": Briefing(
            plain_summary="ED 26-03 deadline already passed. Maintain audit trail.",
            consequences="None if evidence is filed.",
            phase_briefings={"Grace Period": "Audit-only tracker."},
        ),
    },
    # ====================================================================
    "NTC-0004": {
        "epic": EpicDraft(
            summary="FedRAMP authorization labels move to Class A/B/C/D Certifications",
            description=(
                "FedRAMP impact levels move from FIPS-199 Low/Mod/High to numbered Certification "
                "Classes A-D. 'FedRAMP Certification' replaces 'FedRAMP authorization' label. "
                "Class B≈Low/Li-SaaS, Class C≈Moderate, Class D≈High; Class A is time-limited pilot.\n\n"
                "Source: https://fedramp.gov/notices/0004"
            ),
            labels=["fedramp", "marketplace", "rfc-0020", "ntc-0004"],
            due_date=_D("2026-12-31"),
            priority="Medium",
        ),
        "stories": [
            StoryDraft(
                summary="Update marketplace listing and customer-facing materials to Class labels",
                description="Migrate web copy, sales materials, and SSP cover sheet to Class A-D terminology.",
                acceptance_criteria=[
                    "Web/marketing copy updated",
                    "Marketplace listing reflects new class",
                    "Sales playbooks updated",
                    "Internal training delivered",
                ],
                priority="Medium",
                labels=["fedramp", "marketplace", "phase-short-term", "ntc-0004"],
                due_date=_D("2026-12-31"),
                phase="Short-Term",
            ),
        ],
        "briefing": Briefing(
            plain_summary="Naming change: 'authorization' → 'Certification', impact levels → Class A/B/C/D.",
            consequences="Stale terminology in agency-facing materials creates confusion and stalled procurement.",
            phase_briefings={"Short-Term": "Comms/marketing/sales sweep by end of 2026."},
        ),
    },
}


def main() -> None:
    s = Store()
    written = 0
    for item_id, parts in CLASSIFICATIONS.items():
        item = s.get_item(item_id)
        if not item:
            print(f"[skip] {item_id} not in DB")
            continue
        draft = Draft(
            item_id=item_id,
            epic=parts["epic"],
            stories=parts["stories"],
            briefing=parts["briefing"],
            classifier="claude-chat",
            created_at=datetime.utcnow(),
        )
        # Promote item.deadline to the epic's due_date if the item's deadline is None.
        if item.deadline is None and parts["epic"].due_date:
            item.deadline = parts["epic"].due_date
            from lighthouse.sources._common import derive_state
            item.state = derive_state(item.deadline)
            s.upsert_item(item)
        rec = ReviewRecord(
            item_id=item_id,
            draft=draft,
            status=ReviewStatus.PENDING,
            updated_at=datetime.utcnow(),
        )
        s.upsert_review(rec)
        written += 1
        print(f"[ok]  {item_id}: {len(draft.stories)} stories, deadline={item.deadline}")
    print(f"\n{written} drafts written.")


if __name__ == "__main__":
    main()
