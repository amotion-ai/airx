#!/usr/bin/env python3
"""airx agent hooks — put memory state IN the agent's context (Claude Code hook entry points).

Two events, both read the hook's JSON from stdin and are safe no-ops outside an airx repo:

  session-start  SessionStart → plain stdout becomes agent context. A few terse lines: where the router
                 is, how many notes exist, which notes have code changes under them, and any pending worklist.
                 Cheap on purpose (no citation scan, no churn ranking) — `/airx:status` is the full readout.
  post-edit      PostToolUse(Write|Edit) → when the agent writes a memory NOTE, verify that note's
                 citations at once and hand back `additionalContext` naming what doesn't resolve, so
                 cite-or-TBD is enforced while writing, not at the next `/airx:check`.

Why not stderr: Claude Code never shows the model stderr from a hook that exits 0 — the old freshness
warning was invisible to the agent. Stdlib only, no LLM. Always exits 0 (advisory, never blocks).

    python3 agent_hooks.py session-start|post-edit   < hook-input.json
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import airxpaths as ap

MAX_NOTES = 60          # freshness scan cap — keeps SessionStart fast on big wikis
MAX_REPORT = 8          # unresolved citations listed back to the agent per edit


def _vc():
    spec = importlib.util.spec_from_file_location("airx_vc", HERE / "verify-citations.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def _git(repo: Path, *args) -> str:
    try:
        return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:
        return ""


def _stdin() -> dict:
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def find_wiki(start: Path) -> Path | None:
    """The airx wiki for a working dir: in-repo (`.airx/` or legacy root manifest), else the sibling
    `<repo>-wiki/`. Starts from the git toplevel so a session opened in a subdirectory still resolves."""
    top = _git(start, "rev-parse", "--show-toplevel")
    root = Path(top).resolve() if top else start
    for cand in (root, root.parent / f"{root.name}-wiki"):
        if ap.is_wiki(cand):
            return cand
    return None


def wiki_for_note(path: Path) -> Path | None:
    """Walk up from a written file to the wiki that owns it (the dir whose manifest resolves). `.airx/`
    itself is skipped: its manifest would pass the legacy root check and mis-resolve `repo_path`."""
    for d in path.parents:
        if d.name != ".airx" and ap.is_wiki(d):
            return d
    return None


FM_REF = re.compile(r"^code_ref:\s*([0-9a-fA-F]{6,40})\s*$", re.M)
PREFIXES = ("reference_", "project_")


def notes(wiki: Path, vc) -> list[Path]:
    mem = ap.memory(wiki)
    if not mem.is_dir():
        return []
    return sorted(p for p in mem.glob("*.md")
                  if not p.name.startswith("_") and p.name not in vc.NON_NOTES)


def changed_under(repo: Path, note: Path, vc, memo: dict) -> int:
    """How many files changed since the note's `code_ref` that belong to the note: under a directory named
    for its module, or a file it cites. Commit count alone flags every note in an active repo, which
    would teach the agent to distrust all of memory. 0 when the note has no `code_ref`."""
    text = note.read_text(errors="ignore")
    m = FM_REF.search(text[:2000])
    if not m:
        return 0
    ref = m.group(1)
    if ref not in memo:                          # one diff per distinct code_ref
        out = _git(repo, "diff", "--name-only", f"{ref}..HEAD")
        memo[ref] = [f for f in out.splitlines() if f and not f.startswith((".airx/", "ai_memory/"))]
    stem = note.stem
    module = next((stem[len(p):] for p in PREFIXES if stem.startswith(p)), stem).lower().replace("-", "_")
    cited = {c.group(1) for c in vc.CITE.finditer(text)}
    hits = 0
    for f in memo[ref]:
        dirs = {d.lower().replace("-", "_") for d in f.split("/")[:-1]}
        if module in dirs or any(f == c or f.endswith("/" + c) for c in cited):
            hits += 1
    return hits


def overlay_worktree(repo: Path, idx: dict, vc) -> None:
    """The symbol index is cached per HEAD. Add what's declared in modified/untracked files, so a note
    citing a class the agent just wrote (not yet committed) isn't reported as unresolved."""
    out = _git(repo, "ls-files", "--modified", "--others", "--exclude-standard")
    for f in out.splitlines():
        p = repo / f
        if f.startswith(".airx/") or not p.is_file():
            continue
        if p.suffix in (".java", ".kt"):
            text = p.read_text(errors="ignore")
            for d in vc.DECL.finditer(text):
                idx["types"].add(d.group(1))
                tf = idx["type_files"].setdefault(d.group(1), [])
                tf.add(str(p)) if isinstance(tf, set) else tf.append(str(p))
            idx["beans"].update(b.group(1) for b in vc.BEAN_ANN.finditer(text))
        elif p.suffix == ".xml" and "quer" in p.name.lower():
            idx["named_queries"].update(re.findall(r'name="([^"]+)"', p.read_text(errors="ignore")))


def session_start(payload: dict) -> int:
    start = Path(payload.get("cwd") or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()).resolve()
    wiki = find_wiki(start)
    if wiki is None:
        return 0
    vc = _vc()
    mem = ap.memory(wiki)
    repo = vc.repo_from_manifest(wiki) or wiki
    router = mem / "MEMORY.md"
    ns = notes(wiki, vc)
    rel = lambda p: os.path.relpath(p, start)

    lines = ["airx project memory is active for this repo."]
    if router.is_file():
        lines.append(f"- Router: `{rel(router)}` — for a non-trivial or cross-module task, read it, then the "
                     "ONE matching note, before grepping. Skip memory for one-hop greppable lookups.")
    lines.append(f"- Notes: {len(ns)} authored." + ("" if ns else " Next: `/airx:memory` (or `/airx:status`)."))

    memo: dict = {}
    stale = sorted(((n, p.stem) for p in ns[:MAX_NOTES] if (n := changed_under(repo, p, vc, memo))),
                   reverse=True)
    if stale:
        top = ", ".join(f"{s} ({n} file{'s' * (n > 1)})" for n, s in stale[:3])
        lines.append(f"- Code changed under {len(stale)} note(s) since they were verified: {top}. Re-check "
                     "those claims against code before acting on them; `/airx:update <module>` if wrong.")

    pend = mem / "PENDING-ENHANCEMENTS.md"
    if pend.is_file():
        items = sum(1 for ln in pend.read_text(errors="ignore").splitlines() if ln.lstrip().startswith("- "))
        if items:
            lines.append(f"- Pending: {items} drift/enhancement item(s) in `{rel(pend)}` → `/airx:enhance`.")
    lines.append("- Rule: every claim you write into memory cites `file:line` or a symbol, or says "
                 "`TBD — needs human input`.")
    print("\n".join(lines))
    return 0


def post_edit(payload: dict) -> int:
    fp = (payload.get("tool_input") or {}).get("file_path")
    if not fp:
        return 0
    path = Path(fp)
    if not path.is_absolute():
        path = Path(payload.get("cwd") or os.getcwd()) / path
    if (path.suffix != ".md" or "ai_memory" not in path.parts or path.name.startswith("_")
            or ".cache" in path.parts or not path.is_file()):
        return 0                                 # cheap exit first: this runs on every Write/Edit
    vc = _vc()
    if path.name in vc.NON_NOTES:
        return 0
    wiki = wiki_for_note(path)
    repo = vc.repo_from_manifest(wiki) if wiki else None
    if repo is None or not repo.is_dir():
        return 0
    _, _, probs = vc.note_citations(repo, path)
    idx = vc.build_index(repo, cache_dir=ap.memory(wiki) / ".cache")
    overlay_worktree(repo, idx, vc)
    _, sprobs = vc.note_symbols(idx, path)
    if not (probs or sprobs):
        return 0
    msg = [f"airx: {path.name} has citations that don't resolve against the code."]
    msg += [f"  - DANGLING {p}" for p in probs[:MAX_REPORT]]
    msg += [f"  - unresolved symbol {p}" for p in sprobs[:max(0, MAX_REPORT - len(probs))]]
    more = len(probs) + len(sprobs) - MAX_REPORT
    if more > 0:
        msg.append(f"  - …and {more} more (run verify-citations for the full list)")
    msg.append("Fix each: cite the real file:line or symbol, or rewrite the claim as `TBD — needs human input`. "
               "Dangling file:line fails /airx:check; an unresolved symbol is fine only if it's a library type.")
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                             "additionalContext": "\n".join(msg)}}))
    return 0


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in ("session-start", "post-edit"):
        print("usage: agent_hooks.py session-start|post-edit  < hook-input.json", file=sys.stderr)
        return 2
    payload = _stdin()
    try:
        return session_start(payload) if sys.argv[1] == "session-start" else post_edit(payload)
    except Exception as e:                       # a hook must never break the session
        print(f"airx hook error: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
