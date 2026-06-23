#!/usr/bin/env python3
"""Test the codemap whole-repo MAP + coverage ledger (Phase 2).

Pins: init auto-populates the index-first map in MEMORY.md; the map ranks areas + lists key types;
the coverage ledger flips when a note is authored; codemap is idempotent (one map block) and preserves
the human-curated Spine outside the markers.

Hermetic tempdir + git fixture, tools invoked via subprocess. Stdlib only."""
from __future__ import annotations

import subprocess
import sys
import tempfile
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


def git(repo: Path, *args):
    subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        repo = Path(td) / "repo"
        (repo / "src/main/java/billing").mkdir(parents=True)
        (repo / "src/main/java/orders").mkdir(parents=True)
        (repo / "src/main/java/billing/BillingService.java").write_text(
            "package billing;\npublic class BillingService {}\nclass InvoiceCalc {}\n")
        (repo / "src/main/java/orders/OrderService.java").write_text(
            "package orders;\npublic class OrderService {}\n")
        git(repo, "init")
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@e.st", "-c", "user.name=t", "commit", "-m", "init")

        r = run("init.py", "--repo", str(repo))
        check(r.returncode == 0, "init.py exits 0")
        mem_index = repo / ".airx" / "ai_memory" / "MEMORY.md"
        txt = mem_index.read_text() if mem_index.is_file() else ""
        check("airx:map:begin" in txt, "init auto-populated the codebase map")
        check("billing" in txt and "orders" in txt, "map lists both areas")
        check("`BillingService`" in txt, "map lists key declared types")
        check("Coverage:** 0/2" in txt, "ledger shows 0/2 before any note")

        # author a note for billing, refresh the map
        (repo / ".airx" / "ai_memory" / "reference_billing.md").write_text(
            "---\nname: Billing\nstatus: LIVING\n---\n# Billing\n`BillingService` — BillingService.java:2.\n")
        r = run("codemap.py", str(repo))
        check(r.returncode == 0, "codemap.py exits 0")
        txt = mem_index.read_text()
        check("Coverage:** 1/2" in txt, "ledger flips to 1/2 after authoring a note")
        check("reference_billing.md` ✓" in txt, "covered area is marked in the map")
        check("/airx:memory orders" in txt, "NEXT points at the remaining uncovered area")
        check(txt.count("airx:map:begin") == 1, "codemap is idempotent (one map block)")

        # human-curated Spine outside the markers is preserved across regeneration
        check("## Spine" in txt, "the human-curated Spine is preserved")

    if FAILS:
        print(f"\nFAILED ({len(FAILS)}): " + "; ".join(FAILS))
        return 1
    print("\ncodemap: map + ledger + idempotency all pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
