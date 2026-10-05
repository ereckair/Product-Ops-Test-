---
id: PRD-SQ-001
title: Sample Request Tracker (example)
version: 0.2
status: in-review
domain: sq
value_stream: make
product_owner: Example PM
product_leader: Example Director
origin:
  jpd_idea: null
  sources: []
jira:
  initiative: null
kpis: [order_to_delivery_lead_time, cost_per_unit_delivered]
approved_by: []                    # product leader, set in the approval PR
approved_on:
---

# Sample Request Tracker (example)

> Fictional example used to test the toolchain. Replace or delete before real use.

## 1. TL;DR

Sourcing teams track supplier sample requests in spreadsheets, so samples are late and nobody sees status. We will build a tracker where buyers create requests and suppliers update status, cutting sample cycle time.

## 2. Problem & Context

Sample status lives in email and spreadsheets; buyers chase suppliers manually.

## 3. Goals

### 3.1 Business goals

| # | Goal | KPI (The Ten) | Baseline | Target | By when |
|---|------|---------------|----------|--------|---------|
| G1 | Reduce sample cycle time | order_to_delivery_lead_time | 21 days | 14 days | Q2 |

### 3.2 User goals

Buyers see every open sample request and its status in one place.

### 3.3 Non-goals

Sample cost approval workflow.

## 4. Users & Personas

| Persona | Role / team | Primary need | Volume (users) |
|---------|-------------|--------------|----------------|
| Buyer | Sourcing | Track requests | 40 |
| Supplier | External | Update status | 200 |

## 5. Requirements

### EPIC-01: Request management

#### REQ-001 · Create sample request
- **Priority:** Must
- **Persona:** Buyer
- **Story:** As a buyer, I want to create a sample request for an item and supplier, so that the request is tracked from day one.
- **Acceptance criteria:**
  - Given I am a buyer, when I submit item number, supplier, and due date, then a request is created with status "Requested".
  - Given a required field is missing, when I submit, then I see which field is missing.

#### REQ-002 · View open requests
- **Priority:** Must
- **Persona:** Buyer
- **Story:** As a buyer, I want to see all my open requests with status and due date, so that I know what to chase.
- **Acceptance criteria:**
  - Given I have open requests, when I open the tracker, then I see them sorted by due date with overdue ones highlighted.

### EPIC-02: Supplier updates

#### REQ-003 · Supplier updates status
- **Priority:** Should
- **Persona:** Supplier
- **Story:** As a supplier, I want to update the status of a request, so that the buyer knows when the sample ships.
- **Acceptance criteria:**
  - Given a request assigned to me, when I set status to "Shipped" with a tracking number, then the buyer sees the update.

## 6. User Experience

### 6.1 Entry point & first use
Menu item in the OneAshley host.

### 6.2 Core flow
1. **Create** — buyer fills the request form (REQ-001)
2. **Track** — buyer views list (REQ-002)

### 6.3 Edge cases & error states
Supplier not found; item number invalid.

### 6.4 UX standards
@one-ashley/design-system; EN/ZH.

## 7. Business Constraints & Dependencies

- **Systems touched:** SMMS (supplier master)
- **Compliance / regulatory:** none
- **Data sensitivity:** internal
- **Dependent teams / products:** none

## 8. Success Metrics

| Metric | Type | Definition / how measured | Target | KPI link |
|--------|------|---------------------------|--------|----------|
| Cycle time | Business | request created → sample received | 14 days | order_to_delivery_lead_time |

### 8.1 Tracking plan
request_created, status_changed.

## 9. Release Plan

| Phase | Scope (EPIC / REQ) | Target date | Exit criteria |
|-------|--------------------|-------------|---------------|
| MVP | EPIC-01 | Q1 | Buyers using it |

## 10. Risks & Open Questions

| # | Item | Type (risk / question) | Owner | Due | Resolution |
|---|------|------------------------|-------|-----|------------|
| 1 | Supplier login method | question | Example PM | | |

## 11. Decision Log

| Date | Decision | Made by | Context |
|------|----------|---------|---------|
| | | | |

## 12. Sign-off

| Role | Name | Date |
|------|------|------|
| Product owner (L1) | | |
