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
3. Use a sandbox/test project until the user says otherwise.

## Each sync
1. Run `python scripts/pm.py validate <product-dir>`. Stop on errors.
2. Run `python scripts/pm.py plan <product-dir> --json`. If it returns `errors`, stop and report them.
3. Show the user a short summary: counts of create / update / blocked / orphan, and list them.
   Wait for explicit confirmation before writing anything to Jira.
4. Execute operations **tier by tier** (tier 0 initiative → 1 epics → 2 stories → 3 tasks):
   - `create`: create the issue in `project_key` with `issue_type`, `summary`, `description`.
     Set the parent to `parent_key` (for stories, use the epic link field instead if `epic_link_mode` is `epic_link`).
     Set `story_points.field` to `story_points.value` when present.
   - `update`: edit issue `key` — only summary, description, story points.
   - `blocked`: skip; report the reason.
   - `orphan`: never delete or close; report it to the user.
5. After finishing each tier, run
   `python scripts/pm.py record <product-dir> <LOCAL_ID>=<KEY> ...` for every issue you created or updated,
   then re-run `plan --json` so the next tier has its `parent_key` values.
6. When done, report created/updated keys and remind the user to commit `jira.lock.yaml`.

## Never
- Change status, assignee, sprint, labels, or comments.
- Delete or close issues.
- Edit `jira.lock.yaml` by hand — only through `pm.py record`.
- Sync with `--allow-draft` unless the user explicitly says this is a sandbox test.
