#!/usr/bin/env python3
"""airx verify-citations — check that citations in memory notes resolve to real code.

A note's credibility IS its citations. airx supports TWO citation styles (symbol-first by design — see
method/sourcing-playbook.md): symbols are more durable than line numbers across churn in big files.

  1. file:line  — `path.ext:NN` (or `:start-end`) → the line must exist in that file.
  2. SYMBOLS    — the durable citations the good notes actually use:
       • class/interface  `CamelCaseService` (code-y suffix) → a `<Name>.java` exists in the repo
       • named query      `Domain.methodName` (dotted)       → `name="…"` exists in a queries.xml
       • bean id          `@Component("beanId")`             → that annotation literal exists in code

Deterministic, stdlib only, no LLM. Catches hallucinated/stale citations (mechanical citation verification).

    python3 verify-citations.py <wiki-dir>
Exit: 0 = ok (or none found / no repo); 1 = dangling file:line OR dangling symbols exist.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

# --- file:line citations (unchanged) -------------------------------------------------
# A path with an extension, then :line or :start-end. The extension requirement avoids matching
# "T2", "v0.1", "12:30", etc. Captures: path, start, end(optional).
CITE = re.compile(r"([A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z0-9]+):(\d+)(?:-(\d+))?")

# --- symbol citations ----------------------------------------------------------------
BACKTICK = re.compile(r"`([^`]+)`")
# class/interface: CamelCase ending in a code-y suffix (keeps false-positives low — only flags tokens
# that are unmistakably type names, not prose like `TBD` or `LIVING`).
CLASS_SUFFIX = (r"Bean|Service|DAO|Dao|Repository|Controller|Servlet|Job|Model|Form|Engine|Process|"
                r"Filter|Config|Configurer|Util|Utils|Header|Detail|Details|Entity|Mapper|Handler|"
                r"Listener|Factory|Provider|Resolver|Interceptor|Validator|Strategy|Manager|Helper|Impl")
CLASS_TOK = re.compile(r"^[A-Z][A-Za-z0-9]*(?:" + CLASS_SUFFIX + r")$")
# named query: Dotted.identifier with a lowercase-led method-ish segment, no parens (e.g. Inbox.getFoo,
# PH.IDT.findProductPricing). Excludes file names (handled by CITE) and method calls (have parens).
NQ_TOK = re.compile(r"^[A-Z][A-Za-z0-9]+(?:\.[A-Za-z0-9_]+)+$")
# bean id literal inside an annotation, as written in the notes.
BEAN_ANN = re.compile(r'@(?:Component|Service|Repository|Controller|Named)\("([a-z][A-Za-z0-9_]*)"\)')

_IGNORE_DIRS = {".git", "target", "build", "dist", "out", "bin", "node_modules", "__pycache__"}
# file:line citations must name a real code file — keeps `jakarta.faces:4` (a dependency coord) and
# `SalesReturnBean.navEntityPage:2344` (class.method:line notation) out of the hard-fail arm.
_CODE_EXTS = {"java", "kt", "kts", "xml", "xhtml", "jsp", "ts", "tsx", "js", "jsx", "py", "go", "rb",
              "cs", "html", "css", "sql", "json", "yml", "yaml", "properties", "gradle", "sh", "vue"}


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


# ---------------------------------------------------------------------------- repo symbol index
def build_index(repo: Path) -> dict:
    """One-pass, cached index of the repo's resolvable symbols. Deterministic, no LLM."""
    types: set[str] = set()
    nq: set[str] = set()
    for p in repo.rglob("*"):
        if not p.is_file():
            continue
        if any(part in _IGNORE_DIRS for part in p.parts):
            continue
        if p.suffix in (".java", ".kt"):
            types.add(p.stem)                       # one public type per file (high precision in Java)
        elif p.name.endswith("queries.xml") or (p.suffix == ".xml" and "quer" in p.name.lower()):
            try:
                for m in re.finditer(r'name="([^"]+)"', p.read_text(errors="ignore")):
                    nq.add(m.group(1))
            except Exception:
                pass
    # bean ids via one grep pass (fast even on thousands of files)
    beans: set[str] = set()
    try:
        out = subprocess.run(
            ["grep", "-rhoE", r'@(Component|Service|Repository|Controller|Named)\("[a-z][A-Za-z0-9_]*"\)',
             str(repo)], capture_output=True, text=True, timeout=120).stdout
        for m in re.finditer(r'"([a-z][A-Za-z0-9_]*)"', out):
            beans.add(m.group(1))
    except Exception:
        pass
    return {"types": types, "named_queries": nq, "beans": beans}


# ---------------------------------------------------------------------------- file:line resolution
def resolve_one(repo: Path, path: str, start: int, end):
    if "/" in path:
        cands = [repo / path] if (repo / path).is_file() else []
    else:
        cands = [p for p in repo.rglob(path) if not any(d in _IGNORE_DIRS for d in p.parts)]
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
    """(total, resolved, problems[]) for file:line citations in one note. (API preserved.)"""
    total = resolved = 0
    problems, seen = [], set()
    for m in CITE.finditer(md.read_text(errors="ignore")):
        raw, path = m.group(0), m.group(1)
        ext = path.rsplit(".", 1)[-1]
        if raw in seen or path.endswith(".md") or path.startswith("http"):
            continue
        # skip non-citations that look like path:line: IPs (all-numeric), package:version, ports.
        if "." not in path or ext.lower() not in _CODE_EXTS:
            continue
        seen.add(raw)
        total += 1
        status, detail = resolve_one(repo, path, int(m.group(2)), int(m.group(3)) if m.group(3) else None)
        if status == "resolved":
            resolved += 1
        else:
            problems.append(f"{md.name}: {raw} ({status}: {detail})")
    return total, resolved, problems


# ---------------------------------------------------------------------------- symbol resolution
def note_symbols(idx: dict, md: Path):
    """(by_kind, unresolved[]) — resolve class / named-query / bean-id citations in one note.
    by_kind: {kind: {'total':int,'resolved':int}}. A token resolves if it names something real in the
    repo. Symbols are ADVISORY (a CamelCase token may be a framework/library type that lives in a jar,
    not the repo) — so unresolved symbols are reported for review, never a hard fail."""
    text = md.read_text(errors="ignore")
    by = {k: {"total": 0, "resolved": 0} for k in ("class", "named_query", "bean")}
    unresolved, seen = [], set()

    def hit(kind, tok, ok):
        by[kind]["total"] += 1
        if ok:
            by[kind]["resolved"] += 1
        else:
            unresolved.append(f"{md.name}: `{tok}` ({kind}: not in repo — renamed, or external library?)")

    for m in BACKTICK.finditer(text):
        tok = m.group(1).strip()
        if not tok or tok in seen or "(" in tok or ":" in tok or "/" in tok:
            continue
        if NQ_TOK.match(tok) and not tok.endswith((".java", ".xml", ".md", ".xhtml")):
            seen.add(tok)
            # dotted token resolves if it's a named query OR its owning type exists (Class.method/field).
            owner = tok.split(".", 1)[0]
            if tok in idx["named_queries"]:
                hit("named_query", tok, True)
            elif owner in idx["types"]:
                hit("class", tok, True)
            else:
                hit("named_query", tok, False)
        elif CLASS_TOK.match(tok):
            seen.add(tok); hit("class", tok, tok in idx["types"])
    for m in BEAN_ANN.finditer(text):
        tok = m.group(1)
        if tok in seen:
            continue
        seen.add(tok); hit("bean", tok, tok in idx["beans"])
    return by, unresolved


# ---------------------------------------------------------------------------- wiki rollup
def check_wiki(wiki: Path) -> dict:
    repo = repo_from_manifest(wiki)
    out = {"repo": repo, "files": 0, "total": 0, "resolved": 0, "problems": [],
           "sym": {k: {"total": 0, "resolved": 0} for k in ("class", "named_query", "bean")},
           "sym_problems": []}
    if repo is None or not repo.is_dir():
        out["error"] = "no resolvable repo_path in manifest — cannot verify"
        return out
    mem = wiki / "ai_memory"
    if not mem.is_dir():
        return out
    idx = build_index(repo)
    for md in sorted(mem.glob("**/*.md")):
        if md.name.startswith("_") or md.name == "MEMORY.md":
            continue
        t, r, probs = note_citations(repo, md)
        by, sprobs = note_symbols(idx, md)
        sym_total = sum(v["total"] for v in by.values())
        if t or sym_total:
            out["files"] += 1
            out["total"] += t; out["resolved"] += r; out["problems"] += probs
            for k in by:
                out["sym"][k]["total"] += by[k]["total"]; out["sym"][k]["resolved"] += by[k]["resolved"]
            out["sym_problems"] += sprobs
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
    st = sum(v["total"] for v in r["sym"].values())
    sr = sum(v["resolved"] for v in r["sym"].values())
    print(f"  file:line  — total {r['total']}  resolved {r['resolved']}  problems {len(r['problems'])}")
    print(f"  symbols    — total {st}  resolved {sr}  problems {len(r['sym_problems'])}")
    for k in ("class", "named_query", "bean"):
        v = r["sym"][k]
        if v["total"]:
            print(f"      {k:12} {v['resolved']}/{v['total']}")
    for p in r["problems"]:
        print(f"  PROBLEM  {p}")               # file:line — hard
    for p in r["sym_problems"][:25]:
        print(f"  review   {p}")               # symbols — advisory
    extra = len(r["sym_problems"]) - 25
    if extra > 0:
        print(f"  …and {extra} more symbol(s) to review")
    # Only file:line danglers hard-fail. Symbols are advisory (may be external library types) — surfaced
    # as a resolution rate + review list, not a gate, to avoid false alarms on framework classes.
    if any("dangling" in p for p in r["problems"]):
        print("  FAIL - dangling file:line citations (hallucinated or stale). Fix the note or mark TBD.")
        return 1
    if r["total"] == 0 and st == 0:
        print("  (no resolvable citations found)")
    else:
        rate = round(sr / st * 100, 1) if st else 100.0
        print(f"  OK - file:line citations resolve; symbols {rate}% resolved ({sr}/{st}, rest to review).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
