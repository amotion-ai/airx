#!/usr/bin/env python3
"""airx completeness — does an area's note actually COVER the area? (the per-note depth gauge)

The map says what exists; this measures whether the authored note mentions the area's key declared
symbols — so "is the note thorough?" becomes a number + a gap list, not a vibe. It's the measure-don't-
assume answer to "memory isn't doing a good job": run it after /airx:memory and drive MISSING → 0 (cover
the symbol, or record an explicit TBD for why it's out of scope).

It does NOT verify citations (that's verify-citations / check) and it never edits notes — it reports
coverage of the area's classes / public methods / named queries against the note's text. Deterministic,
stdlib, no LLM. Composes extract.py's scanners + init._module_base; never re-implements them.

    python3 completeness.py <wiki-dir> [module]
Without [module]: reports every authored reference_*/project_* note. Exit: 0 (advisory); 2 on usage error.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import airxpaths as ap


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


vc = _load("airx_vc", HERE / "verify-citations.py")
init = _load("airx_init", HERE / "init.py")
extract = _load("airx_extract", HERE / "extract.py")

CAP = 12  # cap the printed MISSING list per category so the report stays scannable


def _present(token: str, text: str) -> bool:
    return re.search(r"\b" + re.escape(token) + r"\b", text) is not None


def area_symbols(repo: Path, module: str):
    """(classes, methods, queries) declared in the module — reusing extract.py's deterministic scanners."""
    base, _ = init._module_base(repo)
    d = base / module
    if not d.is_dir():
        return [], [], []
    classes = [n for n, _ in extract.extract_classes(d)]
    methods = sorted({s.split("(")[0].split()[-1] for _, s in extract.extract_methods(d) if s.split("(")[0].split()})
    queries = [q for q, _ in extract.extract_queries(d)]
    return classes, methods, queries


def report_note(repo: Path, mem: Path, note: Path) -> tuple:
    module = note.stem.split("_", 1)[1] if "_" in note.stem else note.stem
    text = note.read_text(errors="ignore")
    classes, methods, queries = area_symbols(repo, module)
    cats = [("classes", classes), ("methods", methods), ("named queries", queries)]
    tot = cov = 0
    print(f"\n  {note.name}  (area: {module})")
    missing_all = []
    for label, syms in cats:
        if not syms:
            print(f"    {label:14} —  (none declared in the area)")
            continue
        miss = [s for s in syms if not _present(s, text)]
        c = len(syms) - len(miss)
        tot += len(syms); cov += c
        bar = "ok " if not miss else "GAP"
        print(f"    {label:14} {c}/{len(syms)} covered  [{bar}]"
              + (f"  missing: {', '.join(miss[:CAP])}" + (" …" if len(miss) > CAP else "") if miss else ""))
        missing_all += [(label, m) for m in miss]
    pct = round(cov / tot * 100) if tot else 100
    print(f"    → completeness {pct}%  ({cov}/{tot} declared symbols mentioned in the note)")
    return cov, tot, missing_all


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: completeness.py <wiki-dir> [module]", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2
    repo = vc.repo_from_manifest(wiki)
    if repo is None or not repo.is_dir():
        print("airx completeness — no resolvable repo_path in manifest (run /airx:init first).")
        return 0
    mem = ap.memory(wiki)
    arg = sys.argv[2] if len(sys.argv) == 3 else None

    if arg:
        note = mem / f"reference_{arg}.md"
        if not note.is_file():
            note = mem / f"project_{arg}.md"
        if not note.is_file():
            print(f"airx completeness — no note for '{arg}' yet (reference_{arg}.md). Author it with "
                  f"/airx:memory {arg}.")
            return 0
        notes = [note]
    else:
        notes = sorted(p for p in mem.glob("*.md")
                       if not p.name.startswith("_") and p.name not in vc.NON_NOTES
                       and (p.stem.startswith("reference_") or p.stem.startswith("project_")))
        if not notes:
            print("airx completeness — no authored notes yet (run /airx:memory).")
            return 0

    print(f"AIRX COMPLETENESS  {wiki.name}   (does each note cover its area's declared symbols?)")
    g_cov = g_tot = 0
    for note in notes:
        cov, tot, _ = report_note(repo, mem, note)
        g_cov += cov; g_tot += tot
    if len(notes) > 1:
        print(f"\n  OVERALL  {round(g_cov / g_tot * 100) if g_tot else 100}%  ({g_cov}/{g_tot} across {len(notes)} notes)")
    print("\n  Drive MISSING → 0: cover the symbol in the note (cite it), or record an explicit TBD for "
          "why it's out of scope. Coverage of code, not of intent — pair with /airx:score for depth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
