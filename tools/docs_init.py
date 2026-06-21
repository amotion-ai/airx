#!/usr/bin/env python3
"""airx docs_init — scaffold the human-documentation layer (Pillar 1) of an AI-readiness wiki.

OPT-IN, deterministic, stdlib only, no LLM. init.py does NOT call this — it runs only when invoked
(via /airx:docs). Creates `<wiki>/ai_documentation/` with a small SUBSET of the universal doc catalog:
ARCHITECTURE, MULTI-TENANCY, SECURITY, DATABASE, TROUBLESHOOTING, CONFIGURATION-REFERENCE — each a
narrative skeleton (frontmatter + section headers + `TBD` placeholders + the cite-or-TBD rule), plus a
README.md index. These are HUMAN docs (sequential, narrative) — distinct from ai_memory/ (agent context).

    python3 docs_init.py <wiki-dir>

Re-runnable: skips the folder if it already exists and is non-empty (never clobbers human-filled docs).
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# cite-or-TBD rule line — reused verbatim in every doc (the one non-negotiable).
RULE = ("> Every concrete claim cites a real `file:line` **or** says `TBD — needs human input`. "
        "Never invent paths, classes, or methods. Fill via `/airx:memory`-style sourcing.")


def _frontmatter(name: str, today: str, ref: str) -> str:
    return (
        "---\n"
        f"name: {name}\n"
        "type: documentation\n"
        f"created_date: {today}\n"
        "last_verified: TBD\n"
        f"code_ref: {ref}\n"
        "status: LIVING\n"
        "---\n"
    )


def _doc(name: str, title: str, purpose: str, sections: list[str], today: str, ref: str) -> str:
    body = [
        _frontmatter(name, today, ref),
        f"\n# {title}\n",
        f"\n> {purpose}\n",
        f"\n{RULE}\n",
    ]
    for sec in sections:
        body.append(f"\n## {sec}\n\nTBD — needs human input.\n")
    return "".join(body)


# (filename, title, one-line purpose, [section headers]) — a SUBSET of the universal catalog.
DOCS = [
    ("ARCHITECTURE.md", "Architecture",
     "How the system is structured: components, boundaries, and how data flows between them.",
     ["Overview", "Components", "Data flow", "Diagram (Mermaid)", "Cross-cutting concerns"]),
    ("MULTI-TENANCY.md", "Multi-Tenancy",
     "How tenants are isolated: the scoping rule that must hold on every read and write.",
     ["The scoping rule", "Where tenant context is set", "Where it is enforced (queries, filters)",
      "Known gaps / cross-tenant risks"]),
    ("SECURITY.md", "Security",
     "Authentication, authorization, secrets handling, and the threat model.",
     ["Authentication", "Authorization", "Secrets & credentials", "Threat model", "Known issues"]),
    ("DATABASE.md", "Database",
     "Schema, key entities, indexes, and the migration policy.",
     ["Engine & connection", "Key entities", "Indexes & constraints", "Migration policy"]),
    ("TROUBLESHOOTING.md", "Troubleshooting",
     "Symptom -> diagnosis -> fix for the failures on-call actually sees.",
     ["Common symptoms", "Diagnosis steps", "Fixes & workarounds", "Escalation"]),
    ("CONFIGURATION-REFERENCE.md", "Configuration Reference",
     "Every environment variable / config property: name, default, effect, and where it is read.",
     ["Environment variables", "Config files & properties", "Defaults & overrides",
      "Where each is read (cite file:line)"]),
]


def readme(names_titles: list[tuple[str, str]], today: str, ref: str) -> str:
    rows = "\n".join(f"| [`{fn}`]({fn}) | {title} |" for fn, title in names_titles)
    return (
        _frontmatter("Documentation — index", today, ref)
        + "\n# Documentation\n"
        + "\n> Human-narrative documentation for this repo — read sequentially, for engineers, on-call, "
          "and new joiners. This is the OPT-IN docs layer; it is distinct from `ai_memory/` (dense agent "
          "context, queried not read). Each doc is a skeleton: fill it with cited content.\n"
        + f"\n{RULE}\n"
        + "\n## Documents\n\n| Doc | Purpose |\n|---|---|\n" + rows + "\n"
        + "\n## How to fill these\n\n"
          "1. Pick a doc. 2. Source each claim from the code (`/airx:memory`-style: read, then cite "
          "`file:line`). 3. Replace `TBD` with cited prose; leave `TBD — needs human input` where you "
          "cannot verify. 4. When a human confirms a doc against the code, set its `last_verified` date.\n"
    )


def read_manifest(wiki: Path) -> dict:
    """Parse the SUBSET of `.ai-readiness.yml` we need (target.code_ref, target.repo_path).
    Tiny indent-aware line parser — stdlib only, matching init.py's no-yaml-dep style."""
    out: dict = {}
    mf = wiki / ".ai-readiness.yml"
    if not mf.is_file():
        return out
    in_target = False
    for raw in mf.read_text(errors="ignore").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indented = line[0] in " \t"
        key = line.strip().split(":", 1)[0].strip()
        if not indented:
            in_target = (key == "target")
            continue
        if in_target and ":" in line:
            k, v = line.strip().split(":", 1)
            out[k.strip()] = v.strip()
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python3 docs_init.py <wiki-dir>")
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki dir {wiki} not found")
        return 2

    manifest = read_manifest(wiki)
    ref = manifest.get("code_ref", "TBD") or "TBD"
    today = date.today().isoformat()

    docs_dir = wiki / "ai_documentation"
    if docs_dir.exists() and any(docs_dir.iterdir()):
        print(f"airx docs — {docs_dir} already exists and is non-empty; leaving it untouched.")
        print("  (delete it or empty it first if you want a fresh scaffold.)")
        return 0
    docs_dir.mkdir(parents=True, exist_ok=True)

    created = []
    for fn, title, purpose, sections in DOCS:
        (docs_dir / fn).write_text(_doc(fn, title, purpose, sections, today, ref))
        created.append((fn, title))
    (docs_dir / "README.md").write_text(readme(created, today, ref))

    print(f"airx docs ✓  {docs_dir}  (code_ref={ref})")
    print(f"  README.md (index) + {len(created)} doc skeletons:")
    for fn, title in created:
        print(f"    {fn:<28} {title}")
    print()
    print("  these are HUMAN narrative docs (opt-in) — distinct from ai_memory/ agent context.")
    print("  next:  fill each with /airx:memory-style sourcing — cite file:line or TBD; never invent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
