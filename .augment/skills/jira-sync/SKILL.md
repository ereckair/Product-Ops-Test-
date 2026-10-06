---
name: jira-sync
description: Sync an approved PRD/TDD to Jira using the IDE's own Jira access. Use when asked to push, sync, or create Jira epics/stories/tasks from product docs, or to set up a domain's Jira mapping.
---
# Jira sync (agent-executed)

The script decides WHAT to write. You only execute it with your Jira access. Never invent, merge,
split, or reword issues yourself.

## One-time setup per domain
1. With your Jira access, look up for the target project: project key, exact issue type names
   (Epic, Story, Subtask vs Sub-task, Initiative if present), and the story points field id.
2. Update `domains/<domain>/domain.yaml` with those values. Show the diff to the user.
3. Extra fields: read the create screens (create metadata) for Epic and Story in that project. For each
   custom field that matches a known source, add an entry under `jira.fields` (see README "Extra Jira fields").
   Typical: Acceptance Criteria on Story → `req.acceptance_criteria`; Acceptance Criteria on Epic →
   `prd.success_metrics`; select/multi-select fields (e.g. capabilities) → `frontmatter.jira_extra.<key>`
   with type `select`/`multiselect`, and list the allowed option values to the user.
   Never map status-like fields (e.g. "Reason for Block"), assignee, or sprint. Show the diff before saving.
   Also set `jira.repo_url` to the repo's GitHub blob URL for main so epics link back to the PRD.
4. Use a sandbox/test project until the user says otherwise.

## Each sync
1. Run `python scripts/pm.py validate <product-dir>`. Stop on errors.
2. Run `python scripts/pm.py plan <product-dir> --json`. If it returns `errors`, stop and report them.
3. Show the user a short summary: counts of create / update / blocked / orphan, and list them.
   Wait for explicit confirmation before writing anything to Jira.
4. After the user confirms the plan once, execute **all** tiers in one run without stopping (tier 0 initiative → 1 the PRD epic → 2 stories → 3 subtasks):
   - `create`: create the issue in `project_key` with `issue_type`, `summary`, `description`.
     Set the parent to `parent_key` (for stories, use the epic link field instead if `epic_link_mode` is `epic_link`).
     Set `story_points.field` to `story_points.value` when present. Set `labels` on create only.
     Set every entry in `fields` (`id` → `value`, already in Jira API format).
   - `update`: edit issue `key` — summary, description, story points, and `fields`. Never touch labels on update.
   - `blocked`: skip; report the reason.
   - `orphan`: never delete or close; report it to the user.
5. After finishing each tier, run
   `python scripts/pm.py record <product-dir> <LOCAL_ID>=<KEY> ...` for every issue you created or updated,
   then re-run `plan --json` so the next tier has its `parent_key` values.
6. Verify: read the epic back and confirm it has one child story per REQ, and each story has its subtasks.
   Report any story that is not linked to the epic (that means `epic_link_mode` is wrong for this project).
7. Report created/updated keys and remind the user to commit `jira.lock.yaml`.

## Never
- Change status, assignee, sprint, labels, or comments.
- Delete or close issues.
- Edit `jira.lock.yaml` by hand — only through `pm.py record`.
- Sync with `--allow-draft` unless the user explicitly says this is a sandbox test.
