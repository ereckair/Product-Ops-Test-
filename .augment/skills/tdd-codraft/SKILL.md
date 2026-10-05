---
name: tdd-codraft
description: Draft a Technical Design Document from a PRD, co-written with the engineering lead. Use when asked to create or update a TDD, size stories, or break requirements into tasks.
---
# TDD co-drafting

## Preconditions
- The PRD exists in the same product folder. It should be `in-review` or `approved`.
- Read `domains/<domain>/domain.yaml` for `tdd_mode`. If `eng-owned`, only scaffold the file and stubs.
- If the engineering lead has added the code repo as a workspace, read it for context, but never write to it.

## Steps
1. Copy `templates/tdd.md` to `tdd.md` in the product folder. Set `id`, `prd`, owners, `code_repos`.
2. `[PM]` sections — draft fully from the PRD:
   - §1 Overview: scope by EPIC, link to PRD. Do not restate the PRD.
   - §2 Golden Path: default all rows to ✅. Mark ❌ only if the PRD makes a deviation unavoidable, with rationale.
   - §6 Work breakdown: one sizing row per REQ; tasks per REQ split by type (contract, backend, frontend, data, test).
   - §7 Deployment (P6M): workloads, frontend mode, networking, secrets — infer from the PRD and golden path; mark guesses with `<confirm>`.
   - §8 Security: fill defaults from the golden path; set data classification from PRD §7.
3. `[ENG]` sections (§3, §4, §5, §9, §10) — write guiding questions as stubs, not answers, unless the engineering lead asks you to draft.
4. Sizing: propose factor scores 0–3 with a one-line reason each in your summary (not in the file). The engineering lead confirms. Then run `python scripts/pm.py points <product-dir> --write`.
5. Run `python scripts/pm.py validate <product-dir>` and fix errors.
6. Summarize: what the engineering lead must write, every `<confirm>` item, and the sizing rationale.
