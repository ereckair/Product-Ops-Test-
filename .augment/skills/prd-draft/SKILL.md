---
name: prd-draft
description: Turn a raw business proposal (email text, Teams notes, Jira Product Discovery idea, slides) into a PRD that follows the repo template. Use when a PM asks to create, draft, or update a PRD.
---
# PRD drafting

## Inputs to ask for (only if missing)
- Domain and product name (determines the folder)
- The raw proposal material — pasted text or file paths
- Jira Product Discovery idea key, if one exists

## Steps
1. Create `domains/<domain>/products/<product-slug>/prd.md` by copying `templates/prd.md`.
2. Fill frontmatter: `id` = `PRD-<DOMAIN>-<NNN>` (next free number in the domain), domain, value_stream, owners, origin links. Leave `jira.initiative` empty. `status: draft`.
3. Map business goals to The Ten KPIs (listed in the template). If a goal maps to none, flag it in §10 as an open question — do not force a mapping.
4. Group requirements into capability areas (`AREA-NN`), 2–6 per PRD. The whole PRD becomes one Jira epic;
   areas become labels on the stories.
5. Write each requirement as `REQ-NNN` with Priority, Persona, Story, and Given/When/Then acceptance criteria. Each REQ becomes one Jira story, so keep it deliverable within one sprint where possible.
6. Anything the proposal leaves unclear goes into §10 Risks & Open Questions with an owner — never invent business facts, numbers, or targets. Use `<TBD>` for unknown values.
7. Do not write technical design. Note technical constraints in §7 only at business level.
8. Run `python scripts/pm.py validate domains/<domain>/products/<product-slug>` and fix errors.
9. Summarize for the PM: open questions that need business input before the next review round.

## Revising after a business review round
- Update content in place, keep all existing IDs, add a row to §11 Decision Log, bump `version`.
