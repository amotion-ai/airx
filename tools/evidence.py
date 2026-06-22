#!/usr/bin/env python3
"""airx evidence — one "is the project memory actually working?" report for the beta team.

Aggregates the existing tools into a single, plain-English verdict. Deterministic, stdlib only, no LLM.
Composes (never clones) the calibrated logic:
  • QUALITY  — captured verbatim from score.py (Coverage · Depth · Trust + OVERALL/grade + verdict).
  • TRUST    — verify-citations resolution: file:line (hard) + symbols (advisory), from one check_wiki call.
  • DRIFT    — check.py's drift signal = the SYMBOL resolution rate (class/query/bean still in code).
  • TOKEN    — benchmark's memory_reduction_vs_bare from results/token-reduction.json, else "run benchmark".

CRITICAL framing (the product's corrected thesis): the headline is QUALITY + TRUST. Token-% is SECONDARY and
explicitly labelled "not a quality measure (a thin stub scores 99%)". A thin TBD stub wins on tokens yet is
useless — so token-% never leads.

    python3 evidence.py <wiki-dir>
Exit: 0 ALWAYS (advisory). Pairs with /airx:benchmark — run that first to populate the token arm.
"""
from __future__ import annotations

import importlib.util
import io
import json
import re
import sys
from contextlib import redirect_stdout
from pathlib import Path


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


HERE = Path(__file__).resolve().parent


def _rule(title: str) -> None:
    print(f"\n── {title} " + "─" * max(2, 60 - len(title)))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: evidence.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2

    print(f"AIRX EVIDENCE  {wiki.name}   — is project memory earning its place?")

    # ---- QUALITY: reuse score.py verbatim (calibrated Coverage/Depth/Trust + OVERALL/grade) ----
    overall, grade = None, None
    _rule("QUALITY  (is the memory actually good? — the headline)")
    try:
        score = _load("airx_score", HERE / "score.py")
        buf = io.StringIO()
        _saved = sys.argv
        sys.argv = ["score.py", str(wiki)]
        try:
            with redirect_stdout(buf):
                score.main()
        finally:
            sys.argv = _saved
        out = buf.getvalue().rstrip("\n")
        print(out)
        m = re.search(r"OVERALL\s+(\d+)/100\s+grade\s+(\w)", out)
        if m:
            overall, grade = int(m.group(1)), m.group(2)
    except Exception as e:
        print(f"  (quality unavailable: {e})")

    # ---- one citation pass: drives both TRUST and DRIFT ----
    cw = None
    try:
        vc = _load("airx_vc", HERE / "verify-citations.py")
        cw = vc.check_wiki(wiki)
    except Exception as e:
        print(f"\n  (citation verification unavailable: {e})")

    fl_t = fl_r = st = sr = 0
    fl_ok = True  # no dangling file:line citations
    _rule("TRUST  (do the citations resolve to real code? — the headline)")
    if cw is None:
        print("  citation verification did not run")
    elif cw.get("error"):
        print(f"  WARN  {cw['error']}")
    else:
        fl_t, fl_r = cw.get("total", 0), cw.get("resolved", 0)
        sym = cw.get("sym", {})
        st = sum(v["total"] for v in sym.values())
        sr = sum(v["resolved"] for v in sym.values())
        dangling = [p for p in cw.get("problems", []) if "dangling" in p]
        fl_ok = not dangling
        print(f"  scanned {cw.get('files', 0)} note(s) against {cw.get('repo')}")
        print(f"  file:line  {fl_r}/{fl_t} resolve"
              + (f"   DANGLING: {len(dangling)} (hallucinated/stale)" if dangling else "   (no danglers)"))
        srate = round(sr / st * 100) if st else 100
        print(f"  symbols    {sr}/{st} resolve ({srate}%)   class/query/bean — advisory, rest to review")

    # ---- DRIFT: check.py's drift = the symbol resolution rate (memory-vs-code signal) ----
    _rule("DRIFT  (has the code moved out from under the notes?)")
    if st:
        drift = round((st - sr) / st * 100)
        verdict = "low — notes track the code" if drift <= 10 else "elevated — re-verify the notes"
        print(f"  {drift}% of symbol citations no longer resolve ({st - sr}/{st} renamed/missing) — {verdict}")
    else:
        print("  no symbol citations to measure drift against")

    # ---- TOKEN: SECONDARY — explicitly not a quality measure ----
    _rule("TOKEN WIN  (secondary — NOT a quality measure; a thin stub scores 99%)")
    tok_pct = None
    res = wiki / "ai_knowledge_base" / "results" / "token-reduction.json"
    try:
        if res.is_file():
            data = json.loads(res.read_text())
            tot = data.get("totals", {})
            tok_pct = tot.get("memory_reduction_vs_bare")
            if tok_pct is not None:
                print(f"  {tok_pct}% fewer tokens to answer via a verified note vs grepping the repo "
                      f"(memory {tot.get('memory')} vs bare {tot.get('bare')}).")
            else:
                print("  benchmark ran but no memory arm measured — add memory_note fields, re-run /airx:benchmark")
        else:
            print("  no benchmark results yet — run /airx:benchmark first to populate the token arm")
    except Exception as e:
        print(f"  (token results unreadable: {e})")

    # ---- VERDICT: keyed off QUALITY + TRUST, never token-% ----
    _rule("VERDICT")
    cites_line = f"{fl_r + sr}/{fl_t + st} cites resolve" if (fl_t + st) else "no citations yet"
    tok_line = f"{tok_pct}% token win on covered Qs" if tok_pct is not None else "token win: run /airx:benchmark"
    if overall is None:
        print("  UNKNOWN — could not compute a quality score; run /airx:score and /airx:check directly.")
    elif overall >= 70 and fl_ok and (fl_t + st == 0 or (fl_r + sr) / (fl_t + st) >= 0.85):
        print(f"  GOOD: memory is earning its place — {overall}/100 (grade {grade}), {cites_line}, {tok_line}.")
        print("  WHY: it's well-covered and the citations resolve to real code, so an agent can trust it.")
    else:
        reasons = []
        if overall < 70:
            reasons.append(f"quality {overall}/100 (grade {grade}) — coverage/depth still thin")
        if not fl_ok:
            reasons.append("dangling file:line citations (hallucinated or stale)")
        if (fl_t + st) and (fl_r + sr) / (fl_t + st) < 0.85:
            reasons.append("too many citations don't resolve (drift)")
        print(f"  NOT YET: {cites_line}, {tok_line}.")
        print("  WHY: " + "; ".join(reasons) + ". Run /airx:memory on more modules, then re-verify.")
    print("\n  Read top-down: QUALITY + TRUST decide it; token-% is a bonus, not the bar. Advisory only.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
