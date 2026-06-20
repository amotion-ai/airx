#!/usr/bin/env python3
"""airx verify-citations — check that every file:line cited in memory notes resolves to real code.

A note's credibility IS its citations. This confirms each `path.ext:line` (or `:start-end`) in
ai_memory/ points at a real line in the repo, catching hallucinated or stale citations
(the SOTA "mechanical citation verification" idea). Deterministic, stdlib only, no LLM.

    python3 verify-citations.py <wiki-dir>
Exit: 0 = all resolvable citations point at real lines (or none found / no repo); 1 = dangling exist.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

# A path with an extension, then :line or :start-end. The extension requirement avoids matching
# "T2", "v0.1", "12:30", "line 5", etc. Captures: path, start, end(optional).
CITE = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?")


def repo_from_manifest(wiki: Path):
    man = wiki / ".ai-readiness.yml"
    if man.is_file():
        for line in man.read_text(errors="ignore").splitlines():
            line = line.strip()
            if line.startswith("repo_path:"):
                v = line.split(":", 1)[1].strip()
                if v and v != "TBD":
                    return Path(v) if Path(v).is_absolute() else (wiki / v).resolve()
    return None


def resolve_one(repo: Path, path: str, start: int, end):
    """Return (status, detail). status in {resolved, dangling, ambiguous}."""
    if "/" in path:
        cands = [repo / path] if (repo / path).is_file() else []
    else:
        cands = list(repo.rglob(path))
    if not cands:
        return "dangling", "file not found in repo"
    if len(cands) > 1:
        return "ambiguous", f"{len(cands)} files named {path}"
    try:
        n = sum(1 for _ in cands[0].open(errors="ignore"))
    except Exception:
        return "dangling", "unreadable"
    hi = end or start
    if 1 <= start <= n and 1 <= hi <= n and start <= hi:
        return "resolved", ""
    return "dangling", f"line {start}{'-' + str(end) if end else ''} > {n} lines (stale?)"


def note_citations(repo: Path, md: Path):
    """(total, resolved, problems[]) for one note."""
    total = resolved = 0
    problems = []
    seen = set()
    for m in CITE.finditer(md.read_text(errors="ignore")):
        raw, path = m.group(0), m.group(1)
        if raw in seen or path.endswith(".md") or path.startswith("http"):
            continue
        seen.add(raw)
        total += 1
        status, detail = resolve_one(repo, path, int(m.group(2)),
                                     int(m.group(3)) if m.group(3) else None)
        if status == "resolved":
            resolved += 1
        else:
            problems.append(f"{md.name}: {raw} ({status}: {detail})")
    return total, resolved, problems


def check_wiki(wiki: Path) -> dict:
    repo = repo_from_manifest(wiki)
    out = {"repo": repo, "files": 0, "total": 0, "resolved": 0, "problems": []}
    if repo is None or not repo.is_dir():
        out["error"] = "no resolvable repo_path in manifest — cannot verify"
        return out
    mem = wiki / "ai_memory"
    if not mem.is_dir():
        return out
    for md in sorted(mem.glob("**/*.md")):
        if md.name.startswith("_") or md.name == "MEMORY.md":
            continue
        t, r, probs = note_citations(repo, md)
        if t:
            out["files"] += 1
            out["total"] += t
            out["resolved"] += r
            out["problems"] += probs
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: verify-citations.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    r = check_wiki(wiki)
    print(f"AIRX VERIFY-CITATIONS  {wiki.name}")
    if r.get("error"):
        print(f"  WARN  {r['error']}")
        return 0
    print(f"  scanned {r['files']} note(s) against {r['repo']}")
    print(f"  citations: {r['total']}  resolved: {r['resolved']}  problems: {len(r['problems'])}")
    for p in r["problems"]:
        print(f"  PROBLEM  {p}")
    if any("dangling" in p for p in r["problems"]):
        print("  FAIL - dangling citations (hallucinated or stale). Fix the note or mark TBD.")
        return 1
    if r["total"] == 0:
        print("  (no file:line citations found)")
    else:
        print("  OK - every resolvable citation points at a real line.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
