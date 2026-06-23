#!/usr/bin/env python3
"""airx modules — list the repo's candidate modules, churn-ranked, marking which already have a note.

So `/airx:memory` can SHOW you the choices (and explain HOW they're ranked) instead of asking blind —
the gap a beta user hit ("Which module?" with no list). Deterministic, stdlib, no LLM. Composes
`init.rank_modules` (git-churn ranking) + the same note-coverage detection `score.py` uses.

    python3 modules.py <wiki-dir>
Exit: 0 (advisory); 2 on usage error.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); import airxpaths as ap


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


vc = _load("airx_vc", HERE / "verify-citations.py")
init = _load("airx_init", HERE / "init.py")


def covered_modules(mem: Path) -> set:
    """Module names that already have a note — by note-file stem (reference_<m>.md / project_<m>.md),
    the same coverage signal score.py uses."""
    covered = set()
    if not mem.is_dir():
        return covered
    for p in mem.glob("**/*.md"):
        if (p.name.startswith("_") or p.name in vc.NON_NOTES
                or ".cache" in p.parts or "_seed" in p.parts):
            continue
        for pre in ("reference_", "project_"):
            if p.stem.startswith(pre):
                covered.add(p.stem[len(pre):])
    return covered


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: modules.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2
    repo = vc.repo_from_manifest(wiki)
    if repo is None or not repo.is_dir():
        print("airx modules — no resolvable repo_path in manifest (run /airx:init first).")
        return 0
    ranked = init.rank_modules(repo)
    if not ranked:
        print("airx modules — no modules auto-detected from repo structure.\n"
              "  /airx:memory can still take a plain-language area (e.g. \"the billing flow\").")
        return 0
    covered = covered_modules(ap.memory(wiki))

    print(f"AIRX MODULES  {wiki.name}   (ranked by recent git churn; falls back to repo structure)")
    for name, churn in ranked:
        mark = "note ✓" if name in covered else "—"
        print(f"  {name:<28} churn {churn:<5} {mark}")
    nxt = next((n for n, _ in ranked if n not in covered), None)
    if nxt:
        nc = dict(ranked)[nxt]
        print(f"\n  NEXT (no note yet, hottest first): {nxt} ({nc} churn)  →  /airx:memory {nxt}")
    else:
        print("\n  all detected modules have a note ✓")
    print("  ranking = changed-file count over the last year; pick the hottest module you work in.")
    print("  one dense note per hot module — coverage grows over time; you don't author them all at once.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
