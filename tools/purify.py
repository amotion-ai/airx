#!/usr/bin/env python3
"""airx purify — flag stale/dangling citations in memory notes. SAFE: never invents, never deletes facts.

Two modes:
  (default) report-only — prints findings, EDITS NOTHING. Used by the post-commit hook so the working
                          tree stays clean after every commit.
  --apply               — annotates each dangling file:line citation inline with ' ⚠️ STALE — re-verify'
                          and stamps frontmatter 'needs_review: <date>'. Used by /airx:purify, where the
                          human reviews the diff. Never rewrites the claim, never invents a fix.

Only confident-stale file:line citations are flagged (a line that no longer exists / file gone). Symbol
drift (class/query/bean) is surfaced as a rate by /airx:check + verify-citations, not inline-annotated
here, because external library symbols are indistinguishable from renamed ones without import analysis.

    python3 purify.py <wiki-dir> [--apply]
Exit: 0 always (advisory).
"""
from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("airx_vc", HERE / "verify-citations.py")
vc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(vc)

MARK = " ⚠️ STALE — re-verify"


def dangling_in_note(repo: Path, md: Path) -> list[str]:
    """Raw file:line citations in this note that no longer resolve to a real line."""
    out, seen = [], set()
    for m in vc.CITE.finditer(md.read_text(errors="ignore")):
        raw, path = m.group(0), m.group(1)
        ext = path.rsplit(".", 1)[-1]
        if raw in seen or path.endswith(".md") or path.startswith("http"):
            continue
        if "." not in path or ext.lower() not in vc._CODE_EXTS:
            continue
        seen.add(raw)
        status, _ = vc.resolve_one(repo, path, int(m.group(2)), int(m.group(3)) if m.group(3) else None)
        if status == "dangling":
            out.append(raw)
    return out


def apply_marks(md: Path, raws: list[str]) -> bool:
    """Append the STALE marker to each line carrying a dangling citation; stamp needs_review. Idempotent."""
    lines = md.read_text(errors="ignore").split("\n")
    changed = False
    for i, ln in enumerate(lines):
        if MARK in ln:
            continue
        if any(raw in ln for raw in raws):
            lines[i] = ln.rstrip() + MARK
            changed = True
    if not changed:
        return False
    text = "\n".join(lines)
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1 and "needs_review:" not in text[:end]:
            text = text[:end] + f"\nneeds_review: {date.today().isoformat()}" + text[end:]
    md.write_text(text)
    return True


def main() -> int:
    apply = "--apply" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: purify.py <wiki-dir> [--apply]", file=sys.stderr)
        return 2
    wiki = Path(args[0]).resolve()
    repo = vc.repo_from_manifest(wiki)
    mem = wiki / "ai_memory"
    print(f"AIRX PURIFY  {wiki.name}  ({'apply' if apply else 'report-only'})")
    if repo is None or not repo.is_dir() or not mem.is_dir():
        # if the repo dir is missing, EVERY citation would look dangling — refuse rather than mass-flag.
        print(f"  cannot verify (repo_path '{repo}' not found / no ai_memory) — skipping, nothing flagged")
        return 0
    notes = [p for p in sorted(mem.glob("**/*.md"))
             if not p.name.startswith("_") and p.name not in vc.NON_NOTES and ".cache" not in p.parts]
    total, touched = 0, 0
    for md in notes:
        raws = dangling_in_note(repo, md)
        if not raws:
            continue
        total += len(raws)
        print(f"  {md.name}: {len(raws)} dangling — {', '.join(raws[:4])}{'…' if len(raws) > 4 else ''}")
        if apply and apply_marks(md, raws):
            touched += 1
    if total == 0:
        print("  clean — no dangling file:line citations.")
    elif apply:
        print(f"  flagged {total} citation(s) across {touched} note(s) with{MARK.strip()} + needs_review. "
              f"Review the diff; re-verify or fix (or /airx:enhance).")
    else:
        print(f"  {total} dangling across {len(notes)} note(s). Run /airx:purify to flag inline (--apply), "
              f"or /airx:enhance to fix.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
