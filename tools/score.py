#!/usr/bin/env python3
"""airx score — a QUALITY score for project memory: Coverage · Depth · Trust.

Token-reduction is deliberately NOT used here: a thin TBD stub can score 99% on tokens yet be useless.
This scores whether memory is actually GOOD —
  • Coverage : how much of the codebase has a note (notes vs detected code modules)
  • Depth    : per-note richness (verified citations, ticket history, traps, low TBD-ratio)
  • Trust    : how many citations still resolve (file:line + symbols), via verify-citations
Calibrated so deep, hand-curated memory scores HIGH and a thin/TBD stub scores LOW — the opposite of what
token-% does. Reuses tools/verify-citations.py (symbol-aware) and tools/init.py (module detection).

    python3 score.py <wiki-dir>
Exit: 0 always (advisory). Pairs with /airx:check (trust/freshness gate) and /airx:benchmark (token win).
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


HERE = Path(__file__).resolve().parent
vc = _load("airx_vc", HERE / "verify-citations.py")
init = _load("airx_init", HERE / "init.py")

TICKET = re.compile(r"\b[A-Z]{2,}-\d+\b")                       # SKI-44, DMSMOD-400, PCSNG-992
TRAP = re.compile(r"trap|gotcha|do not|do-not|don't|never |must not|caution|do[- ]not[- ]revert", re.I)


def clamp(x) -> int:
    return max(0, min(100, int(round(x))))


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: score.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    mem = wiki / "ai_memory"
    # real notes only — exclude templates, the index, and seed scaffolding (_seed/, SEED-*, MODULE-MAP…)
    _SEED = {"SEED-", "MODULE-MAP", "DOMAIN-GLOSSARY", "example-"}
    notes = sorted(p for p in mem.glob("**/*.md")
                   if not p.name.startswith("_") and p.name != "MEMORY.md"
                   and "_seed" not in p.parts
                   and not any(p.name.startswith(s) for s in _SEED)) if mem.is_dir() else []
    n_notes = len(notes)
    repo = vc.repo_from_manifest(wiki)

    # --- Coverage: notes vs detected code modules (the module map init produces) ---
    modules = []
    if repo and repo.is_dir():
        try:
            modules = init.rank_modules(repo)
        except Exception:
            modules = []
    n_modules = max(len(modules), 1)
    coverage = clamp(n_notes / n_modules * 100)

    # --- Trust + citation totals via the symbol-aware verifier ---
    cw = vc.check_wiki(wiki)
    fl_t, fl_r = cw.get("total", 0), cw.get("resolved", 0)
    sym = cw.get("sym", {})
    st = sum(v["total"] for v in sym.values())
    sr = sum(v["resolved"] for v in sym.values())
    tot_cites, res_cites = fl_t + st, fl_r + sr
    trust = clamp(res_cites / tot_cites * 100) if tot_cites else 0

    # --- Depth: per-note richness ---
    files = cw.get("files", 0) or 1
    avg_res = res_cites / files
    cite_density = clamp(avg_res / 15 * 100)               # 15 verified cites/note = full marks
    with_ticket = sum(1 for p in notes if TICKET.search(p.read_text(errors="ignore")))
    with_trap = sum(1 for p in notes if TRAP.search(p.read_text(errors="ignore")))
    tbd = sum(len(re.findall(r"\bTBD\b", p.read_text(errors="ignore"))) for p in notes)
    ticket_score = clamp(with_ticket / max(n_notes, 1) * 100)
    trap_score = clamp(with_trap / max(n_notes, 1) * 100)
    tbd_ratio = tbd / (tbd + res_cites) if (tbd + res_cites) else 0
    tbd_score = clamp((1 - tbd_ratio) * 100)
    depth = round((cite_density + ticket_score + trap_score + tbd_score) / 4)

    overall = round(0.45 * coverage + 0.35 * depth + 0.20 * trust)
    grade = ("A" if overall >= 85 else "B" if overall >= 70 else
             "C" if overall >= 55 else "D" if overall >= 40 else "F")

    print(f"AIRX SCORE  {wiki.name}   (quality, not tokens)")
    print(f"  repo: {repo}")
    print(f"  notes: {n_notes}   detected code modules: {len(modules)}")
    print(f"  Coverage  {coverage:3}/100   {n_notes} notes / {len(modules)} modules")
    print(f"  Depth     {depth:3}/100   cites/note {avg_res:.1f}→{cite_density} · ticket {ticket_score} · "
          f"traps {trap_score} · non-TBD {tbd_score}")
    print(f"  Trust     {trust:3}/100   {res_cites}/{tot_cites} citations resolve")
    print(f"  ── OVERALL {overall}/100  grade {grade}   (0.45·Cov + 0.35·Depth + 0.20·Trust)")

    flags = []
    if coverage < 55:
        flags.append(f"only {n_notes}/{len(modules)} modules documented")
    if tbd_ratio > 0.15:
        flags.append(f"{round(tbd_ratio * 100)}% TBD")
    if ticket_score < 50:
        flags.append("little/no ticket history (the crown-jewel tacit knowledge)")
    if trust < 80:
        flags.append(f"{100 - trust}% of citations don't resolve (drift)")
    print("  verdict: " + ("GOOD — deep, well-covered, verified" if not flags else "NOT DONE — " + "; ".join(flags)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
