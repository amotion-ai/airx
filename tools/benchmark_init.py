#!/usr/bin/env python3
"""airx benchmark_init — scaffold a starter, memory-only benchmark so a user can PROVE impact.

The token-win proof (`/airx:benchmark`) needs a `benchmark.json` of questions, but nothing authored it —
so a memory-only user could never measure their note's impact. This writes a deterministic starter from
the notes they ALREADY have: it derives honest `grep_term`s from each note's *resolved* citations
(class / named-query / bean / cited file) and points each question at that note.

It COMPOSES `verify-citations.py` (build_index + the same membership sets it resolves against) — it never
re-implements resolution. `expect` is left BLANK on purpose: the token win is measured honestly, and the
accuracy arm stays "-" until the user fills a real business answer (predict-and-verify, not a vanity yes).

Footprint: writes `.airx/ai_memory/benchmark.json` — the memory benchmark lives WITH memory, never in
`ai_knowledge_base/` (that's the opt-in KB layer). A memory-only repo never grows a KB folder.

    python3 benchmark_init.py <wiki-dir>
Exit: 0 on success or a no-op (idempotent — never clobbers an existing benchmark.json); 2 on usage error.
Stdlib only, no LLM.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); import airxpaths as ap


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


vc = _load("airx_vc", HERE / "verify-citations.py")

MAX_Q = 6  # a starter set — enough to show the win; the user broadens it by hand.


def note_grep_terms(idx: dict, repo: Path, md: Path) -> list:
    """Distinct, repo-resolvable terms cited by a note, best-first: symbols (class / named-query / bean)
    then cited-file basenames. Resolution = membership in verify-citations' own index (compose, not clone)."""
    text = md.read_text(errors="ignore")
    terms, seen = [], set()

    def add(tok):
        if tok and tok not in seen:
            seen.add(tok); terms.append(tok)

    # symbols in backticks — same predicates note_symbols resolves against
    for m in vc.BACKTICK.finditer(text):
        tok = m.group(1).strip()
        if not tok or "(" in tok or ":" in tok or "/" in tok:
            continue
        if vc.NQ_TOK.match(tok) and not tok.endswith((".java", ".xml", ".md", ".xhtml")):
            if tok in idx["named_queries"]:
                add(tok)                                   # an externalized named query
            elif tok.split(".", 1)[0] in idx["types"]:
                add(tok.split(".", 1)[0])                  # Owner.member → grep the owning class
        elif vc.CLASS_TOK.match(tok) and tok in idx["types"]:
            add(tok)
    for m in vc.BEAN_ANN.finditer(text):
        if m.group(1) in idx["beans"]:
            add(m.group(1))
    # fallback: resolvable file:line citations → grep the file's basename stem
    if not terms:
        for m in vc.CITE.finditer(text):
            path = m.group(1)
            if path.endswith(".md") or path.startswith("http"):
                continue
            status, _ = vc.resolve_one(repo, path, int(m.group(2)),
                                       int(m.group(3)) if m.group(3) else None)
            if status == "resolved":
                add(Path(path).stem)
    return terms


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: benchmark_init.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2
    mem = ap.memory(wiki)
    if not mem.is_dir():
        print("airx benchmark_init — no ai_memory/ (run /airx:init first).")
        return 0
    out = mem / "benchmark.json"
    if out.is_file():
        print(f"airx benchmark_init — {out} already exists; edit it by hand (never clobbered).")
        return 0

    repo = vc.repo_from_manifest(wiki)
    if repo is None or not repo.is_dir():
        print("airx benchmark_init — no resolvable repo_path in manifest; cannot derive grep terms.")
        return 0

    notes = sorted(p for p in mem.glob("**/*.md")
                   if not p.name.startswith("_") and p.name not in vc.NON_NOTES
                   and ".cache" not in p.parts and "_seed" not in p.parts)
    if not notes:
        print("airx benchmark_init — no authored notes yet; run /airx:memory first, then re-run.")
        return 0

    idx = vc.build_index(repo, cache_dir=mem / ".cache")
    questions, n = [], 0
    for md in notes:
        rel = md.relative_to(mem).as_posix()
        for term in note_grep_terms(idx, repo, md):
            n += 1
            questions.append({
                "id": f"q{n}",
                "category": "lookup",
                "question": f"Where/what is `{term}`?",
                # `expect` intentionally OMITTED — accuracy stays "-" until the user adds a real
                # expected answer (see _note). An empty/missing expect is "not asserted", never a vanity yes.
                "measure": {"grep_term": term, "memory_note": rel},
            })
            if len(questions) >= MAX_Q:
                break
        if len(questions) >= MAX_Q:
            break

    if not questions:
        print("airx benchmark_init — found notes but no repo-resolvable citations to derive terms from. "
              "Add a few cited symbols to a note (or author benchmark.json by hand), then re-run.")
        return 0

    payload = {
        "_note": ("Starter scaffold from airx benchmark_init — questions derived from your notes' "
                  "resolved citations. The token win is measured as-is. To enable the ACCURACY arm, "
                  "fill each question's measure.expect with a real expected answer (a phrase the note "
                  "should contain). Edit/add questions freely; this file is yours."),
        "questions": questions,
    }
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"airx benchmark_init ✓  {out}  ({len(questions)} starter question(s))")
    print("  next: /airx:benchmark  → token win vs grep (accuracy shows '-' until you fill 'expect').")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
