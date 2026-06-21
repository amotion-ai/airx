#!/usr/bin/env python3
"""airx extract — background auto-DRAFT: the deterministic half of "AI fills the memory".

Produces a CANDIDATE stub (never asserted as truth) of CODE-DERIVED facts a human then confirms via
/airx:memory. This is verify-first by construction: every extracted fact is tagged `[verify]` (a
hypothesis to check against code), every INTENT section (why / what-changed / traps) is left
`TBD — needs human input` because code cannot source intent. The draft file is `_`-prefixed so the
existing tools (check.py / score.py / verify-citations.py all skip `_`-files) do NOT count it as a real
note. Stdlib only, no LLM.

    python3 tools/extract.py <wiki-dir> [module]

If [module] is omitted, picks the hottest UNDOCUMENTED module (no reference_<module>.md yet) from
init.rank_modules (git-churn ranking). Reuses tools/init.py (rank_modules, _module_base, _IGNORE_DIRS).
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def _load(name: str, path: Path):
    """Load a sibling tool as a module (same pattern as tools/score.py)."""
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


HERE = Path(__file__).resolve().parent
init = _load("airx_init", HERE / "init.py")

# Reuse score.py's tighter ticket pattern (>=2 leading letters) — the loose [A-Z]+-\d+ over-matches.
TICKET = re.compile(r"\b[A-Z]{2,}-\d+\b")
# Annotations that classify a class (kept intentionally short — the durable, high-signal ones).
CLASS_ANN = ("RestController", "Controller", "Service", "Component", "Repository", "Entity",
             "Configuration", "Configurer")
ANN_LINE = re.compile(r"@(" + "|".join(CLASS_ANN) + r")\b(\([^)]*\))?")
# public method signatures (Java/Kotlin): a public method, capture return + name + params (best-effort,
# deterministic — flagged [verify] so a human confirms each).
METHOD = re.compile(
    r"^\s*public\s+(?:static\s+|final\s+|synchronized\s+|abstract\s+)*"
    r"([A-Za-z_][\w<>\[\],.\s?]*?)\s+([a-zA-Z_]\w*)\s*\(([^;{]*)\)\s*(?:throws[\w,\s.]*)?\s*[{]",
    re.M)
TABLE = re.compile(r'@Table\s*\(\s*name\s*=\s*"([^"]+)"')
NQ_NAME = re.compile(r'name="([^"]+)"')

_IGNORE = init._IGNORE_DIRS | {"test"}            # skip src/test so test classes don't pollute the draft
METHOD_CAP = 40                                    # keep the draft scannable; flagged when hit


def java_files(module_dir: Path) -> list[Path]:
    out = []
    for p in sorted(module_dir.rglob("*.java")):
        if any(part in _IGNORE for part in p.relative_to(module_dir).parts):
            continue
        out.append(p)
    return out


def extract_classes(module_dir: Path) -> list[tuple[str, list[str]]]:
    """(class_name, [annotation, ...]) for each .java whose declared class carries a classifying
    annotation. Best-effort, deterministic — every row ships as [verify]."""
    rows = []
    for p in java_files(module_dir):
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        anns = [m.group(0) for m in ANN_LINE.finditer(text)
                # only annotations sitting on the top-level class declaration (cheap heuristic: before
                # the first `class <Stem>` line)
                ]
        cls_re = re.search(r"\b(?:public\s+)?(?:final\s+|abstract\s+)*(?:class|interface|enum)\s+"
                           + re.escape(p.stem) + r"\b", text)
        if not cls_re:
            continue
        # annotations literally appearing above the class declaration line
        head = text[:cls_re.start()]
        anns = []
        for m in ANN_LINE.finditer(head):
            anns.append((m.group(1), m.group(0)))      # (name, full literal e.g. @Component("x"))
        # dedup: collapse a bare `@Component` when a parameterized `@Component("x")` of the same name
        # is also present; keep distinct literals otherwise (preserves order).
        params = {name for name, lit in anns if "(" in lit}
        seen, out = set(), []
        for name, lit in anns:
            if "(" not in lit and name in params:
                continue
            if lit not in seen:
                seen.add(lit)
                out.append(lit)
        if out:
            rows.append((p.stem, out))
    return rows


def extract_methods(module_dir: Path, limit: int = METHOD_CAP) -> list[tuple[str, str]]:
    """(class_name, signature) for public methods, deterministic best-effort, capped to keep the draft
    scannable. Each is a [verify] hypothesis."""
    out = []
    for p in java_files(module_dir):
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for m in METHOD.finditer(text):
            ret, name, params = m.group(1).strip(), m.group(2), " ".join(m.group(3).split())
            if name in ("if", "for", "while", "switch", "catch", "synchronized", "new"):
                continue
            sig = f"{ret} {name}({params})"
            out.append((p.stem, sig))
            if len(out) >= limit:
                return out
    return out


def extract_queries(module_dir: Path, limit: int = 60) -> list[tuple[str, str]]:
    """(query_name, queries-file-name) for named queries in XML under the MODULE (build_index is
    repo-wide; the requirement is module-scoped, so we scan the module dir directly)."""
    out, seen = [], set()
    for p in sorted(module_dir.rglob("*.xml")):
        nm = p.name.lower()
        if not (nm.endswith("queries.xml") or "quer" in nm):
            continue
        if any(part in _IGNORE for part in p.relative_to(module_dir).parts):
            continue
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for m in NQ_NAME.finditer(text):
            q = m.group(1)
            if q in seen:
                continue
            seen.add(q)
            out.append((q, p.name))
            if len(out) >= limit:
                return out
    return out


def extract_tables(module_dir: Path) -> list[str]:
    out = []
    for p in java_files(module_dir):
        try:
            text = p.read_text(errors="ignore")
        except Exception:
            continue
        for m in TABLE.finditer(text):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


def extract_tickets(repo: Path, rel_path: str, limit: int = 20) -> list[str]:
    """Distinct ticket IDs from the module's git log (most recent first)."""
    out, seen = [], set()
    try:
        log = subprocess.run(
            ["git", "-C", str(repo), "log", "--oneline", "-n", "400", "--", rel_path],
            capture_output=True, text=True, timeout=30).stdout
    except Exception:
        log = ""
    for line in log.splitlines():
        for t in TICKET.findall(line):
            if t not in seen:
                seen.add(t)
                out.append(t)
                if len(out) >= limit:
                    return out
    return out


def banner(module: str) -> str:
    return (
        "> ============================================================================\n"
        "> DRAFT — auto-extracted, UNVERIFIED. Confirm each [verify] line against code via\n"
        f"> /airx:memory, then rename to reference_{module}.md.\n"
        "> Code-derived facts are HYPOTHESES ([verify]); intent (why / what-changed / traps)\n"
        "> is left TBD because code cannot source intent. Nothing here is asserted as truth.\n"
        "> ============================================================================"
    )


def _v(items: list[str], empty: str) -> str:
    return "\n".join(items) if items else empty


def build_draft(module: str, code_ref: str, classes, methods, queries, tables, tickets) -> str:
    today = date.today().isoformat()

    cls_rows = "\n".join(
        f"| `{name}` | {' '.join('`' + a + '`' for a in anns)} | TBD `[verify]` |"
        for name, anns in classes) or "| TBD | | TBD `[verify]` |"

    method_lines = _v([f"- `{cls}.{sig}` `[verify]`" for cls, sig in methods],
                      "- TBD `[verify]` — no public method signatures auto-extracted")
    if len(methods) >= METHOD_CAP:
        method_lines += (f"\n- … (auto-extraction capped at {METHOD_CAP}; more public methods exist — "
                         f"see code) `[verify]`")

    query_lines = _v([f"- `{q}` (in `{f}`) `[verify]`" for q, f in queries],
                     "- TBD `[verify]` — no named queries found under this module")

    table_lines = _v([f"- table `{t}` (`@Table`) `[verify]`" for t in tables],
                     "- TBD `[verify]` — no `@Table`/`@Entity` table names auto-extracted")

    ticket_lines = _v(
        [f"- {today} — `{t}` `[verify]` (what changed / why: TBD — needs human input)" for t in tickets],
        "- TBD `[verify]` — no ticket-linked commits found on this module's git log")

    return f"""\
---
name: {module} — DRAFT (auto-extracted, UNVERIFIED)
description: >
  CANDIDATE stub of code-derived facts for the `{module}` module. Auto-extracted by airx extract.py.
  Every fact is a [verify] hypothesis; intent sections are TBD. NOT a finished note — confirm via
  /airx:memory, then rename to reference_{module}.md.
type: reference
created_date: {today}
origin_session_id: TBD
updated_date: {today} (extract: auto-drafted)
owner: TBD
last_verified: TBD
code_ref: {code_ref}
tier: T2
status: DRAFT
---

# {module} — DRAFT (auto-extracted, UNVERIFIED)

{banner(module)}

## What it is
TBD — needs human input (code cannot source intent).

## Package & class overview
> Auto-extracted class names + annotations — each is a `[verify]` hypothesis; confirm the purpose.

| Class | Annotations | Purpose |
|---|---|---|
{cls_rows}

## Types & statuses (CODE enum → labelled BUSINESS meaning)
TBD — needs human input (code cannot source the business meaning of status codes).

## Key methods (grouped; cite each)
> Auto-extracted public method signatures — best-effort, confirm each `[verify]`.
{method_lines}

## Models & screens (key fields · XHTML pages / REST paths)
TBD — needs human input (map fields/screens to business meaning).

## Named queries & tables (incl. geo-specific; verify in queries.xml)
> Auto-extracted named-query names + `@Table` hints under this module — each `[verify]`.

Named queries:
{query_lines}

Tables:
{table_lines}

## Business-logic flows & formulas
TBD — needs human input (code cannot source the intended flow/formula or why it exists).

## Geo-variants (e.g. PH/MY — prefix, differing fields, routing method)
TBD — needs human input (confirm forks + routing with the team).

## Inter-module deps & config flags
TBD — needs human input (intent of cross-module coupling / flags).

## Ticket history
> Auto-extracted ticket IDs from this module's git log — each `[verify]`; the WHY is the crown jewel.
{ticket_lines}

## Gotchas / traps
TBD — needs human input (tacit "do not revert / never touch X" knowledge lives with the team).
"""


def pick_module(repo: Path, wiki: Path, arg: str | None) -> tuple[str | None, str]:
    """Return (module, why). If arg given, use it (validated against detected modules but accepted even
    if unranked). Else the hottest UNDOCUMENTED module (no reference_<m>.md) from rank_modules."""
    ranked = init.rank_modules(repo)
    names = [n for n, _ in ranked]
    if arg:
        why = "explicit module argument"
        if names and arg not in names:
            why += f" (note: not in detected modules {names[:8]})"
        return arg, why
    mem = wiki / "ai_memory"
    for n, churn in ranked:
        if not (mem / f"reference_{n}.md").is_file():
            return n, f"hottest undocumented module ({churn} recent change{'s' if churn != 1 else ''})"
    if ranked:
        n, churn = ranked[0]
        return n, f"all detected modules already have a reference note; defaulting to hottest ({churn} changes)"
    return None, "no modules detected"


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: extract.py <wiki-dir> [module]", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2
    arg = sys.argv[2] if len(sys.argv) == 3 else None

    # resolve repo from the manifest (target.repo_path), same key check init/verify-citations use.
    repo = None
    man = wiki / ".ai-readiness.yml"
    if man.is_file():
        for line in man.read_text(errors="ignore").splitlines():
            s = line.strip()
            if s.startswith("repo_path:"):
                v = s.split(":", 1)[1].strip()
                if v and v != "TBD":
                    repo = Path(v) if Path(v).is_absolute() else (wiki / v).resolve()
    if repo is None or not repo.is_dir():
        print("error: no resolvable target.repo_path in .ai-readiness.yml — cannot extract", file=sys.stderr)
        return 2

    module, why = pick_module(repo, wiki, arg)
    if not module:
        print("error: could not pick a module (none detected from git churn)", file=sys.stderr)
        return 2

    # resolve the module's source dir via _module_base (correct for multi-module AND single-module repos)
    base, names = init._module_base(repo)
    module_dir = base / module
    if not module_dir.is_dir():
        print(f"error: module dir {module_dir} not found (module='{module}')", file=sys.stderr)
        return 2
    rel_path = module_dir.relative_to(repo).as_posix()

    classes = extract_classes(module_dir)
    methods = extract_methods(module_dir)
    queries = extract_queries(module_dir)
    tables = extract_tables(module_dir)
    tickets = extract_tickets(repo, rel_path)
    ref = init.code_ref(repo)

    draft = build_draft(module, ref, classes, methods, queries, tables, tickets)
    out = wiki / "ai_memory" / f"_draft_{module}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(draft)

    print(f"airx extract ✓  drafted {out}")
    print(f"  module: {module}  ({why})")
    print(f"  source: {module_dir}")
    print(f"  extracted (all [verify] hypotheses): "
          f"{len(classes)} class(es) · {len(methods)} method(s) · "
          f"{len(queries)} named quer{'y' if len(queries) == 1 else 'ies'} · "
          f"{len(tables)} table(s) · {len(tickets)} ticket(s)")
    print(f"  intent sections (why / what-changed / traps) left: TBD — needs human input")
    print(f"  UNVERIFIED draft — `_`-prefixed so check.py/score.py do NOT count it as a real note.")
    print()
    print(f"  next: /airx:memory {module}  → confirm each [verify] line against code, fill the TBD")
    print(f"        intent sections, then rename _draft_{module}.md → reference_{module}.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
