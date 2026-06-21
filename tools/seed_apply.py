#!/usr/bin/env python3
"""airx seed — apply a predict-and-verify SEED bundle to jump-start a wiki's memory.

A seed gives a repo of a known archetype a head start instead of a blank page. The SEED-*.md files
are PREDICTIONS tagged [family]/[verify]/[fill] — hypotheses the human confirms against code, NOT
facts. Deterministic, stdlib only, no LLM.

    python3 seed_apply.py <wiki-dir> [archetype]

Archetype comes from the arg, else is inferred from the manifest's `stack`
("enterprise-java"/"beanstack" → enterprise-java), else defaults to enterprise-java if its bundle
exists. The SEED-*.md files are copied into `<wiki>/ai_memory/_seed/` and additionally given a
leading-underscore filename so EVERY existing tool skips them as non-notes:
  - check.py     — non-recursive `glob("*.md")` never descends into `_seed/`.
  - score.py     — excludes `_seed` in path parts AND `_`-prefixed names.
  - verify-citations.py — recursive `glob("**/*.md")`, but skips any `md.name` starting with `_`.
So copied files land as `ai_memory/_seed/_SEED-*.md` — belt and suspenders, no tool edits needed.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SEED_ROOT = PLUGIN_ROOT / "seed-memory"

RULE = ("These are PREDICTIONS ([verify]/[fill]); confirm each against code via /airx:memory before "
        "treating as fact, then promote to reference_<module>.md.")


def read_stack(wiki: Path) -> str:
    """Best-effort `stack` value from the manifest. Flat scan: works whether `stack:` is top-level or
    nested under `target:` (the indentation is irrelevant to a substring match)."""
    man = wiki / ".ai-readiness.yml"
    if not man.is_file():
        return ""
    for line in man.read_text(errors="ignore").splitlines():
        s = line.strip()
        if s.startswith("stack:"):
            return s.split(":", 1)[1].strip()
    return ""


def infer_archetype(wiki: Path) -> str | None:
    """archetype from the manifest stack, else default enterprise-java IF its bundle exists."""
    stack = read_stack(wiki).lower()
    if "enterprise-java" in stack or "beanstack" in stack:
        return "enterprise-java"
    if (SEED_ROOT / "enterprise-java").is_dir():
        return "enterprise-java"
    return None


def main() -> int:
    if len(sys.argv) not in (2, 3):
        print("usage: seed_apply.py <wiki-dir> [archetype]", file=sys.stderr)
        return 2

    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2

    archetype = sys.argv[2] if len(sys.argv) == 3 else infer_archetype(wiki)
    if not archetype:
        print("airx seed: no archetype given and none inferable from the manifest stack — "
              "pass one, e.g.  python3 seed_apply.py <wiki> enterprise-java")
        return 0

    bundle = SEED_ROOT / archetype
    seeds = sorted(bundle.glob("SEED-*.md")) if bundle.is_dir() else []
    if not seeds:
        avail = sorted(p.name for p in SEED_ROOT.iterdir() if p.is_dir()) if SEED_ROOT.is_dir() else []
        print(f"airx seed: no SEED bundle for archetype '{archetype}' (no-op). "
              f"Available: {', '.join(avail) or 'none'}.")
        return 0

    dest = wiki / "ai_memory" / "_seed"
    dest.mkdir(parents=True, exist_ok=True)

    applied, skipped = [], []
    for src in seeds:
        # leading `_` on the filename so verify-citations (recursive) also skips it as a non-note.
        out = dest / ("_" + src.name)
        if out.exists():
            skipped.append(out.name)
            continue
        shutil.copy2(src, out)
        applied.append(out.name)

    rel = dest.relative_to(wiki)
    print(f"airx seed ✓  archetype={archetype}  →  {rel}/")
    if applied:
        print(f"  applied: {', '.join(applied)}")
    if skipped:
        print(f"  skipped (already present, not overwritten): {', '.join(skipped)}")
    if not applied and not skipped:
        print("  (nothing to apply)")
    print()
    print(f"  RULE: {RULE}")
    print("  (Excluded from note counts/citation checks — verify before promoting.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
