#!/usr/bin/env python3
"""airx status — the "where am I / what do I do next" memory dashboard (the orchestrator's ledger).

One deterministic readout of an airx wiki: which layers exist, how much of the codebase has memory, do
the citations resolve, and the proven token win — plus the single highest-leverage NEXT action so the
memory loop is self-driving. Memory-first: KB/docs/view are shown only if present, never pushed.

Composes the existing surface (init.rank_modules, verify-citations.check_wiki, the benchmark result) —
never re-derives. Stdlib only, no LLM. Writes `.airx/STATUS.md` (regenerable) and prints the same.

    python3 status.py <wiki-dir>
Exit: 0 (advisory); 2 on usage error.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import airxpaths as ap


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


vc = _load("airx_vc", HERE / "verify-citations.py")
init = _load("airx_init", HERE / "init.py")


def covered_modules(mem: Path) -> set:
    covered = set()
    if not mem.is_dir():
        return covered
    for p in mem.glob("**/*.md"):
        if (p.name.startswith("_") or p.name in vc.NON_NOTES
                or ".cache" in p.parts or "_seed" in p.parts):
            continue
        for pre in ("reference_", "project_"):
            if p.stem.startswith(pre):
                covered.add(p.stem[len(pre):])
    return covered


def gather(wiki: Path) -> dict:
    mem = ap.memory(wiki)
    d = {"layers": [], "modules": [], "covered": set(), "notes": 0,
         "fl": (0, 0), "sym": (0, 0), "token": None, "repo": None}
    # layers present (memory-first; others only if real on disk)
    if mem.is_dir():
        d["layers"].append("memory")
    if ap.docs(wiki).is_dir() and any(ap.docs(wiki).glob("*.md")):
        d["layers"].append("docs")
    if (ap.kb(wiki) / "registry").is_dir() and any((ap.kb(wiki) / "registry").glob("*.json")):
        d["layers"].append("kb")
    if any(ap.view(wiki).glob("*.html")) if ap.view(wiki).is_dir() else False:
        d["layers"].append("view")
    # real authored notes
    if mem.is_dir():
        d["notes"] = len([p for p in mem.glob("*.md")
                          if not p.name.startswith("_") and p.name not in vc.NON_NOTES])
    # coverage vs detected modules
    repo = vc.repo_from_manifest(wiki)
    d["repo"] = repo
    if repo and repo.is_dir():
        try:
            d["modules"] = init.rank_modules(repo)
        except Exception:
            d["modules"] = []
    d["covered"] = covered_modules(mem)
    # trust (citation resolution)
    try:
        cw = vc.check_wiki(wiki)
        if not cw.get("error"):
            d["fl"] = (cw.get("resolved", 0), cw.get("total", 0))
            sym = cw.get("sym", {})
            d["sym"] = (sum(v["resolved"] for v in sym.values()),
                        sum(v["total"] for v in sym.values()))
    except Exception:
        pass
    # token win (only if benchmark has run)
    res = mem / ".cache" / "token-reduction.json"
    if res.is_file():
        try:
            d["token"] = json.loads(res.read_text()).get("totals", {}).get("memory_reduction_vs_bare")
        except Exception:
            pass
    return d


def next_action(d: dict) -> str:
    names = [n for n, _ in d["modules"]]
    uncovered = [(n, c) for n, c in d["modules"] if n not in d["covered"]]
    if d["notes"] == 0:
        if uncovered:
            return f"author your first note → /airx:memory {uncovered[0][0]}  (hottest module)"
        return "author your first note → /airx:memory"
    if uncovered:
        return f"document the next hot module → /airx:memory {uncovered[0][0]}  ({uncovered[0][1]} churn)"
    fl_r, fl_t = d["fl"]; sy_r, sy_t = d["sym"]
    if (fl_t + sy_t) and (fl_r + sy_r) < (fl_t + sy_t):
        return "re-verify drifted citations → /airx:purify then /airx:enhance"
    if d["token"] is None:
        return "prove the win → /airx:benchmark   (then /airx:evidence)"
    return "coverage complete ✓ — keep notes fresh (/airx:update after tickets) and re-score periodically"


def render(wiki: Path, d: dict) -> str:
    n_mod = len(d["modules"])
    n_cov = len([n for n, _ in d["modules"] if n in d["covered"]])
    cov_pct = round(n_cov / n_mod * 100) if n_mod else 0
    fl_r, fl_t = d["fl"]; sy_r, sy_t = d["sym"]
    tot_r, tot_t = fl_r + sy_r, fl_t + sy_t
    trust = round(tot_r / tot_t * 100) if tot_t else 100
    tok = f"{d['token']}% fewer tokens vs grep" if d["token"] is not None else "not measured (run /airx:benchmark)"
    uncovered = [n for n, _ in d["modules"] if n not in d["covered"]][:5]
    lines = [
        f"# airx status — {wiki.name}",
        "",
        f"- **Layers:** {', '.join(d['layers']) or 'none (run /airx:init)'}",
        f"- **Memory coverage:** {n_cov}/{n_mod} modules ({cov_pct}%) · {d['notes']} authored note(s)",
        f"- **Trust:** {tot_r}/{tot_t} citations resolve ({trust}%)",
        f"- **Token win:** {tok}",
        f"- **NEXT:** {next_action(d)}",
    ]
    if uncovered:
        lines += ["", "Uncovered (hottest first): " + ", ".join(uncovered)
                  + (" …" if len([n for n, _ in d['modules'] if n not in d['covered']]) > 5 else "")]
    lines += ["",
              "_Memory-first: docs/KB/viewer are opt-in and shown only if present. Regenerate with "
              "`/airx:status`._"]
    return "\n".join(lines) + "\n"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: status.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2
    if not ap.manifest(wiki).is_file():
        print(f"airx status — {wiki} is not an airx wiki yet (run /airx:init).")
        return 0
    d = gather(wiki)
    doc = render(wiki, d)
    try:                                       # .airx/STATUS.md (regenerable dashboard)
        out = ap.base(wiki) / "STATUS.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(doc)
    except Exception:
        pass
    print(doc, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
