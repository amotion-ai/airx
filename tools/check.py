#!/usr/bin/env python3
"""airx check — conformance for a memory-first AI-readiness wiki.

Memory-first: ai_memory/ is REQUIRED; ai_documentation/ and ai_knowledge_base/ are optional, opt-in
layers (noted if present, never required). Deterministic, stdlib only, no LLM.

    python3 check.py <wiki-dir>
Exit: 0 = PASS/WARN, 1 = FAIL (gates CI).
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# memory notes use `name` (not `title`); see AGENTS.md / frontmatter rules
REQUIRED_MEMORY_KEYS = {"name", "owner", "last_verified", "code_ref", "status"}


def parse_manifest(wiki: Path) -> dict:
    f = wiki / ".ai-readiness.yml"
    out = {}
    if f.is_file():
        for line in f.read_text().splitlines():
            m = re.match(r"^\s*([a-z_]+):\s*(\S.*)$", line)
            if m:
                out[m.group(1)] = m.group(2).strip()
    return out


def frontmatter_keys(md: Path) -> set:
    txt = md.read_text(errors="ignore")
    if not txt.startswith("---"):
        return set()
    end = txt.find("\n---", 3)
    if end == -1:
        return set()
    return {m.group(1) for m in re.finditer(r"^([a-z_]+):", txt[3:end], re.M)}


def head_ref(wiki: Path, repo_path: str | None) -> str:
    repo = (wiki / repo_path).resolve() if repo_path and repo_path != "TBD" else wiki
    try:
        r = subprocess.run(["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check.py <wiki-dir>", file=sys.stderr)
        return 2
    wiki = Path(sys.argv[1]).resolve()
    if not wiki.is_dir():
        print(f"error: {wiki} not found", file=sys.stderr)
        return 2

    results, fail = [], False
    man = parse_manifest(wiki)

    # manifest
    if not man:
        results.append(("manifest", "FAIL", "no .ai-readiness.yml")); fail = True
    else:
        results.append(("manifest", "PASS", f"standard={man.get('standard','?')}"))

    # structure — ai_memory REQUIRED; others optional/noted
    mem = wiki / "ai_memory"
    if not mem.is_dir():
        results.append(("structure", "FAIL", "missing required folder: ai_memory")); fail = True
        notes = []
    else:
        # exclude airx-generated non-notes (index/report/worklist), not just templates
        _non_notes = {"MEMORY.md", "PENDING-ENHANCEMENTS.md", "VALIDATION-REPORT.md"}
        notes = [p for p in mem.glob("*.md")
                 if not p.name.startswith("_") and p.name not in _non_notes]
        opt = [d for d in ("ai_documentation", "ai_knowledge_base") if (wiki / d).is_dir()]
        has_index = (mem / "MEMORY.md").is_file()
        if not has_index:
            results.append(("structure", "WARN", "ai_memory/ present but no MEMORY.md index"))
        elif not notes:
            results.append(("structure", "WARN", "ai_memory/ present, 0 module notes yet (run /airx:memory)"))
        else:
            extra = f"; optional layers: {', '.join(opt)}" if opt else ""
            results.append(("structure", "PASS", f"{len(notes)} memory note(s){extra}"))

    # frontmatter on memory notes
    bad = [p.name for p in notes if not REQUIRED_MEMORY_KEYS.issubset(frontmatter_keys(p))]
    if notes:
        if bad:
            results.append(("frontmatter", "WARN", f"{len(bad)} note(s) missing keys (e.g. {bad[0]})"))
        else:
            results.append(("frontmatter", "PASS", f"{len(notes)} note(s) valid"))

    # freshness
    cr = man.get("code_ref", "TBD")
    if cr and cr != "TBD":
        hr = head_ref(wiki, man.get("repo_path"))
        if hr not in ("unknown",) and hr != cr:
            results.append(("freshness", "WARN", f"verified at {cr}; HEAD {hr} — re-verify/curate"))
        else:
            results.append(("freshness", "PASS", f"code_ref {cr}"))

    # citations + drift - mechanical verification (symbol-aware; see verify-citations.py):
    #   citations = file:line anti-hallucination gate (dangling → FAIL, per conformance-spec §3)
    #   drift     = symbol resolution rate (class/query/bean still in code) — the memory-vs-code signal
    if notes:
        try:
            import importlib.util
            _p = Path(__file__).resolve().parent / "verify-citations.py"
            _spec = importlib.util.spec_from_file_location("airx_vc", _p)
            _vc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_vc)
            cite = _vc.check_wiki(wiki)
            if not cite.get("error"):
                fl_t, fl_r = cite["total"], cite["resolved"]
                dangling = [p for p in cite["problems"] if "dangling" in p]
                if fl_t:
                    if dangling:
                        results.append(("citations", "FAIL",
                                        f"{fl_r}/{fl_t} file:line resolve; dangling (e.g. {dangling[0]})"))
                        fail = True
                    elif cite["problems"]:
                        results.append(("citations", "WARN",
                                        f"{fl_r}/{fl_t} file:line resolve; {len(cite['problems'])} ambiguous"))
                    else:
                        results.append(("citations", "PASS", f"{fl_r}/{fl_t} file:line resolve"))
                st = sum(v["total"] for v in cite["sym"].values())
                sr = sum(v["resolved"] for v in cite["sym"].values())
                if st:
                    rate = sr / st * 100
                    grade = "PASS" if rate >= 90 else "WARN"
                    results.append(("drift", grade,
                                    f"{sr}/{st} symbols resolve ({rate:.0f}%); "
                                    f"{st - sr} renamed/missing to review"))
        except Exception:
            pass

    # report
    print(f"AIRX CHECK  {wiki.name}  (memory-first)")
    w = max(len(d) for d, _, _ in results)
    for d, s, det in results:
        print(f"  {d.ljust(w)}  {s:4}  {det}")
    overall = "FAIL" if fail else ("WARN" if any(s == "WARN" for _, s, _ in results) else "PASS")
    print(f"  {'OVERALL'.ljust(w)}  {overall}")
    print("\n  note: conformance PASS is necessary, not sufficient — prove the win with /airx:benchmark.")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
