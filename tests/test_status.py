#!/usr/bin/env python3
"""Test the status dashboard (Phase 3.1).

Pins: init writes an initial .airx/STATUS.md; status reports memory coverage + trust + a NEXT action;
coverage and NEXT update as notes are authored; layers are memory-first (KB/docs/view only if present).

Hermetic tempdir + git fixture; tool via subprocess. Stdlib only."""
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
            "package billing;\nimport org.springframework.stereotype.Service;\n"
            '@Service("billingService")\npublic class BillingService { public int applyTax(int a){return a;} }\n')
        (repo / "src/main/java/orders/OrderService.java").write_text(
            "package orders;\npublic class OrderService {}\n")
        git(repo, "init")
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@e.st", "-c", "user.name=t", "commit", "-m", "init")

        run("init.py", "--repo", str(repo))
        status_md = repo / ".airx" / "STATUS.md"
        check(status_md.is_file(), "init wrote .airx/STATUS.md")

        r = run("status.py", str(repo))
        check(r.returncode == 0, "status.py exits 0")
        out = r.stdout
        check("Layers:" in out and "memory" in out, "reports layers (memory-first)")
        check("Memory coverage:" in out and "0/2" in out, "coverage 0/2 before any note")
        check("kb" not in out.split("Layers:")[1].split("\n")[0], "KB not shown when absent (memory-first)")
        check("/airx:memory billing" in out, "NEXT points at the hottest module")

        # author a note → coverage + NEXT update
        (repo / ".airx" / "ai_memory" / "reference_billing.md").write_text(
            "---\nname: Billing\nstatus: LIVING\n---\n# Billing\n"
            "`BillingService` via `BillingService.applyTax` — BillingService.java:4.\n")
        out2 = run("status.py", str(repo)).stdout
        check("1/2" in out2, "coverage rises to 1/2 after a note")
        check("citations resolve" in out2, "reports trust (citation resolution)")
        check("/airx:memory orders" in out2, "NEXT advances to the next uncovered module")

    if FAILS:
        print(f"\nFAILED ({len(FAILS)}): " + "; ".join(FAILS))
        return 1
    print("\nstatus: dashboard + coverage/NEXT progression pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
