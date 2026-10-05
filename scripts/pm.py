#!/usr/bin/env python3
"""Product docs CLI.

  python scripts/pm.py new <domain> <product-slug> --title "Name"
  python scripts/pm.py validate [product-dir ...]        # default: every product
  python scripts/pm.py points <product-dir> [--write]
  python scripts/pm.py plan <product-dir> [--allow-draft]
  python scripts/pm.py apply <product-dir> [--allow-draft] [--yes]
  python scripts/pm.py plan <product-dir> --json         # for an agent with its own Jira access
  python scripts/pm.py record <product-dir> EPIC-01=SQ-12 REQ-001=SQ-13 ...

Jira env vars for apply: JIRA_BASE_URL, JIRA_TOKEN, and either
JIRA_EMAIL (Cloud, basic auth) or JIRA_AUTH=bearer (Data Center PAT).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

try:
    import jsonschema
except ImportError:  # validation still runs, schema checks skipped
    jsonschema = None

ROOT = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"<[^<>\n]{1,80}>")
PRD_SECTIONS = ["TL;DR", "Problem & Context", "Goals", "Users & Personas", "Requirements",
                "User Experience", "Business Constraints & Dependencies", "Success Metrics",
                "Release Plan", "Risks & Open Questions", "Decision Log", "Sign-off"]
TDD_SECTIONS = ["Overview", "Golden Path Conformance", "Architecture", "Data Model", "API Contract",
                "Work Breakdown & Story Sizing", "Deployment (P6M)", "Security",
                "Performance & Observability", "Testing", "Risks & Open Questions", "Sign-off"]
FACTOR_COLS = ["Complexity", "Uncertainty", "Integrations", "Data / migration", "Security impact"]


# ── parsing ──────────────────────────────────────────────────────────────────
def load_doc(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError(f"{path}: missing YAML frontmatter")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def strip_comments(body: str) -> str:
    return re.sub(r"<!--.*?-->", "", body, flags=re.S)


def is_blank(value) -> bool:
    if value is None:
        return True
    s = str(value).strip()
    return s == "" or bool(PLACEHOLDER.fullmatch(s)) or s.upper() in {"TBD", "<TBD>"}


def h2_titles(body: str) -> list[str]:
    return [re.sub(r"`[^`]*`", "", t).strip()
            for t in re.findall(r"^## (?:\d+\.\s*)?(.+)$", body, re.M)]


def find_table(body: str, heading_prefix: str) -> tuple[list[str], list[dict], int, int]:
    """Return (headers, rows, start_line, end_line) of the first table after a heading."""
    lines = body.split("\n")
    start = next((i for i, l in enumerate(lines) if l.lstrip("#").strip().startswith(heading_prefix)
                  and l.startswith("#")), None)
    if start is None:
        return [], [], -1, -1
    i = start + 1
    while i < len(lines) and not lines[i].startswith("|"):
        if lines[i].startswith("#"):
            return [], [], -1, -1
        i += 1
    if i >= len(lines):
        return [], [], -1, -1
    t0 = i
    while i < len(lines) and lines[i].startswith("|"):
        i += 1
    tbl = lines[t0:i]
    split = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
    headers = split(tbl[0])
    rows = [dict(zip(headers, split(l))) for l in tbl[2:]]
    return headers, rows, t0, i


@dataclass
class Req:
    id: str
    name: str
    epic: str
    priority: str = ""
    persona: str = ""
    story: str = ""
    ac: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class Epic:
    id: str
    name: str
    reqs: list[Req] = field(default_factory=list)


def parse_requirements(body: str) -> list[Epic]:
    body = strip_comments(body)
    epics: list[Epic] = []
    cur_req: Req | None = None
    in_ac = False
    for line in body.split("\n"):
        if m := re.match(r"^### (EPIC-\d+):\s*(.+)$", line):
            epics.append(Epic(m.group(1), m.group(2).strip()))
            cur_req, in_ac = None, False
        elif m := re.match(r"^#### (REQ-\d+)\s*[·:\-]\s*(.+)$", line):
            if not epics:
                epics.append(Epic("EPIC-00", "Unassigned"))
            cur_req = Req(m.group(1), m.group(2).strip(), epics[-1].id)
            epics[-1].reqs.append(cur_req)
            in_ac = False
        elif line.startswith("## ") or line.startswith("### "):
            cur_req, in_ac = None, False
        elif cur_req:
            if m := re.match(r"^- \*\*(Priority|Persona|Story|Notes / business rules):\*\*\s*(.*)$", line):
                key = {"Priority": "priority", "Persona": "persona", "Story": "story",
                       "Notes / business rules": "notes"}[m.group(1)]
                setattr(cur_req, key, m.group(2).strip())
                in_ac = False
            elif re.match(r"^- \*\*Acceptance criteria:\*\*", line):
                in_ac = True
            elif in_ac and (m := re.match(r"^\s+- (.+)$", line)):
                cur_req.ac.append(m.group(1).strip())
    return epics


# ── product context ─────────────────────────────────────────────────────────
@dataclass
class Product:
    dir: Path
    domain_cfg: dict
    prd_fm: dict
    prd_body: str
    tdd_fm: dict | None
    tdd_body: str | None
    epics: list[Epic]

    @property
    def reqs(self) -> list[Req]:
        return [r for e in self.epics for r in e.reqs]


def load_product(pdir: Path) -> Product:
    pdir = pdir.resolve()
    domain_cfg = yaml.safe_load((pdir.parent.parent / "domain.yaml").read_text()) or {}
    prd_fm, prd_body = load_doc(pdir / "prd.md")
    tdd_fm = tdd_body = None
    if (pdir / "tdd.md").exists():
        tdd_fm, tdd_body = load_doc(pdir / "tdd.md")
    return Product(pdir, domain_cfg, prd_fm, prd_body, tdd_fm, tdd_body, parse_requirements(prd_body))


def rubric() -> dict:
    return yaml.safe_load((ROOT / "standards" / "sizing-rubric.yaml").read_text())


def compute_points(total: int, rb: dict) -> int | None:
    if total > rb["split_above"]:
        return None
    for t in rb["thresholds"]:
        if total <= t["max"]:
            return t["points"]
    return None


def sizing_rows(p: Product) -> tuple[list[str], list[dict], int, int]:
    return find_table(strip_comments(p.tdd_body or ""), "6.1")


def score_row(row: dict, rb: dict) -> tuple[int | None, int | None, str | None]:
    """Return (total, points, error)."""
    scores = []
    for col in FACTOR_COLS:
        v = row.get(col, "").strip()
        if v == "":
            return None, None, None  # not yet scored
        if not v.isdigit() or not 0 <= int(v) <= rb["max_per_factor"]:
            return None, None, f"{col} must be 0-{rb['max_per_factor']}, got '{v}'"
        scores.append(int(v))
    total = sum(scores)
    pts = compute_points(total, rb)
    if pts is None:
        return total, None, f"total {total} exceeds {rb['split_above']} — split this story"
    return total, pts, None


# ── validate ────────────────────────────────────────────────────────────────
def schema_errors(fm: dict, name: str) -> list[str]:
    if jsonschema is None:
        return []
    schema = json.loads((ROOT / "schemas" / name).read_text())
    v = jsonschema.Draft202012Validator(schema)
    return [f"frontmatter {'.'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in v.iter_errors(fm)]


def validate_product(pdir: Path) -> tuple[list[str], list[str]]:
    errs, warns = [], []
    try:
        p = load_product(pdir)
    except Exception as e:  # noqa: BLE001
        return [str(e)], []
    fm, status = p.prd_fm, p.prd_fm.get("status")
    strict = status in ("in-review", "approved")
    sink = errs if strict else warns

    errs += [f"PRD {e}" for e in schema_errors(fm, "prd.schema.json")]
    dom = str(p.domain_cfg.get("domain", "")).upper()
    if fm.get("id") and dom and not str(fm["id"]).startswith(f"PRD-{dom}-"):
        errs.append(f"PRD id {fm['id']} does not match domain '{dom}'")
    titles = h2_titles(p.prd_body)
    for s in PRD_SECTIONS:
        if s not in titles:
            errs.append(f"PRD missing section: {s}")
    if not p.epics:
        errs.append("PRD has no EPIC-NN headings under §5")
    seen = set()
    for e in p.epics:
        if not e.reqs:
            sink.append(f"PRD {e.id} has no requirements")
        for r in e.reqs:
            if r.id in seen:
                errs.append(f"PRD duplicate requirement id {r.id}")
            seen.add(r.id)
            if r.priority not in ("Must", "Should", "Could"):
                sink.append(f"PRD {r.id}: priority must be Must | Should | Could")
            if is_blank(r.story) or PLACEHOLDER.search(r.story):
                sink.append(f"PRD {r.id}: story is empty or has placeholders")
            real_ac = [a for a in r.ac if not PLACEHOLDER.search(a) and a.strip()]
            if not real_ac:
                sink.append(f"PRD {r.id}: needs at least one acceptance criterion")
    if status == "approved" and not fm.get("approved_by"):
        errs.append("PRD approved but approved_by is empty")

    if p.tdd_fm is not None:
        t, tstatus = p.tdd_fm, p.tdd_fm.get("status")
        tstrict = tstatus in ("in-review", "approved")
        tsink = errs if tstrict else warns
        errs += [f"TDD {e}" for e in schema_errors(t, "tdd.schema.json")]
        if t.get("prd") != fm.get("id"):
            errs.append(f"TDD prd '{t.get('prd')}' does not match PRD id '{fm.get('id')}'")
        if tstatus == "approved" and status != "approved":
            errs.append("TDD cannot be approved before the PRD is approved")
        ttitles = h2_titles(p.tdd_body or "")
        for s in TDD_SECTIONS:
            if s not in ttitles:
                errs.append(f"TDD missing section: {s}")

        _, gp, _, _ = find_table(strip_comments(p.tdd_body), "2. Golden Path")
        for row in gp:
            if "❌" in row.get("Conform", "") and is_blank(row.get("Deviation rationale")):
                errs.append(f"TDD golden path deviation '{row.get('Area')}' needs a rationale")

        rb = rubric()
        _, srows, _, _ = sizing_rows(p)
        req_ids = {r.id for r in p.reqs}
        sized = set()
        for row in srows:
            rid = row.get("REQ", "").strip()
            if not rid or is_blank(rid):
                continue
            if rid not in req_ids:
                errs.append(f"TDD sizing row {rid} not found in PRD")
                continue
            sized.add(rid)
            total, pts, err = score_row(row, rb)
            if err:
                errs.append(f"TDD sizing {rid}: {err}")
            elif total is None:
                tsink.append(f"TDD sizing {rid}: factors not scored yet")
            else:
                if row.get("Total", "").strip() not in ("", str(total)) or \
                   row.get("Points", "").strip() not in ("", str(pts)):
                    errs.append(f"TDD sizing {rid}: Total/Points do not match rubric "
                                f"(expected {total}/{pts}) — run `pm.py points --write`")
                elif row.get("Points", "").strip() == "":
                    tsink.append(f"TDD sizing {rid}: points not written — run `pm.py points --write`")
        for rid in sorted(req_ids - sized):
            tsink.append(f"TDD sizing: {rid} has no sizing row")

        _, trows, _, _ = find_table(strip_comments(p.tdd_body), "6.2")
        tids = set()
        for row in trows:
            tid = row.get("Task", "").strip()
            if not re.fullmatch(r"TASK-\d+", tid):
                continue
            if tid in tids:
                errs.append(f"TDD duplicate task id {tid}")
            tids.add(tid)
            if row.get("Parent REQ", "").strip() not in req_ids:
                errs.append(f"TDD {tid}: parent REQ '{row.get('Parent REQ')}' not in PRD")
            if is_blank(row.get("Description")):
                tsink.append(f"TDD {tid}: description is empty")

        if tstatus == "approved":
            _, wl, _, _ = find_table(strip_comments(p.tdd_body), "7.1")
            if not any(not PLACEHOLDER.search(r.get("Workload", "<x>")) for r in wl):
                errs.append("TDD approved but §7.1 has no real P6M workloads")
            _, net, _, _ = find_table(strip_comments(p.tdd_body), "7.4")
            oidc = next((r.get("Value", "") for r in net if r.get("Item", "").startswith("OIDC")), "")
            if is_blank(oidc) or "/" in oidc:
                errs.append("TDD approved but §7.4 OIDC setting is not decided")
    return errs, warns


def all_products() -> list[Path]:
    return sorted(p.parent for p in (ROOT / "domains").glob("*/products/*/prd.md"))


def cmd_validate(args) -> int:
    dirs = [Path(d) for d in args.dirs] or all_products()
    failed = 0
    for d in dirs:
        errs, warns = validate_product(d)
        rel = d.resolve().relative_to(ROOT) if d.resolve().is_relative_to(ROOT) else d
        mark = "FAIL" if errs else "ok"
        print(f"[{mark}] {rel}")
        for e in errs:
            print(f"   ✗ {e}")
        for w in warns:
            print(f"   ! {w}")
        failed += bool(errs)
    print(f"\n{len(dirs) - failed}/{len(dirs)} products valid")
    return 1 if failed else 0


# ── points ──────────────────────────────────────────────────────────────────
def cmd_points(args) -> int:
    pdir = Path(args.dir)
    p = load_product(pdir)
    if p.tdd_body is None:
        print("No tdd.md in this product")
        return 1
    rb = rubric()
    tdd_path = pdir / "tdd.md"
    text = tdd_path.read_text(encoding="utf-8")
    lines = text.split("\n")
    # locate the sizing table in the raw file (not comment-stripped) to rewrite in place
    hdr_i = next(i for i, l in enumerate(lines) if l.startswith("### 6.1"))
    i = hdr_i + 1
    while not lines[i].startswith("|"):
        i += 1
    headers = [c.strip() for c in lines[i].strip().strip("|").split("|")]
    rc = 1
    j = i + 2
    while j < len(lines) and lines[j].startswith("|"):
        cells = [c.strip() for c in lines[j].strip().strip("|").split("|")]
        row = dict(zip(headers, cells))
        total, pts, err = score_row(row, rb)
        rid = row.get("REQ", "")
        if err:
            print(f"✗ {rid}: {err}")
        elif total is None:
            print(f"- {rid}: not scored")
        else:
            print(f"✓ {rid}: total {total} → {pts} pts")
            row["Total"], row["Points"] = str(total), str(pts)
            lines[j] = "| " + " | ".join(row.get(h, "") for h in headers) + " |"
            rc = 0
        j += 1
    if args.write:
        tdd_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"Wrote points to {tdd_path}")
    return rc


# ── Jira plan / apply ───────────────────────────────────────────────────────
@dataclass
class Item:
    local_id: str
    kind: str              # initiative | epic | story | task
    summary: str
    description: str
    parent: str | None
    points: int | None = None
    gated_by: str | None = None   # reason it cannot be synced yet

    def digest(self) -> str:
        raw = json.dumps([self.summary, self.description, self.parent, self.points], ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()[:12]


def build_items(p: Product, allow_draft: bool) -> list[Item]:
    fm = p.prd_fm
    prd_ok = fm.get("status") == "approved" or allow_draft
    tdd_ok = (p.tdd_fm or {}).get("status") == "approved" or allow_draft
    prd_gate = None if prd_ok else "PRD not approved"
    tdd_gate = None if tdd_ok else ("TDD not approved" if p.tdd_fm else "no TDD")
    items: list[Item] = []
    jcfg = p.domain_cfg.get("jira", {})
    init_parent = None
    if jcfg.get("issue_types", {}).get("initiative"):
        items.append(Item("INITIATIVE", "initiative", fm.get("title", ""),
                          f"Source: {fm.get('id')}\nKPIs: {', '.join(fm.get('kpis') or [])}", None, gated_by=prd_gate))
        init_parent = "INITIATIVE"

    pts = {}
    if p.tdd_body:
        rb = rubric()
        for row in sizing_rows(p)[1]:
            total, pt, err = score_row(row, rb)
            if pt is not None:
                pts[row.get("REQ", "").strip()] = pt

    for e in p.epics:
        items.append(Item(e.id, "epic", e.name, f"Source: {fm.get('id')} / {e.id}", init_parent, gated_by=prd_gate))
        for r in e.reqs:
            desc = [r.story, "", "h3. Acceptance criteria"] + [f"* {a}" for a in r.ac]
            if r.notes and not is_blank(r.notes):
                desc += ["", "h3. Notes", r.notes]
            desc += ["", f"Priority: {r.priority} · Persona: {r.persona}", f"Source: {fm.get('id')} / {r.id}"]
            items.append(Item(r.id, "story", f"{r.name}", "\n".join(desc), e.id,
                              points=pts.get(r.id) if tdd_ok else None, gated_by=prd_gate))

    if p.tdd_body:
        for row in find_table(strip_comments(p.tdd_body), "6.2")[1]:
            tid = row.get("Task", "").strip()
            if not re.fullmatch(r"TASK-\d+", tid) or is_blank(row.get("Description")):
                continue
            desc = f"{row.get('Description')}\n\nDefinition of done: {row.get('Definition of done', '')}\n" \
                   f"Type: {row.get('Type', '')}\nSource: {p.tdd_fm.get('id')} / {tid}"
            items.append(Item(tid, "task", f"[{row.get('Type', '').strip()}] {row.get('Description')}"[:250],
                              desc, row.get("Parent REQ", "").strip(), gated_by=tdd_gate or prd_gate))
    return items


def load_lock(pdir: Path) -> dict:
    f = pdir / "jira.lock.yaml"
    return (yaml.safe_load(f.read_text()) or {}) if f.exists() else {}


def save_lock(pdir: Path, lock: dict) -> None:
    header = "# Generated by scripts/pm.py apply. Do not edit by hand.\n"
    (pdir / "jira.lock.yaml").write_text(header + yaml.safe_dump(lock, sort_keys=True, allow_unicode=True))


def make_plan(p: Product, allow_draft: bool) -> list[tuple[str, Item | None, str]]:
    lock = load_lock(p.dir).get("items", {})
    items = build_items(p, allow_draft)
    plan = []
    for it in items:
        if it.gated_by:
            plan.append(("blocked", it, it.gated_by))
        elif it.local_id not in lock:
            plan.append(("create", it, ""))
        elif lock[it.local_id]["hash"] != it.digest():
            plan.append(("update", it, lock[it.local_id]["key"]))
        else:
            plan.append(("noop", it, lock[it.local_id]["key"]))
    local = {i.local_id for i in items}
    for lid, v in lock.items():
        if lid not in local:
            plan.append(("orphan", None, f"{lid} → {v['key']} (removed from docs; close in Jira manually)"))
    return plan


def print_plan(plan) -> dict:
    counts: dict[str, int] = {}
    for action, it, note in plan:
        counts[action] = counts.get(action, 0) + 1
        if action == "noop":
            continue
        label = f"{it.kind:<10} {it.local_id:<10} {it.summary[:60]}" if it else ""
        pts = f" [{it.points} pts]" if it and it.points is not None else ""
        print(f"  {action:<8} {label}{pts}  {note}")
    print("\nSummary: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return counts


def cmd_plan(args) -> int:
    p = load_product(Path(args.dir))
    errs, _ = validate_product(Path(args.dir))
    if errs and args.json:
        print(json.dumps({"errors": errs}, indent=2, ensure_ascii=False))
        return 1
    if errs:
        print("Validation errors — fix before syncing:")
        for e in errs:
            print(f"  ✗ {e}")
        return 1
    plan = make_plan(p, args.allow_draft)
    if args.json:
        print(json.dumps(plan_json(p, plan), indent=2, ensure_ascii=False))
        return 0
    print(f"Jira plan for {p.prd_fm.get('id')} → project {p.domain_cfg.get('jira', {}).get('project_key')}\n")
    print_plan(plan)
    return 0


def plan_json(p: Product, plan) -> dict:
    """Machine-readable plan for an agent with its own Jira access (e.g. Augment)."""
    cfg = p.domain_cfg.get("jira", {})
    keys = {k: v["key"] for k, v in load_lock(p.dir).get("items", {}).items()}
    order = {"initiative": 0, "epic": 1, "story": 2, "task": 3}
    ops = []
    for action, it, note in plan:
        if action in ("noop",):
            continue
        if it is None:
            ops.append({"action": action, "note": note})
            continue
        op = {"action": action, "local_id": it.local_id, "tier": order[it.kind], "kind": it.kind,
              "issue_type": cfg.get("issue_types", {}).get(it.kind), "summary": it.summary,
              "description": it.description}
        if action == "blocked":
            op["reason"] = note
        if action == "update":
            op["key"] = note
        if it.parent:
            op["parent_local_id"] = it.parent
            op["parent_key"] = keys.get(it.parent)  # null until the parent is created and recorded
        if it.points is not None:
            op["story_points"] = {"field": cfg.get("story_points_field"), "value": it.points}
        ops.append(op)
    ops.sort(key=lambda o: o.get("tier", 9))
    return {"product": str(p.dir.relative_to(ROOT)), "prd": p.prd_fm.get("id"),
            "project_key": cfg.get("project_key"), "epic_link_mode": cfg.get("epic_link_mode", "parent"),
            "epic_link_field": cfg.get("epic_link_field"),
            "owned_fields": ["summary", "description", "story points", "parent"],
            "never_touch": ["status", "assignee", "sprint", "comments", "delete"],
            "operations": ops}


class Jira:
    def __init__(self):
        import requests
        self.base = os.environ["JIRA_BASE_URL"].rstrip("/")
        self.s = requests.Session()
        token = os.environ["JIRA_TOKEN"]
        if os.environ.get("JIRA_AUTH", "basic") == "bearer":
            self.s.headers["Authorization"] = f"Bearer {token}"
        else:
            self.s.auth = (os.environ["JIRA_EMAIL"], token)
        self.s.headers["Content-Type"] = "application/json"

    def create(self, fields: dict) -> str:
        r = self.s.post(f"{self.base}/rest/api/2/issue", json={"fields": fields}, timeout=30)
        if not r.ok:
            raise RuntimeError(f"create failed {r.status_code}: {r.text[:500]}")
        return r.json()["key"]

    def update(self, key: str, fields: dict) -> None:
        r = self.s.put(f"{self.base}/rest/api/2/issue/{key}", json={"fields": fields}, timeout=30)
        if not r.ok:
            raise RuntimeError(f"update {key} failed {r.status_code}: {r.text[:500]}")


def fields_for(it: Item, cfg: dict, keys: dict, creating: bool) -> dict:
    """Only fields the docs own: summary, description, points, parent. Never status/assignee/sprint."""
    f = {"summary": it.summary, "description": it.description}
    if it.points is not None and cfg.get("story_points_field"):
        f[cfg["story_points_field"]] = it.points
    if creating:
        f["project"] = {"key": cfg["project_key"]}
        f["issuetype"] = {"name": cfg["issue_types"][it.kind]}
        parent_key = keys.get(it.parent) if it.parent else None
        if parent_key:
            if it.kind == "story" and cfg.get("epic_link_mode") == "epic_link":
                f[cfg["epic_link_field"]] = parent_key
            else:
                f["parent"] = {"key": parent_key}
    return f


def write_initiative_key(p: Product, key: str) -> None:
    path = p.dir / "prd.md"
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"(?m)^(  initiative:)[^\n#]*", rf"\g<1> {key}  ", text, count=1)
    path.write_text(text, encoding="utf-8")


def cmd_apply(args) -> int:
    pdir = Path(args.dir)
    p = load_product(pdir)
    errs, _ = validate_product(pdir)
    if errs:
        print("Validation errors — fix before syncing.")
        return 1
    plan = make_plan(p, args.allow_draft)
    counts = print_plan(plan)
    todo = [(a, it, n) for a, it, n in plan if a in ("create", "update")]
    if not todo:
        print("Nothing to apply.")
        return 0
    if not args.yes and input(f"\nApply {len(todo)} change(s) to Jira? [y/N] ").strip().lower() != "y":
        print("Aborted.")
        return 1
    cfg = p.domain_cfg["jira"]
    jira = Jira()
    lock = load_lock(pdir)
    lock.setdefault("items", {})
    keys = {k: v["key"] for k, v in lock["items"].items()}
    order = {"initiative": 0, "epic": 1, "story": 2, "task": 3}
    for action, it, note in sorted(todo, key=lambda x: order[x[1].kind]):
        if action == "create":
            key = jira.create(fields_for(it, cfg, keys, creating=True))
            keys[it.local_id] = key
            print(f"  created {key} ← {it.local_id}")
            if it.kind == "initiative":
                write_initiative_key(p, key)
        else:
            key = note
            jira.update(key, fields_for(it, cfg, keys, creating=False))
            print(f"  updated {key} ← {it.local_id}")
        lock["items"][it.local_id] = {"key": key, "hash": it.digest()}
        save_lock(pdir, lock)  # save after every call so a failure is resumable
    print("Done. Commit jira.lock.yaml.")
    return 0


def cmd_record(args) -> int:
    """Record Jira keys created/updated by an external agent: LOCAL_ID=KEY ..."""
    pdir = Path(args.dir)
    p = load_product(pdir)
    items = {i.local_id: i for i in build_items(p, allow_draft=True)}
    lock = load_lock(pdir)
    lock.setdefault("items", {})
    for pair in args.pairs:
        if "=" not in pair:
            print(f"✗ expected LOCAL_ID=KEY, got '{pair}'")
            return 1
        lid, key = pair.split("=", 1)
        if lid not in items:
            print(f"✗ {lid} is not in the current docs")
            return 1
        lock["items"][lid] = {"key": key.strip(), "hash": items[lid].digest()}
        if lid == "INITIATIVE":
            write_initiative_key(p, key.strip())
        print(f"✓ {lid} → {key.strip()}")
    save_lock(pdir, lock)
    return 0


# ── new product ─────────────────────────────────────────────────────────────
def cmd_new(args) -> int:
    ddir = ROOT / "domains" / args.domain
    if not (ddir / "domain.yaml").exists():
        print(f"No domain config at {ddir/'domain.yaml'}")
        return 1
    pdir = ddir / "products" / args.slug
    if pdir.exists():
        print(f"{pdir} already exists")
        return 1
    dom = args.domain.upper()
    nums = []
    for prd in ddir.glob("products/*/prd.md"):
        m = re.search(rf"^id:\s*PRD-{dom}-(\d+)", prd.read_text(), re.M)
        if m:
            nums.append(int(m.group(1)))
    n = f"{(max(nums) + 1) if nums else 1:03d}"
    cfg = yaml.safe_load((ddir / "domain.yaml").read_text())
    pdir.mkdir(parents=True)
    prd = (ROOT / "templates" / "prd.md").read_text()
    prd = prd.replace("PRD-<DOMAIN>-<NNN>            # e.g. PRD-SQ-014. Stable, never reused.", f"PRD-{dom}-{n}")
    prd = prd.replace("title: <Product / capability name>", f"title: {args.title}")
    prd = re.sub(r"(?m)^domain: .*$", f"domain: {args.domain}", prd, count=1)
    prd = re.sub(r"(?m)^value_stream: .*$", f"value_stream: {cfg.get('value_stream', '<design | plan | make | enable>')}", prd, count=1)
    prd = prd.replace("# <Title>", f"# {args.title}", 1)
    (pdir / "prd.md").write_text(prd)
    print(f"Created {pdir/'prd.md'} as PRD-{dom}-{n}. Create the TDD later with the tdd-codraft skill.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("validate"); s.add_argument("dirs", nargs="*"); s.set_defaults(fn=cmd_validate)
    s = sub.add_parser("points"); s.add_argument("dir"); s.add_argument("--write", action="store_true"); s.set_defaults(fn=cmd_points)
    s = sub.add_parser("plan"); s.add_argument("dir"); s.add_argument("--allow-draft", action="store_true")
    s.add_argument("--json", action="store_true"); s.set_defaults(fn=cmd_plan)
    s = sub.add_parser("record"); s.add_argument("dir"); s.add_argument("pairs", nargs="+"); s.set_defaults(fn=cmd_record)
    s = sub.add_parser("apply"); s.add_argument("dir"); s.add_argument("--allow-draft", action="store_true")
    s.add_argument("--yes", action="store_true"); s.set_defaults(fn=cmd_apply)
    s = sub.add_parser("new"); s.add_argument("domain"); s.add_argument("slug"); s.add_argument("--title", required=True)
    s.set_defaults(fn=cmd_new)
    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
