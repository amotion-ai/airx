#!/usr/bin/env python3
"""airx init — stamp a memory-first AI-readiness skeleton beside a repo.

Memory-first by design: creates ONLY ai_memory/ + the context files + the manifest.
No knowledge base, no docs — those are opt-in layers you add (and measure) later.
Stdlib only, deterministic, no LLM.

    python3 init.py --repo <path-to-code-repo> [--out <wiki-dir>] [--stack S] [--domain D]
"""
from __future__ import annotations

import argparse
import subprocess
from datetime import date
from pathlib import Path

MEMORY_INDEX = """\
# Project Memory — index

> What the agent should load before working a module: the "why & what-changed" it would otherwise
> re-derive every session. Each note cites a real `file:line` or says `TBD`. Add a row per module.

## Spine (cross-cutting, verify against code)
- _TBD — architecture spine, multi-tenancy/scoping rule, the one load-bearing fact._

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

> Every concrete claim cites a real `file:line` or says `TBD — needs human input`. Never invent.

## What it is
TBD

## Key code (file:line)
- TBD

## What changed & why (ticket-linked)
- {today} — TBD (TICKET: what changed, the trap, "do not revert" lessons)

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

AGENTS_MD = """\
# AGENTS.md — {repo}

> Runtime context for coding agents (Claude Code, Codex, Cursor…). Terse on purpose.

## Ground truth
Before answering about this codebase: read `{wiki}/ai_memory/MEMORY.md` and the relevant
`reference_*`/`project_*` note. **Cite `file:line`. If you can't, say `TBD` — never invent.**

## This repo
- Stack: {stack}. Domain: {domain}.
- Objective: **project-memory first** (speed + fewer re-investigations). KB/docs are opt-in, measured layers.

## Posture
- Search before writing; reuse existing code. One change-aspect at a time.
- After each ticket, update the module's memory note (`updated_date: <date> (<ticket>: what changed)`).
"""

CLAUDE_MD = """\
# CLAUDE.md

Working rules live in [`AGENTS.md`](AGENTS.md). Read it first.
Before answering: load `{wiki}/ai_memory/` · cite `file:line` or `TBD` · never invent.
"""

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
created: {today}
"""


def code_ref(repo: Path) -> str:
    try:
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "TBD"
    except Exception:
        return "TBD"


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


def main() -> int:
    ap = argparse.ArgumentParser(description="Stamp a memory-first airx skeleton.")
    ap.add_argument("--repo", required=True, help="path to the code repo")
    ap.add_argument("--out", help="wiki dir (default: ../<repo>-wiki)")
    ap.add_argument("--stack", default=None, help="override; default is auto-detected from build files")
    ap.add_argument("--domain", default="TBD")
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    if not repo.is_dir():
        print(f"error: repo {repo} not found")
        return 2
    wiki = Path(args.out).resolve() if args.out else repo.parent / f"{repo.name}-wiki"
    mem = wiki / "ai_memory"
    mem.mkdir(parents=True, exist_ok=True)

    today = date.today().isoformat()
    ref = code_ref(repo)
    stack = args.stack or detect_stack(repo)
    ctx = dict(today=today, code_ref=ref, repo=repo.name,
               repo_path=f"../{repo.name}", stack=stack, domain=args.domain,
               wiki=wiki.name)

    (mem / "MEMORY.md").write_text(MEMORY_INDEX)
    (mem / "_reference_TEMPLATE.md").write_text(REFERENCE_TEMPLATE.format(**ctx))
    (mem / "_project_TEMPLATE.md").write_text(PROJECT_TEMPLATE.format(**ctx))
    (wiki / "AGENTS.md").write_text(AGENTS_MD.format(**ctx))
    (wiki / "CLAUDE.md").write_text(CLAUDE_MD.format(**ctx))
    (wiki / ".ai-readiness.yml").write_text(MANIFEST.format(**ctx))

    print(f"airx init ✓  {wiki}")
    print(f"  ai_memory/ (MEMORY.md + templates) · AGENTS.md · CLAUDE.md · .ai-readiness.yml")
    print(f"  stack={stack}{' (auto-detected)' if not args.stack and stack != 'TBD' else ''}")
    print(f"  code_ref={ref}  objective=project-memory-first (KB/docs opt-in, measured later)")
    print(f"  next: /airx:memory <module>  →  then  /airx:check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
