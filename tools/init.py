#!/usr/bin/env python3
"""airx init — stamp the memory layer of an AI-readiness skeleton in (or beside) a repo.

Progressive by design: creates ONLY the project-memory layer (ai_memory/ + the agent context files +
the manifest) and prints a menu of the OPTIONAL layers you can add later (docs / kb / viewer). Memory is
the universal entry layer; nothing heavier is stamped unless you ask for it. Stdlib only, no LLM.

Layouts:
  in-repo  (default) — ai_memory/ + CLAUDE.md/AGENTS.md at the REPO ROOT, so the agent auto-loads memory.
  sibling            — everything in ../<repo>-wiki/ (keeps the repo's git tree untouched).
  ignored            — in-repo, but airx paths are added to .gitignore (local-only, not committed).

    python3 init.py --repo <path> [--layout in-repo|sibling|ignored] [--out DIR] [--stack S] [--domain D]
"""
from __future__ import annotations

import argparse
import subprocess
from datetime import date
from pathlib import Path

AIRX_BEGIN = "<!-- airx:begin -->"
AIRX_END = "<!-- airx:end -->"

MEMORY_INDEX = """\
# Project Memory — index

> What the agent should load before working a module: the "why & what-changed" it would otherwise
> re-derive every session. Each note cites a real `file:line` or says `TBD`. Add a row per module.

## Spine (cross-cutting, verify against code)
- _TBD — architecture spine, multi-tenancy/scoping rule, the one load-bearing fact._

## Your modules (detected + ranked by recent git activity — this is the map; pick one for `/airx:memory`)
{candidates}

## Module notes
| Module | Note | Last verified |
|---|---|---|
| _example_ | `reference_example_module.md` | TBD |
"""

REFERENCE_TEMPLATE = """\
---
name: <Module> — Developer Reference
description: >
  DENSE index — class names, method names, query names, ticket IDs. Built for the agent to load,
  not to read top-to-bottom.
type: reference
created_date: {today}
origin_session_id: TBD
updated_date: {today} (init: created)
owner: TBD
last_verified: TBD
code_ref: {code_ref}
tier: T2
status: LIVING
---

# <Module> — Developer Reference

> Every concrete claim carries a real anchor — `file:line` **or** a durable symbol (class / method /
> `queries.xml` name / bean id / table) — or says `TBD — needs human input`. Never invent. Symbols are
> preferred (they survive churn; `/airx:check` verifies them). Fill each section via `/airx:memory`.

## What it is
TBD

## Package & class overview
| Class | Annotations | Purpose |
|---|---|---|
| TBD | | |

## Types & statuses (CODE enum → labelled BUSINESS meaning)
- TBD

## Key methods (grouped; cite each)
- TBD

## Models & screens (key fields · XHTML pages / REST paths)
- TBD

## Named queries & tables (incl. geo-specific; verify in queries.xml)
- TBD

## Business-logic flows & formulas
- TBD

## Geo-variants (e.g. PH/MY — prefix, differing fields, routing method)
- TBD

## Inter-module deps & config flags
- TBD

## Ticket history
- {today} — TBD (<TICKET>: cause · flows · queries/methods · UI line; "do not revert" lessons)

## Gotchas / traps
- TBD
"""

PROJECT_TEMPLATE = """\
---
name: <Subsystem> — Project Note
description: Subsystem-level "what changed & why" across modules.
type: project
created_date: {today}
origin_session_id: TBD
updated_date: {today} (init: created)
owner: TBD
last_verified: TBD
code_ref: {code_ref}
tier: T2
status: LIVING
---

# <Subsystem> — Project Note

## Overview (cite file:line or TBD)
TBD
"""

# Full file content when no AGENTS.md/CLAUDE.md exists yet.
AGENTS_MD = """\
# AGENTS.md — {repo}

> Runtime context for coding agents (Claude Code, Codex, Cursor…). Terse on purpose.

<!-- airx:begin -->
## Ground truth (airx — project memory)
Before answering about this codebase: read `ai_memory/MEMORY.md` and the relevant
`reference_*`/`project_*` note. **Cite `file:line`. If you can't, say `TBD` — never invent.**

### When to consult memory (be selective — notes cost tokens)
- DO load `ai_memory/MEMORY.md` + the relevant note before working a HOT/COMPLEX module, a
  multi-tenant/scoping/security change, a bug whose root cause isn't obvious, or anything with
  known traps / do-not-revert lessons.
- SKIP it for a trivial, single-file, greppable lookup (a config value, a constant, an obvious
  symbol) — just grep; loading notes there only burns tokens.
- Rule of thumb: consult memory when a WRONG change would be costly or the right file is
  non-obvious; skip it when grep answers in one hop.
<!-- airx:end -->

## This repo
- Stack: {stack}. Domain: {domain}.
- Objective: **project-memory first** (speed + fewer re-investigations). Docs/KB/viewer are opt-in,
  measured layers — add them only if you want them.

## Posture
- Search before writing; reuse existing code. One change-aspect at a time.
- After each ticket, update the module's memory note (`updated_date: <date> (<ticket>: what changed)`).
"""

CLAUDE_MD = """\
# CLAUDE.md

Working rules live in [`AGENTS.md`](AGENTS.md). Read it first.

<!-- airx:begin -->
## airx — project memory
Before answering: load `ai_memory/MEMORY.md` and the relevant `reference_*`/`project_*` note.
Cite `file:line` or `TBD` · never invent.

### When to consult memory (be selective — notes cost tokens)
- DO load memory + the relevant note before a HOT/COMPLEX module, a multi-tenant/scoping/security
  change, a non-obvious-root-cause bug, or anything with known traps / do-not-revert lessons.
- SKIP it for a trivial, single-file, greppable lookup (config value, constant, obvious symbol) —
  just grep; notes there only burn tokens.
- Rule of thumb: consult memory when a WRONG change is costly or the right file is non-obvious;
  skip it when grep answers in one hop.
<!-- airx:end -->
"""

# Compact block appended to an EXISTING AGENTS.md/CLAUDE.md (never clobber the user's file).
AGENTS_BLOCK = """\
<!-- airx:begin -->
## Ground truth (airx — project memory)
Before answering about this codebase: read `ai_memory/MEMORY.md` and the relevant memory note.
Cite `file:line` or say `TBD` — never invent.

### When to consult memory (be selective — notes cost tokens)
- DO load memory + the relevant note before a HOT/COMPLEX module, a multi-tenant/scoping/security
  change, a non-obvious-root-cause bug, or anything with known traps / do-not-revert lessons.
- SKIP it for a trivial, single-file, greppable lookup (config value, constant, obvious symbol) —
  just grep; notes there only burn tokens.
- Rule of thumb: consult memory when a WRONG change is costly or the right file is non-obvious;
  skip it when grep answers in one hop.
<!-- airx:end -->"""

CLAUDE_BLOCK = """\
<!-- airx:begin -->
## airx — project memory
Before answering: load `ai_memory/MEMORY.md` and the relevant memory note. Cite `file:line` or `TBD`.

### When to consult memory (be selective — notes cost tokens)
- DO load memory + the relevant note before a HOT/COMPLEX module, a multi-tenant/scoping/security
  change, a non-obvious-root-cause bug, or anything with known traps / do-not-revert lessons.
- SKIP it for a trivial, single-file, greppable lookup (config value, constant, obvious symbol) —
  just grep; notes there only burn tokens.
- Rule of thumb: consult memory when a WRONG change is costly or the right file is non-obvious;
  skip it when grep answers in one hop.
<!-- airx:end -->"""

MANIFEST = """\
# .ai-readiness.yml — stamped by airx init
schema: ai-readiness-manifest/1.0
standard: airx
objective_ranking:
  - project-memory
  - TBD
  - TBD
target:
  repo: {repo}
  repo_path: {repo_path}
  code_ref: {code_ref}
self_improve:
  auto_purify: true      # post-commit hook flags stale citations (safe, deterministic)
  auto_enhance: false    # off = propose additions for human approval; on = auto-land verified symbols
created: {today}
"""


def code_ref(repo: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "TBD"
    except Exception:
        return "TBD"


def install_post_commit(repo: Path) -> str | None:
    """Install the self-improve post-commit hook the SHAREABLE way: a committed `.airx-hooks/` dir wired via
    `git config core.hooksPath`, so the loop propagates across clones/teams. Never clobbers an existing
    hooksPath — chains into it. Returns a status string, or None if not a git repo."""
    if not (repo / ".git").exists() and not subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--git-dir"], capture_output=True).returncode == 0:
        return None
    plugin = Path(__file__).resolve().parent.parent          # airx plugin root (tools/..)
    target = subprocess.run(["git", "-C", str(repo), "config", "--get", "core.hooksPath"],
                            capture_output=True, text=True).stdout.strip()
    hooks_dir = repo / (target or ".airx-hooks")
    hooks_dir.mkdir(parents=True, exist_ok=True)
    if not target:
        subprocess.run(["git", "-C", str(repo), "config", "core.hooksPath", ".airx-hooks"])
    shim = hooks_dir / "post-commit"
    call = f'bash "{plugin}/hooks/post-commit.sh" "$@"'      # via bash → no +x needed on the target
    if shim.exists():
        cur = shim.read_text()
        if "post-commit.sh" not in cur:                      # chain into a foreign hook, don't replace
            shim.write_text(cur.rstrip() + "\n" + call + "\n")
    else:
        shim.write_text("#!/usr/bin/env bash\n" + call + "\n")
    shim.chmod(0o755)
    update_gitignore(repo, ["ai_memory/.cache/", "ai_memory/PENDING-ENHANCEMENTS.md"])  # keep tree clean
    return f"core.hooksPath={target or '.airx-hooks'}  →  {shim}"


def detect_stack(repo: Path) -> str:
    """Best-effort stack label from build/manifest files at the repo root. Deterministic, no LLM.
    Returns 'TBD' when nothing recognizable is found (caller may still pass --stack)."""
    try:
        names = {p.name for p in repo.iterdir() if p.is_file()}
    except Exception:
        return "TBD"
    if {"pom.xml", "build.gradle", "build.gradle.kts"} & names:
        # Legacy "beanstack" tell: JSF/PrimeFaces views present → the enterprise-java seed fits.
        try:
            beanstack = next(repo.rglob("*.xhtml"), None) is not None
        except Exception:
            beanstack = False
        return "enterprise-java (legacy beanstack: JSF/PrimeFaces)" if beanstack else "java"
    if "package.json" in names:
        return "node"
    if "pubspec.yaml" in names:
        return "flutter"
    if {"requirements.txt", "pyproject.toml", "setup.py"} & names:
        return "python"
    if "go.mod" in names:
        return "go"
    return "TBD"


_IGNORE_DIRS = {".git", ".github", ".idea", ".vscode", ".mvn", ".gradle", "target", "build", "dist",
                "out", "bin", "node_modules", "__pycache__", "venv", ".venv", "ai_memory",
                "ai_documentation", "ai_knowledge_base"}
_CODE_EXT = {".java", ".kt", ".py", ".go", ".ts", ".js", ".rb", ".cs"}


def _subdirs(d: Path) -> list[Path]:
    try:
        return [p for p in sorted(d.iterdir())
                if p.is_dir() and p.name not in _IGNORE_DIRS and not p.name.startswith(".")]
    except Exception:
        return []


def _has_code(d: Path) -> bool:
    try:
        return any(p.is_file() and p.suffix in _CODE_EXT for p in d.iterdir())
    except Exception:
        return False


def _module_base(repo: Path):
    """Return (base, names): the directory whose immediate children are the modules, and their names.
    1) Multi-module build (Maven/Gradle): repo root + the sub-modules.
    2) Single-module: the source package root (descend src/main/java, collapse single-child chains)
       so modules are the real packages (petclinic's owner/vet/model), not top dirs (gradle/k8s/src).
    3) Fallback: repo root + top-level dirs."""
    top = _subdirs(repo)
    multi = [p.name for p in top
             if any((p / b).is_file() for b in ("pom.xml", "build.gradle", "build.gradle.kts"))]
    if multi:
        return repo, multi
    for cand in ("src/main/java", "src/main/kotlin", "src", "lib", "app"):
        base = repo / cand
        if not base.is_dir():
            continue
        cur = base
        while True:  # collapse org/springframework/samples/petclinic -> petclinic
            kids = _subdirs(cur)
            if len(kids) == 1 and not _has_code(cur):
                cur = kids[0]
            else:
                break
        names = [p.name for p in _subdirs(cur)]
        if names:
            return cur, names
    return repo, [p.name for p in top]


def detect_modules(repo: Path, limit: int = 12) -> list[str]:
    """Candidate module names from repo structure (REAL dirs, to verify — never asserted)."""
    return _module_base(repo)[1][:limit]


def rank_modules(repo: Path, limit: int = 12) -> list[tuple]:
    """Every detected module ranked by recent git churn (changed-file hits, last year; 0 if untouched).
    Deterministic — this is the 'how do I know which module' map seeded into MEMORY.md."""
    base, names = _module_base(repo)
    if not names:
        return []
    nameset = set(names)
    rel = base.relative_to(repo).as_posix() if base != repo else ""
    prefix = "" if rel in ("", ".") else rel + "/"
    counts = {n: 0 for n in names}
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "log", "--since=1 year ago", "--name-only", "--pretty=format:"],
            capture_output=True, text=True, timeout=30).stdout
        for line in out.splitlines():
            line = line.strip()
            if prefix and not line.startswith(prefix):
                continue
            seg = line[len(prefix):].split("/", 1)[0]
            if seg in nameset:
                counts[seg] += 1
    except Exception:
        pass
    ranked = sorted(names, key=lambda n: (-counts[n], n))
    return [(n, counts[n]) for n in ranked[:limit]]


def candidates_md(ranked: list) -> str:
    """ranked: list of (name, churn). Rendered hottest-first with recent-activity counts."""
    if not ranked:
        return ("- _none auto-detected — run `/airx:memory`; it proposes the hottest areas from git "
                "churn and you pick one._")
    lines = []
    for i, (name, churn) in enumerate(ranked):
        tag = "  ← hottest" if i == 0 and churn > 0 else ""
        activity = f"{churn} recent change{'s' if churn != 1 else ''}" if churn else "no recent changes"
        lines.append(f"- `{name}` — {activity} · `/airx:memory {name}`{tag}")
    return "\n".join(lines)


def write_context_file(path: Path, full: str, block: str) -> bool:
    """Create with full content if absent; otherwise append the airx block ONCE (idempotent), never
    clobbering the user's existing file. Returns True iff the file was newly created."""
    if not path.exists():
        path.write_text(full)
        return True
    text = path.read_text(errors="ignore")
    if AIRX_BEGIN not in text:
        path.write_text(text.rstrip() + "\n\n" + block + "\n")
    return False


def update_gitignore(repo: Path, entries: list[str]) -> None:
    gi = repo / ".gitignore"
    existing = gi.read_text(errors="ignore") if gi.is_file() else ""
    have = set(existing.split())
    add = [e for e in entries if e not in have]
    if not add:
        return
    with gi.open("a") as f:
        if existing and not existing.endswith("\n"):
            f.write("\n")
        f.write("# airx (local-only layout)\n" + "\n".join(add) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Stamp the memory layer of an airx skeleton.")
    ap.add_argument("--repo", required=True, help="path to the code repo")
    ap.add_argument("--layout", choices=["in-repo", "sibling", "ignored"], default="in-repo",
                    help="where airx files live (default: in-repo, so the agent auto-loads memory)")
    ap.add_argument("--out", help="wiki dir for --layout sibling (default: ../<repo>-wiki)")
    ap.add_argument("--stack", default=None, help="override; default is auto-detected from build files")
    ap.add_argument("--domain", default="TBD")
    ap.add_argument("--install-hook", action="store_true",
                    help="install the post-commit self-improve hook via git core.hooksPath (.airx-hooks/)")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"error: repo {repo} not found")
        return 2

    if args.layout == "sibling":
        wiki = Path(args.out).resolve() if args.out else repo.parent / f"{repo.name}-wiki"
        repo_path = f"../{repo.name}"
    else:  # in-repo or ignored: airx lives inside the repo so the agent auto-loads it
        wiki = repo
        repo_path = "."

    mem = wiki / "ai_memory"
    mem.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    ref = code_ref(repo)
    stack = args.stack or detect_stack(repo)
    ranked = rank_modules(repo)
    modules = [n for n, _ in ranked]
    ctx = dict(today=today, code_ref=ref, repo=repo.name,
               repo_path=repo_path, stack=stack, domain=args.domain)

    # Memory-only footprint: ai_memory/ + context files + manifest. No docs/ or kb/ folders.
    (mem / "MEMORY.md").write_text(MEMORY_INDEX.format(candidates=candidates_md(ranked)))
    (mem / "_reference_TEMPLATE.md").write_text(REFERENCE_TEMPLATE.format(**ctx))
    (mem / "_project_TEMPLATE.md").write_text(PROJECT_TEMPLATE.format(**ctx))
    created_agents = write_context_file(wiki / "AGENTS.md", AGENTS_MD.format(**ctx), AGENTS_BLOCK)
    created_claude = write_context_file(wiki / "CLAUDE.md", CLAUDE_MD.format(**ctx), CLAUDE_BLOCK)
    (wiki / ".ai-readiness.yml").write_text(MANIFEST.format(**ctx))

    if args.layout == "ignored":
        ig = ["ai_memory/", ".ai-readiness.yml"]
        if created_claude:
            ig.append("CLAUDE.md")
        if created_agents:
            ig.append("AGENTS.md")
        update_gitignore(repo, ig)

    hook_status = install_post_commit(repo) if args.install_hook else None

    auto = stack != "TBD" and not args.stack
    print(f"airx init ✓  {wiki}  (layout={args.layout})")
    print(f"  ai_memory/ (MEMORY.md + templates) · AGENTS.md · CLAUDE.md · .ai-readiness.yml")
    print(f"  stack={stack}{' (auto-detected)' if auto else ''}  code_ref={ref}")
    if args.install_hook:
        print(f"  self-improve hook: {hook_status or 'NOT installed (not a git repo)'}")
    if ranked:
        top_n, top_c = ranked[0]
        hot = f"{top_n} ({top_c} recent changes)" if top_c else top_n
        more = f" — full ranked map in ai_memory/MEMORY.md (+{len(ranked) - 1} more)" if len(ranked) > 1 else ""
        print(f"  modules: hottest = {hot}{more}")
    print()
    print("  next:  /airx:memory     → it proposes your hottest modules from git; pick one (memory is the win)")
    print("  later (optional — only if you want them):")
    print("         /airx:docs  human documentation   ·   /airx:kb  knowledge base (token lever, per-stack)")
    print("         /airx:view  browse what you've built")
    print(f"  note: memory works on ANY stack; a KB pack for '{stack}' may not exist yet — memory-only is fine.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
