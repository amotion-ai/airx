#!/usr/bin/env python3
"""airx benchmark — honest, deterministic token measurement (no LLM).

Proves what a knowledge base actually buys ON THIS REPO — and reports honestly when it doesn't pay.
Applies once a KB exists (memory-first repos add a KB only when this benchmark justifies it).
For each question it computes the tokens to answer three ways:

  • bare     — grep the source repo and read the matches      (what you do WITHOUT a KB)
  • kb_mcp   — query the index, get back just matching item(s) (WITH a KB)
  • kb_files — load the WHOLE registry the answer lives in     (naive arm)

Token estimate = chars/4 (model-agnostic). Honest by design: precise lookups win ~99%; broad/conceptual
queries win little; small/modern repos can be neutral-or-negative. The point is to SHOW which.

    python3 benchmark.py <wiki-dir>
Reads:  <wiki>/ai_knowledge_base/benchmark.json
Writes: <wiki>/ai_knowledge_base/results/token-reduction.json
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def toks(s: str) -> int:
    return max(1, len(s) // 4)


def load_json(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def item_lists(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                yield v
            elif isinstance(v, dict):
                yield from item_lists(v)
    elif isinstance(obj, list) and obj and isinstance(obj[0], dict):
        yield obj


def kb_mcp_tokens(registry: Path, term: str) -> int:
    data = load_json(registry)
    if data is None:
        return 0
    t = term.lower()
    hits = [it for lst in item_lists(data) for it in lst
            if t in json.dumps(it, separators=(",", ":")).lower()]
    return 8 if not hits else toks(json.dumps(hits, separators=(",", ":")))


def bare_tokens(repo: Path, term: str):
    if not repo or not repo.is_dir():
        return None
    try:
        out = subprocess.run(["grep", "-rI", "--", term, str(repo)],
                             capture_output=True, text=True, timeout=60)
        return toks(out.stdout)
    except Exception:
        return None


def repo_from_manifest(wiki: Path):
    man = wiki / ".ai-readiness.yml"
    if not man.is_file():
        return None
    for line in man.read_text().splitlines():
        line = line.strip()
        if line.startswith("repo_path:"):
            v = line.split(":", 1)[1].strip()
            if v and v != "TBD":
                return Path(v) if Path(v).is_absolute() else (wiki / v).resolve()
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: benchmark.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    kb = wiki / "ai_knowledge_base"
    bench = load_json(kb / "benchmark.json")
    if not bench or "questions" not in bench:
        print(f"error: no usable {kb/'benchmark.json'} (memory-first repo? benchmark applies once a KB exists)",
              file=sys.stderr)
        return 2

    repo = repo_from_manifest(wiki)
    rows, tf, tm, tb = [], 0, 0, 0
    for q in bench["questions"]:
        m = q.get("measure")
        if not m:
            continue
        reg = kb / m["registry"]
        term = m.get("grep_term") or m.get("args", {}).get("query", "")
        f = toks(reg.read_text()) if reg.is_file() else 0
        mc = kb_mcp_tokens(reg, term) if reg.is_file() else 0
        b = bare_tokens(repo, term)
        red = round((f - mc) / f * 100, 1) if f else None
        tf += f; tm += mc; tb += (b or 0)
        rows.append({"id": q.get("id"), "cat": q.get("category"), "kb_files": f,
                     "kb_mcp": mc, "bare": b, "reduction_vs_files": red})

    total = round((tf - tm) / tf * 100, 1) if tf else None
    (kb / "results").mkdir(exist_ok=True)
    (kb / "results" / "token-reduction.json").write_text(json.dumps(
        {"wiki": wiki.name, "totals": {"kb_files": tf, "kb_mcp": tm, "bare": tb,
         "reduction_vs_files": total}, "per_question": rows}, indent=2))

    print(f"AIRX BENCHMARK  {wiki.name}  (token ≈ chars/4, no LLM)")
    print(f"  bare-grep repo: {repo if repo else '(none — bare arm skipped)'}")
    print(f"  {'Q':4} {'cat':10} {'kb_files':>9} {'kb_mcp':>8} {'bare':>10} {'red%':>7}")
    for r in rows:
        print(f"  {str(r['id']):4} {str(r['cat']):10} {r['kb_files']:>9} {r['kb_mcp']:>8} "
              f"{(r['bare'] if r['bare'] is not None else '-'):>10} "
              f"{(r['reduction_vs_files'] if r['reduction_vs_files'] is not None else '-'):>7}")
    print(f"  {'TOT':4} {'':10} {tf:>9} {tm:>8} {tb:>10} {str(total):>7}")
    print(f"\n  → {total}% fewer tokens via KB query vs loading registries ({tm} vs {tf}); "
          f"vs grep: {tm} vs {tb}.")
    print("  Honest: precise lookups win big; broad queries win little; if it doesn't pay, stay memory-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
