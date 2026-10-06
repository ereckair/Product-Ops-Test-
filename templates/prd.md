---
# ── Identity ───────────────────────────────────────────────
id: PRD-<DOMAIN>-<NNN>            # e.g. PRD-SQ-014. Stable, never reused.
title: <Product / capability name>
version: 0.1
status: draft                      # draft | in-review | approved | superseded
# ── Ownership (drives site publishing + CODEOWNERS) ───────
domain: <sq | sales | gtm | hr | manufacturing | ...>
value_stream: <design | plan | make | enable>
product_owner: <name>              # L1
product_leader: <name>             # L2
# ── Origin & traceability ──────────────────────────────────
origin:
  jpd_idea: <JPD-123>              # Jira Product Discovery idea, if any
  sources: []                      # links to email / Teams thread / deck
jira:
  initiative: <KEY-1>              # written back by sync — do not edit
# ── Strategic alignment ────────────────────────────────────
kpis: []                           # from The Ten: otif | order_to_delivery_lead_time |
                                   # cost_per_unit_delivered | cash_conversion_cycle |
                                   # contacts_per_delivered_unit | brand_health | vitality |
                                   # workforce_stability | growth_to_plan | margin_to_plan
# ── Approval ───────────────────────────────────────────────
jira_extra: {}                     # values for extra Jira fields mapped in domain.yaml, e.g.
                                   #   finance_id: FIN-123
                                   #   v2030_capabilities: [Quality Intelligence]
approved_by: []                    # product leader, set in the approval PR
approved_on:
---

# <Title>

<!-- AGENT: Only `approved` status triggers Jira sync. Every requirement needs a stable REQ-ID.
     Do not include technical design here — architecture, data model, deployment belong in the TDD. -->

## 1. TL;DR

<!-- 2–3 sentences: the problem, who has it, what we will build, and the expected outcome. -->

## 2. Problem & Context

<!-- What is broken today, for whom, and how we know (data, incidents, cost). Link evidence. -->

## 3. Goals

### 3.1 Business goals

| # | Goal | KPI (The Ten) | Baseline | Target | By when |
|---|------|---------------|----------|--------|---------|
| G1 | | | | | |

### 3.2 User goals

<!-- 3–5 outcomes for the end user, phrased as outcomes not features. -->

### 3.3 Non-goals

<!-- 2–3 items explicitly out of scope. Prevents scope creep in Jira. -->

## 4. Users & Personas

| Persona | Role / team | Primary need | Volume (users) |
|---------|-------------|--------------|----------------|
| | | | |

## 5. Requirements

<!-- AGENT: This whole PRD becomes ONE Jira EPIC. Each REQ becomes a STORY under it.
     Capability areas (AREA-NN) group requirements and become a label on each story.
     Acceptance criteria become the story's AC verbatim. Priority uses MoSCoW.
     Story points are NOT set here — they are computed after TDD approval. -->

### AREA-01: <Capability area>

#### REQ-001 · <Short requirement name>
- **Priority:** Must | Should | Could
- **Persona:** <persona>
- **Story:** As a <persona>, I want to <action>, so that <benefit>.
- **Acceptance criteria:**
  - Given <context>, when <action>, then <result>.
  - Given <context>, when <action>, then <result>.
- **Notes / business rules:** <optional>

#### REQ-002 · <Short requirement name>
- **Priority:**
- **Persona:**
- **Story:**
- **Acceptance criteria:**
  -

### AREA-02: <Capability area>

#### REQ-003 · <Short requirement name>
- **Priority:**
- **Persona:**
- **Story:**
- **Acceptance criteria:**
  -

## 6. User Experience

### 6.1 Entry point & first use
<!-- How users find and access it (OneAshley host menu, Teams, link). Onboarding. -->

### 6.2 Core flow
<!-- Step by step. Reference REQ-IDs at each step. -->
1. **<Step>** — <what the user does / sees> (REQ-001)
2. **<Step>** — (REQ-002)

### 6.3 Edge cases & error states
<!-- Empty states, permission denied, partial data, upstream system down. -->

### 6.4 UX standards
<!-- Must use @one-ashley/design-system. Note any accessibility, i18n (EN/ZH), or device needs. -->

## 7. Business Constraints & Dependencies

<!-- Business-level only. Technical integration detail goes in the TDD. -->
- **Systems touched:** <e.g. SMMS, PLM/PIM, QIS, CTMS>
- **Compliance / regulatory:** <e.g. CPSC, CARB, data residency>
- **Data sensitivity:** <public | internal | confidential | restricted>
- **Dependent teams / products:** <team — what we need — by when>

## 8. Success Metrics

| Metric | Type | Definition / how measured | Target | KPI link |
|--------|------|---------------------------|--------|----------|
| | Adoption | | | |
| | Business | | | |
| | Quality | | | |

### 8.1 Tracking plan
<!-- Events to instrument (via @one-ashley/observability). Event name → trigger → properties. -->

## 9. Release Plan

| Phase | Scope (AREA / REQ) | Target date | Exit criteria |
|-------|--------------------|-------------|---------------|
| MVP | | | |
| Phase 2 | | | |

<!-- AGENT: Do not estimate team size or effort here. Effort comes from story points after TDD approval. -->

## 10. Risks & Open Questions

| # | Item | Type (risk / question) | Owner | Due | Resolution |
|---|------|------------------------|-------|-----|------------|
| 1 | | | | | |

## 11. Decision Log

| Date | Decision | Made by | Context |
|------|----------|---------|---------|
| | | | |

## 12. Sign-off

| Role | Name | Date |
|------|------|------|
| Product owner (L1) | | |
| Product leader (L2) — approver | | |
