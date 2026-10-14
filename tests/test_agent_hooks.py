#!/usr/bin/env python3
"""Test the agent-facing hooks under the `.airx/` layout.

Pins: hooks.json points only at files that exist; SessionStart puts the router + stale notes in the
agent's context (stdout), in-repo and sibling, and stays silent outside airx; post-edit returns
`additionalContext` for a memory note with dangling citations and nothing for clean notes, drafts, or code;
post-commit.sh finds an `.airx/` wiki, scans code commits, and skips memory-only commits (no loop).

Hermetic tempdir + git fixture; tools via subprocess. Stdlib only."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
FAILS: list[str] = []


def check(cond: bool, name: str):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}")
    if not cond:
        FAILS.append(name)


def run(tool: str, *args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / tool), *args],
                          capture_output=True, text=True, timeout=180)


def hook(event: str, payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(TOOLS / "agent_hooks.py"), event],
                          input=json.dumps(payload), capture_output=True, text=True, timeout=60)


def git(repo: Path, *args) -> str:
    return subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@e.st", "-c", "user.name=t", *args],
                          capture_output=True, text=True).stdout.strip()


def make_repo(path: Path) -> Path:
    (path / "src/main/java/billing").mkdir(parents=True)
    (path / "src/main/java/billing/BillingService.java").write_text(
        "package billing;\npublic class BillingService {\n  public int applyTax(int a){return a;}\n}\n")
    git(path, "init", "-q")
    git(path, "add", "-A")
    git(path, "commit", "-qm", "init")
    return path


def main() -> int:
    # hooks.json references only real plugin files
    cfg = json.loads((ROOT / "hooks/hooks.json").read_text())
    cmds = [h["command"] for ev in cfg["hooks"].values() for m in ev for h in m["hooks"]]
    paths = [re.search(r'"\$\{CLAUDE_PLUGIN_ROOT\}"(/\S+)', c).group(1) for c in cmds]
    check(all((ROOT / p.lstrip("/")).is_file() for p in paths), "hooks.json commands point at existing files")
    check("SessionStart" in cfg["hooks"], "SessionStart hook registered")

    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        td = Path(td)
        plain = make_repo(td / "plain")
        r = hook("session-start", {"cwd": str(plain)})
        check(r.returncode == 0 and r.stdout == "", "session-start: silent no-op outside airx")

        # ---- in-repo layout
        repo = make_repo(td / "repo")
        run("init.py", "--repo", str(repo))
        git(repo, "add", "-A"); git(repo, "commit", "-qm", "airx init")
        mem = repo / ".airx" / "ai_memory"
        check((repo / ".airx" / ".ai-readiness.yml").is_file(), "fixture: manifest under .airx/")
        r = hook("session-start", {"cwd": str(repo / "src")})
        check(".airx/ai_memory/MEMORY.md" in r.stdout, "session-start: router path in context (from a subdir)")
        check("Notes: 0" in r.stdout, "session-start: reports zero notes")

        head = git(repo, "rev-parse", "--short", "HEAD")
        note = mem / "reference_billing.md"
        note.write_text(f"---\nname: Billing\ncode_ref: {head}\nstatus: LIVING\n---\n# Billing\n"
                        "`BillingService.applyTax` — src/main/java/billing/BillingService.java:3.\n")
        r = hook("post-edit", {"cwd": str(repo), "tool_name": "Write", "tool_input": {"file_path": str(note)}})
        check(r.returncode == 0 and r.stdout == "", "post-edit: clean note → no context")

        bad = mem / "reference_ghost.md"
        bad.write_text("---\nname: Ghost\n---\n`GhostService.haunt` lives at "
                       "src/main/java/billing/BillingService.java:999.\n")
        r = hook("post-edit", {"cwd": str(repo), "tool_name": "Edit",
                               "tool_input": {"file_path": ".airx/ai_memory/reference_ghost.md"}})
        try:
            ctx = json.loads(r.stdout)["hookSpecificOutput"]
        except Exception:
            ctx = {}
        check(ctx.get("hookEventName") == "PostToolUse", "post-edit: emits PostToolUse JSON for a bad note")
        add = ctx.get("additionalContext", "")
        check("DANGLING" in add and "BillingService.java:999" in add, "post-edit: names the dangling file:line")
        check("GhostService" in add, "post-edit: names the unresolved symbol")
        bad.unlink()

        draft = mem / "_draft_ghost.md"
        draft.write_text("`GhostService` BillingService.java:999\n")
        r = hook("post-edit", {"cwd": str(repo), "tool_input": {"file_path": str(draft)}})
        check(r.stdout == "", "post-edit: ignores _draft_ scaffolding")
        r = hook("post-edit", {"cwd": str(repo), "tool_input": {
            "file_path": str(repo / "src/main/java/billing/BillingService.java")}})
        check(r.stdout == "", "post-edit: ignores code edits")
        draft.unlink()

        # a class written but not yet committed: the HEAD-keyed index cache must not call it unresolved
        new = repo / "src/main/java/billing/NewService.java"
        new.write_text("package billing;\npublic class NewService {}\n")
        wip = mem / "reference_wip.md"
        wip.write_text("---\nname: Wip\n---\n`NewService` handles the new flow.\n")
        r = hook("post-edit", {"cwd": str(repo), "tool_input": {"file_path": str(wip)}})
        check(r.stdout == "", "post-edit: resolves a class in an uncommitted file (cache overlay)")
        new.unlink(); wip.unlink()

        # code moves in an UNRELATED module → billing note is not flagged
        (repo / "src/main/java/orders").mkdir()
        (repo / "src/main/java/orders/Order.java").write_text("package orders;\npublic class Order {}\n")
        git(repo, "add", "src"); git(repo, "commit", "-qm", "add Order")
        r = hook("session-start", {"cwd": str(repo)})
        check("Code changed under" not in r.stdout, "session-start: unrelated-module commit doesn't flag the note")

        # code moves → note is behind HEAD
        (repo / "src/main/java/billing/Tax.java").write_text("package billing;\npublic class Tax {}\n")
        git(repo, "add", "src"); git(repo, "commit", "-qm", "add Tax")
        r = hook("session-start", {"cwd": str(repo)})
        check("Code changed under 1 note(s)" in r.stdout and "reference_billing (1 file)" in r.stdout,
              "session-start: flags the note whose module changed")

        # ---- post-commit.sh against the .airx layout
        pc = ["bash", str(ROOT / "hooks/post-commit.sh")]
        r = subprocess.run(pc, cwd=repo, capture_output=True, text=True, timeout=30)
        check("scanning commit" in r.stderr, "post-commit: code commit triggers the background scan")
        pending = mem / "PENDING-ENHANCEMENTS.md"
        for _ in range(100):
            if pending.is_file():
                break
            time.sleep(0.2)
        check(pending.is_file(), "post-commit: scan wrote .airx/ai_memory/PENDING-ENHANCEMENTS.md")
        time.sleep(1)                          # let the rest of the background scan settle
        note.write_text(note.read_text() + "Tax lives in `Tax`.\n")
        git(repo, "add", ".airx"); git(repo, "commit", "-qm", "memory only")
        names = git(repo, "diff", "--name-only", "HEAD~1..HEAD").splitlines()
        check(bool(names) and all(n.startswith(".airx/") for n in names), "fixture: last commit touched memory only")
        r = subprocess.run(pc, cwd=repo, capture_output=True, text=True, timeout=30)
        check("scanning commit" not in r.stderr, "post-commit: .airx/-only commit is skipped (no loop)")

        # ---- sibling layout
        sib = make_repo(td / "svc")
        run("init.py", "--repo", str(sib), "--layout", "sibling")
        r = hook("session-start", {"cwd": str(sib)})
        check("svc-wiki" in r.stdout and "MEMORY.md" in r.stdout, "session-start: finds a sibling <repo>-wiki")

    if FAILS:
        print(f"\nFAILED ({len(FAILS)}): " + "; ".join(FAILS))
        return 1
    print("\nagent hooks: SessionStart context + note verify-on-write + post-commit (.airx) pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
