---
type: always_apply
description: Core rules for product documentation in this repo
---
Follow every rule in `AGENTS.md` at the repo root. In particular: start from `templates/`, keep IDs stable,
never hand-enter story points, never edit `jira.lock.yaml`, never set `status: approved`, and run
`python scripts/pm.py validate` before proposing a commit.
