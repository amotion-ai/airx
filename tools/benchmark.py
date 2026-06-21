#!/usr/bin/env python3
"""airx benchmark — honest, deterministic token measurement (no LLM).

Proves what project memory and/or a knowledge base actually buy ON THIS REPO — honestly.
Memory-first repos can run this with NO KB: just a `memory_note` per question measures the memory win.
For each question it computes the tokens to answer up to four ways:

  • bare     — grep the source repo and read the matches      (the COLD path: no memory, no KB)
  • memory   — load the verified note that answers it          (WITH project memory)
  • kb_mcp   — query the index, get back just matching item(s) (WITH a KB)
  • kb_files — load the WHOLE registry the answer lives in     (naive KB arm)

The memory win = (bare − memory) / bare: tokens saved by loading one verified note instead of
re-deriving the answer by grepping/reading the repo. The KB win = (kb_files − kb_mcp) / kb_files.

Token estimate = chars/4 (model-agnostic). Honest by design: precise lookups win ~99%; broad/conceptual
queries win little; small/modern repos can be neutral-or-negative. The point is to SHOW which.

    python3 benchmark.py <wiki-dir>
Reads:  <wiki>/ai_knowledge_base/benchmark.json
        (each question's `measure` may carry: grep_term, registry [KB arm], memory_note [memory arm])
        memory_note paths are resolved under <wiki>/ai_memory/.
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
    mem_dir = wiki / "ai_memory"
    try:  # reuse the citation checker for per-note resolved/total (file:line + symbols)
        import importlib.util
        _vp = Path(__file__).resolve().parent / "verify-citations.py"
        _vs = importlib.util.spec_from_file_location("airx_vc", _vp)
        vc = importlib.util.module_from_spec(_vs); _vs.loader.exec_module(vc)
    except Exception:
        vc = None
    idx = vc.build_index(repo) if (vc and repo and repo.is_dir()) else None  # symbol index, built once
    rows, tf, tm, tb = [], 0, 0, 0
    tmem, tb_mem = 0, 0  # memory-note tokens, and bare tokens for the questions that HAVE a note
    for q in bench["questions"]:
        m = q.get("measure")
        if not m:
            continue
        regname = m.get("registry")
        reg = (kb / regname) if regname else None
        term = m.get("grep_term") or m.get("args", {}).get("query", "")
        f = toks(reg.read_text()) if reg and reg.is_file() else 0
        mc = kb_mcp_tokens(reg, term) if reg and reg.is_file() else 0
        b = bare_tokens(repo, term)
        # memory arm: cost of loading the one verified note that answers the question,
        # plus accuracy (does the note contain the expected answer?) and citation resolution.
        notename = m.get("memory_note")
        note = (mem_dir / notename) if notename else None
        mem = ans = cites = None
        if note and note.is_file():
            _txt = note.read_text(errors="ignore")
            mem = toks(_txt)
            _exp = m.get("expect")
            ans = (_exp.lower() in _txt.lower()) if _exp is not None else None
            if vc and repo and repo.is_dir():
                _t, _r, _ = vc.note_citations(repo, note)          # file:line
                _by, _ = vc.note_symbols(idx, note) if idx else ({}, [])  # class/query/bean
                _st = sum(v["total"] for v in _by.values())
                _sr = sum(v["resolved"] for v in _by.values())
                tot, res = _t + _st, _r + _sr
                cites = f"{res}/{tot}" if tot else "0/0"
        red = round((f - mc) / f * 100, 1) if f else None
        red_mem = round((b - mem) / b * 100, 1) if (b and mem is not None) else None
        tf += f; tm += mc; tb += (b or 0)
        if mem is not None and b:
            tmem += mem; tb_mem += b
        rows.append({"id": q.get("id"), "cat": q.get("category"), "kb_files": f,
                     "kb_mcp": mc, "bare": b, "memory": mem, "answers": ans, "cites": cites,
                     "reduction_vs_files": red, "reduction_vs_bare_via_memory": red_mem})

    total = round((tf - tm) / tf * 100, 1) if tf else None
    mem_total = round((tb_mem - tmem) / tb_mem * 100, 1) if tb_mem else None
    (kb / "results").mkdir(exist_ok=True)
    (kb / "results" / "token-reduction.json").write_text(json.dumps(
        {"wiki": wiki.name, "totals": {"kb_files": tf, "kb_mcp": tm, "bare": tb, "memory": tmem,
         "reduction_vs_files": total, "memory_reduction_vs_bare": mem_total},
         "per_question": rows}, indent=2))

    print(f"AIRX BENCHMARK  {wiki.name}  (token ≈ chars/4, no LLM)")
    print(f"  bare-grep repo: {repo if repo else '(none — bare arm skipped)'}")
    print(f"  {'Q':4} {'cat':10} {'bare':>10} {'memory':>8} {'mem%':>7} {'ans':>4} {'cites':>6} {'kb_files':>9} {'kb_mcp':>8} {'red%':>7}")
    for r in rows:
        print(f"  {str(r['id']):4} {str(r['cat']):10} "
              f"{(r['bare'] if r['bare'] is not None else '-'):>10} "
              f"{(r['memory'] if r['memory'] is not None else '-'):>8} "
              f"{(r['reduction_vs_bare_via_memory'] if r['reduction_vs_bare_via_memory'] is not None else '-'):>7} "
              f"{('yes' if r['answers'] else 'no' if r['answers'] is not None else '-'):>4} "
              f"{(str(r['cites']) if r['cites'] is not None else '-'):>6} "
              f"{r['kb_files']:>9} {r['kb_mcp']:>8} "
              f"{(r['reduction_vs_files'] if r['reduction_vs_files'] is not None else '-'):>7}")
    print(f"  {'TOT':4} {'':10} {tb:>10} {tmem:>8} {str(mem_total):>7} {'':>4} {'':>6} {tf:>9} {tm:>8} {str(total):>7}")
    if mem_total is not None:
        print(f"\n  → MEMORY: {mem_total}% fewer tokens to answer via a verified note vs grepping the repo "
              f"({tmem} vs {tb_mem}).")
    a_n = sum(1 for r in rows if r.get("answers"))
    a_d = sum(1 for r in rows if r.get("answers") is not None)
    if a_d:
        print(f"  → accuracy: the note answers {a_n}/{a_d} questions (expected term present); "
              f"'cites' = resolved/total per note (dangling = stale/hallucinated).")
    if total is not None:
        print(f"  → KB: {total}% fewer tokens via index query vs loading registries ({tm} vs {tf}); "
              f"vs grep: {tm} vs {tb}.")
    print("  Honest: precise lookups win big; broad queries win little; if it doesn't pay, stay memory-only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
