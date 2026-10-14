#!/usr/bin/env python3
"""airx paths — the single source of truth for WHERE airx's layers live.

All airx artifacts live under `<wiki>/.airx/`: `ai_memory/`, `ai_knowledge_base/`, `ai_documentation/`,
`view/`, and the `.ai-readiness.yml` manifest. Only the agent context files (`CLAUDE.md` / `AGENTS.md`)
stay at the repo/wiki root, so the coding agent auto-loads them.

Back-compat: pre-`.airx` installs kept these folders at the wiki root. Every resolver prefers `.airx/`
and falls back to the legacy root location, so older repos keep working with no migration.

Stdlib only, zero deps. Tools import it with `import airxpaths` (the tools dir is placed on sys.path by
the small guard each tool runs, so it resolves under both direct `python3 tools/x.py` runs and importlib
loads from elsewhere).
"""
from __future__ import annotations

import sys
from pathlib import Path

MANIFEST_NAME = ".ai-readiness.yml"


def base(wiki) -> Path:
    """The directory that CONTAINS the layer folders.
    New installs: `<wiki>/.airx`. Legacy installs (pre-.airx): `<wiki>` itself, detected by a root
    `ai_memory/` or a root manifest. Fresh repos (nothing yet) default to `<wiki>/.airx`."""
    wiki = Path(wiki)
    airx = wiki / ".airx"
    if airx.is_dir():
        return airx
    if (wiki / "ai_memory").is_dir() or (wiki / MANIFEST_NAME).is_file():
        return wiki                      # legacy layout (pre-.airx) — keep working
    return airx                          # fresh install → everything under .airx


def memory(wiki) -> Path:
    return base(wiki) / "ai_memory"


def kb(wiki) -> Path:
    return base(wiki) / "ai_knowledge_base"


def docs(wiki) -> Path:
    return base(wiki) / "ai_documentation"


def view(wiki) -> Path:
    return base(wiki) / "view"


def manifest(wiki) -> Path:
    """Path to the manifest. Prefers `<wiki>/.airx/.ai-readiness.yml`, falls back to the legacy root
    file, and defaults to the `.airx` location for fresh installs. (repo_path inside the manifest is
    still resolved relative to `<wiki>` by callers, so the repo location is unaffected by this move.)"""
    wiki = Path(wiki)
    a = wiki / ".airx" / MANIFEST_NAME
    if a.is_file():
        return a
    legacy = wiki / MANIFEST_NAME
    if legacy.is_file():
        return legacy
    return a


def is_wiki(wiki) -> bool:
    return manifest(wiki).is_file()


def main() -> int:
    """Diagnostic: print the resolved airx layer paths for a wiki (handy when debugging layout)."""
    if len(sys.argv) != 2:
        print("usage: airxpaths.py <wiki-dir>   (prints resolved .airx layer paths)", file=sys.stderr)
        return 2
    w = sys.argv[1]
    for label, p in (("base", base(w)), ("memory", memory(w)), ("kb", kb(w)),
                     ("docs", docs(w)), ("view", view(w)), ("manifest", manifest(w))):
        print(f"  {label:9} {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
