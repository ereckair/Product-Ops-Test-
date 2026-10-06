# product-docs

Docs-as-code for product management: PRD → TDD → Jira (and later, the Product Engine site).
Product docs only — application code stays in its own repos.

## Quick start (personal test repo)

```bash
pip install -r requirements.txt
python scripts/pm.py validate                         # check every product
python scripts/pm.py plan domains/sq/products/sample-request-tracker --allow-draft
```

The sample product is fictional. Use it to see the full flow, then delete it.

## Daily flow

| Step | Who | How |
|------|-----|-----|
| 1. New product | PM | `python scripts/pm.py new sq <slug> --title "Name"`, or ask the agent (prd-draft skill) |
| 2. Draft PRD from proposal | PM + agent | Paste the proposal into Augment; the agent follows `.augment/skills/prd-draft` |
| 3. Request approval | Product owner | Set `status: approved`, add leader to `approved_by`, mark PR ready |
| 4. Approve PRD | Product leader | Approve + merge the PR (required by CODEOWNERS) |
| 5. Draft TDD | PM + eng lead + agent | `.augment/skills/tdd-codraft`; eng lead may add the code repo as a workspace |
| 6. Size stories | Eng lead | Score §6.1 factors, run `pm.py points <dir> --write` |
| 7. Approve TDD | Product leader | Same as step 4 |
| 8. Sync to Jira | PM | PR shows the plan; run the **Jira sync** workflow to apply |

## Roles

| Role | Does | Approves |
|------|------|----------|
| Product owner (L1) | Writes PRD, co-drafts TDD with eng lead, syncs Jira | — |
| Product leader (L2) | Reviews, configures domain | PRDs and TDDs in their domain (PR merge) |
| Product VP (L3) | Views across domains | — |

## Commands

| Command | What it does |
|---------|--------------|
| `validate [dir...]` | Schema, required sections, ID uniqueness, traceability, sizing math, P6M/security completeness |
| `points <dir> [--write]` | Computes story points from the rubric in `standards/sizing-rubric.yaml` |
| `plan <dir>` | Dry run: what would be created / updated / is blocked in Jira |
| `apply <dir>` | Pushes to Jira, writes `jira.lock.yaml` (idempotent; only changed items are updated) |
| `plan <dir> --json` | Same plan as structured operations, for an agent to execute |
| `record <dir> ID=KEY ...` | Writes Jira keys created by an agent into `jira.lock.yaml` |
| `new <domain> <slug> --title` | Scaffolds a product folder with the next PRD id |

`--allow-draft` on plan/apply bypasses the approval gate — for sandbox testing only.

## Jira ownership rule

The sync only sets **summary, description, story points, and parent**. Status, assignee, sprint,
and comments belong to Jira and are never touched. Items removed from docs are reported as
`orphan` and must be closed manually — the sync never deletes.

## Jira mapping

| Docs | Jira |
|------|------|
| PRD | One epic |
| `REQ-NNN` | Story under the epic (with story points) |
| `AREA-NN` capability area | Label on each story, e.g. `area-request-management` |
| `TASK-NNN` (TDD) | Subtask under its story |

## Extra Jira fields

Spaces often have custom fields (Acceptance Criteria, capability pickers, finance IDs). Map them in
`domain.yaml`; the agent can discover field IDs for you (jira-sync skill, setup step 3).

```yaml
jira:
  repo_url: https://github.com/<you>/<repo>/blob/main   # epics link back to the PRD
  fields:
    epic:
      - {name: Acceptance Criteria, id: customfield_XXXXX, source: prd.success_metrics, type: text}
      - {name: V2030 Capabilities,  id: customfield_XXXXX, source: frontmatter.jira_extra.v2030_capabilities, type: multiselect}
      - {name: Finance ID,          id: customfield_XXXXX, source: frontmatter.jira_extra.finance_id, type: text}
    story:
      - {name: Acceptance Criteria, id: customfield_XXXXX, source: req.acceptance_criteria, type: text}
```

Sources: `prd.tldr`, `prd.problem`, `prd.business_goals`, `prd.non_goals`, `prd.success_metrics`,
`req.acceptance_criteria`, `req.persona`, `req.priority`, `frontmatter.<path>`. Types: `text`, `select`,
`multiselect`, `number`. Blank values are skipped, so a field is only written when the docs have a value.
The epic description always carries summary, problem, business goals, and non-goals (anything not mapped to its own field).

## Two ways to write to Jira

| Mode | Auth | Best for |
|------|------|----------|
| **Agent-executed** (default) | The IDE's Jira access (Augment) | Individual PMs; no API token needed |
| **Script-executed** (`pm.py apply`) | API token / service account | CI and org-wide automation later |

Both use the same plan and the same `jira.lock.yaml`, so you can switch at any time.
Agent mode: ask Augment "sync sample-request-tracker to Jira" — it follows `.augment/skills/jira-sync`:
`plan --json` → you confirm → it creates/updates issues tier by tier → `pm.py record` writes the keys.

## Testing with a token instead (script mode)

1. Create a free Jira Cloud site and a Scrum project; put its key in `domains/sq/domain.yaml`.
2. Find your story points field: `GET <site>/rest/api/2/field` → look for "Story point estimate" or "Story Points".
3. Team-managed projects use `Subtask`; company-managed use `Sub-task`.
4. Create an API token at id.atlassian.com, then:
   ```bash
   export JIRA_BASE_URL=https://<you>.atlassian.net JIRA_EMAIL=<you> JIRA_TOKEN=<token>
   python scripts/pm.py apply domains/sq/products/sample-request-tracker --allow-draft
   ```
5. Edit a story title in `prd.md`, run apply again — only that story updates.

## Repo map

```
AGENTS.md                      agent rules (read by Augment, Cursor, Claude Code, Copilot)
.augment/rules/                always-on rule pointing at AGENTS.md
.augment/skills/               prd-draft, tdd-codraft, jira-sync
templates/                     canonical PRD and TDD
schemas/                       frontmatter JSON schemas
standards/sizing-rubric.yaml   story point rubric (moves to a standards repo later)
domains/<domain>/domain.yaml   Jira project + issue type mapping, tdd_mode
domains/<domain>/products/     one folder per product: prd.md, tdd.md, jira.lock.yaml
scripts/pm.py                  CLI
.github/workflows/             validate on PR (+ plan summary); manual Jira apply
```

## Moving to the company repo

Copy the repo as-is, update `CODEOWNERS` handles, set `domain.yaml` to the real Jira project,
add `JIRA_*` secrets and required reviewers on the `jira` environment. Do not include `.platform/`.
