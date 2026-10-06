---
# ── Identity ───────────────────────────────────────────────
id: TDD-SQ-001
prd: PRD-SQ-001
title: Sample Request Tracker — Technical Design
version: 0.1
status: draft                      # draft | in-review | approved | superseded
# ── Authorship ─────────────────────────────────────────────
tdd_mode: co-draft                 # co-draft | eng-owned (set per domain)
engineering_lead: Example Eng Lead
co_author: Example PM               # only when tdd_mode = co-draft
code_repos: [example-org/sample-request-tracker]
# ── Standards ──────────────────────────────────────────────
golden_path: true                  # follows Ashley reference stack unless deviations listed
deviations: []                     # e.g. [backend-runtime, database]
p6m:
  repo: <github org/repo>
  workloads: []                    # filled from §7.1 — used to generate infra tasks
approved_on:
---

# Sample Request Tracker — Technical Design

<!-- AGENT: Section owner tags:
     [PM]  = PM agent drafts from the PRD; engineering lead reviews.
     [ENG] = engineering lead writes; agent leaves a stub with prompts only.
     Jira TASKS are generated from §6 only after status = approved. -->

## 1. Overview  `[PM]`

<!-- Do not restate the PRD. 3–5 lines: what is being built and why, link to PRD. -->
- **PRD:** [PRD-<DOMAIN>-<NNN>](./prd.md)
- **Scope of this design:** AREA-01, AREA-02 (list of capability areas)
- **Out of scope:** <carried from PRD non-goals + technical exclusions>

## 2. Golden Path Conformance  `[PM]` `[ENG]`

<!-- Default = Ashley reference stack. Mark ✅ to conform. Any ❌ needs a rationale and an ADR in §3.3. -->

| Area | Ashley standard | Conform | Deviation rationale |
|------|-----------------|---------|---------------------|
| Frontend | OneAshley MFE (React 19, Rsbuild, Module Federation) | ✅ | |
| UI kit | `@one-ashley/design-system` only | ✅ | |
| Auth | Host principal via `@one-ashley/security` `useAuthorization`; Keycloak JWT on API | ✅ | |
| API | Contract-first oRPC + zod in `shared` package; OpenAPI generated | ✅ | |
| Backend | Hono on Node.js 22+, vertical feature slices | ✅ | |
| Data | Drizzle ORM + MySQL (owned); external sources read-only | ✅ | |
| Type safety | TS strict; no `any` / `as`; zod at boundaries | ✅ | |
| Errors | ADT + exhaustive matching; `RpcResult` envelope | ✅ | |
| Testing | Vitest (BDD), fakes for unit tests | ✅ | |
| Tooling | pnpm workspaces, Biome, commitlint | ✅ | |
| Deploy | P6M GitOps on AKS (`.platform/kubernetes`) | ✅ | |
| Packages | `@one-ashley/*` via JFrog Artifactory | ✅ | |

## 3. Architecture  `[ENG]`

### 3.1 Component view
<!-- Components and how they connect: MFE, server, ETL task, external systems. Diagram welcome (Mermaid). -->

### 3.2 Integrations

| System | Direction | Protocol | Access (R / RW) | Owner team |
|--------|-----------|----------|-----------------|------------|
| | | | | |

### 3.3 Architecture decisions (ADRs)

| ADR | Decision | Alternatives considered | Why |
|-----|----------|-------------------------|-----|
| ADR-01 | | | |

## 4. Data Model  `[ENG]`

### 4.1 Entities
```
EntityName
  - field: type (constraints)
```

### 4.2 Relationships & storage
<!-- FKs, cardinality, indexes. Owned DB vs read-only sources. Caching. Retention. -->

### 4.3 Migrations
<!-- Drizzle migration plan and rollback approach for each schema change. -->

## 5. API Contract  `[ENG]`

<!-- One row per oRPC procedure. Every procedure must trace to at least one REQ. -->

| Procedure | Input schema | Output schema | REQ | Exposed as MCP tool |
|-----------|--------------|---------------|-----|---------------------|
| `feature.action` | | | REQ-001 | Y / N |

## 6. Work Breakdown & Story Sizing  `[PM]` `[ENG]`

<!-- AGENT: This table is the source for Jira TASKS (children of the REQ story) and for STORY POINTS.
     Score each factor 0–3. Points = Fibonacci lookup of total (see rubric). Never hand-enter points. -->

### 6.1 Story sizing

| REQ | Complexity | Uncertainty | Integrations | Data / migration | Security impact | Total | Points |
|-----|-----------|-------------|--------------|------------------|-----------------|-------|--------|
| REQ-001 | 1 | 0 | 1 | 1 | 0 | 3 | 2 |
| REQ-002 | 1 | 0 | 0 | 0 | 0 | 1 | 1 |
| REQ-003 | 2 | 1 | 1 | 0 | 2 | 6 | 5 |

<details><summary>Sizing rubric (default — calibrated in the standards repo)</summary>

| Total score | 0–1 | 2–3 | 4–5 | 6–7 | 8–10 | 11–13 | 14–15 |
|-------------|-----|-----|-----|-----|------|-------|-------|
| Story points | 1 | 2 | 3 | 5 | 8 | 13 | Split the story |

</details>

### 6.2 Tasks

| Task | Parent REQ | Type | Description | Definition of done |
|------|-----------|------|-------------|--------------------|
| TASK-001 | REQ-001 | contract | [TEST] Define request.create procedure and zod schemas | Contract merged, types compile |
| TASK-002 | REQ-001 | backend | [TEST] Implement request.create service + Drizzle table | Unit tests pass with fakes |
| TASK-003 | REQ-001 | frontend | [TEST] Request form MFE page | Form validates per AC |
| TASK-004 | REQ-002 | frontend | [TEST] Open requests list with overdue highlight | Sorted by due date |
| TASK-005 | REQ-003 | backend | [TEST] Supplier status update with tracking number | Buyer sees update |

<!-- Types: frontend | backend | contract | data | infra | security | test | docs.
     Infra and security tasks from §7 and §8 are appended automatically under an "Enablement" story. -->

## 7. Deployment (P6M)  `[PM]` `[ENG]`

### 7.1 Workloads

| Workload | Kind | Image / source | Schedule | Notes |
|----------|------|----------------|----------|-------|
| <app>-server | PlatformApplication | | — | |
| <app>-etl | PlatformTask | | | |
| <app>-<job> | CronJob | | `<cron>` | |
| <app>-frontend | PlatformApplication (nginx) | | — | |

### 7.2 Frontend delivery
- **Mode:** self-host | CDN host repo (`<domain>-apps-host`)
- **Asset path:** `$hostname/apps/<app_name>/<version>/*`
- **Version retention:** last 3 releases kept for host pinning

### 7.3 Environments
<!-- dev / stg / prd overlays on a shared base. List only what differs per environment. -->

| Setting | dev | stg | prd |
|---------|-----|-----|-----|
| Replicas | | | |
| Data source | | | |

### 7.4 Networking

| Item | Value |
|------|-------|
| Ingress enabled | Y / N |
| OIDC (OAuth2 proxy) | on (default) / off — justify if off |
| Inbound from (namespace:port) | |
| Outbound to (namespace:port) | |

### 7.5 Secrets

| Secret name (Azure Key Vault) | Used by | Purpose | Rotation |
|-------------------------------|---------|---------|----------|
| | | | |

### 7.6 Release & rollback
<!-- Deploy trigger, smoke tests, rollback (ArgoCD revert + MFE version pin), migration rollback, feature flags. -->

## 8. Security  `[PM]` `[ENG]`

| Control | Approach | Status |
|---------|----------|--------|
| Authentication | OneAshley host + Keycloak JWT | |
| Authorization | Roles / permissions model: <describe> | |
| Data classification | <from PRD §7> | |
| Input validation | zod at HTTP and external-data boundaries | |
| Secrets | Azure Key Vault only; none in repo or config | |
| Dependency scanning | <tool> in CI | |
| PII / sensitive data | <fields, masking, retention> | |
| Audit logging | <events logged> | |
| OWASP Top 10 | <relevant items and mitigations> | |

## 9. Performance & Observability  `[ENG]`

- **Targets:** page load < __ s · API p95 < __ ms · <throughput>
- **Query rule:** every user-facing query checked with EXPLAIN against production-scale data
- **Observability:** `@one-ashley/observability`; logs, metrics, alerts and who responds
- **Scaling:** <expected load, replicas, limits>

## 10. Testing  `[ENG]`

| Level | Tooling | Scope | Gate |
|-------|---------|-------|------|
| Unit | Vitest + fakes | services, ADT branches | CI required |
| Contract | oRPC contract types | server ↔ frontend | type-check |
| Integration | | DB, external reads | |
| E2E | | core flows from PRD §6.2 | |

### 10.1 Key test cases
<!-- One per PRD acceptance criterion at minimum. Reference REQ-IDs. -->

## 11. Risks & Open Questions  `[PM]` `[ENG]`

| # | Item | Type | Owner | Due | Resolution |
|---|------|------|-------|-----|------------|
| 1 | | | | | |

## 12. Sign-off

| Role | Name | Date |
|------|------|------|
| Engineering lead | | |
| Product owner (co-author) | | |
| Platform / DevOps (if deviations or new infra) | | |
| Security (if data classification ≥ confidential) | | |
