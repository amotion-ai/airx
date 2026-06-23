#!/usr/bin/env python3
"""Test the per-area completeness gauge (Phase 2.5).

Pins: completeness reports which of an area's declared symbols (classes / public methods / named queries)
a note covers, names the MISSING ones, and reaches 100% once they're all mentioned. This is the
measurable answer to "is the note thorough?" — measure-don't-assume for note depth.

Hermetic tempdir + git fixture; tool invoked via subprocess. Stdlib only."""
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
        (repo / "src/main/java/orders").mkdir(parents=True)   # 2nd package so module detection resolves
        (repo / "src/main/java/billing/BillingService.java").write_text(
            "package billing;\nimport org.springframework.stereotype.Service;\n"
            '@Service("billingService")\npublic class BillingService {\n'
            "  public int applyTax(int amt) { return amt; }\n"
            "  public int refund(int amt) { return amt; }\n}\n")
        (repo / "src/main/java/billing/InvoiceCalc.java").write_text(
            "package billing;\nimport org.springframework.stereotype.Component;\n"
            "@Component\npublic class InvoiceCalc { public int total(int a){return a;} }\n")
        (repo / "src/main/java/orders/OrderService.java").write_text(
            "package orders;\npublic class OrderService {}\n")
        git(repo, "init")
        git(repo, "add", "-A")
        git(repo, "-c", "user.email=t@e.st", "-c", "user.name=t", "commit", "-m", "init")
        run("init.py", "--repo", str(repo))
        note = repo / ".airx" / "ai_memory" / "reference_billing.md"

        # partial note: covers BillingService + applyTax, misses refund + InvoiceCalc
        note.write_text("---\nname: Billing\nstatus: LIVING\n---\n# Billing\n"
                        "`BillingService` computes tax via `BillingService.applyTax` — BillingService.java:5.\n")
        r = run("completeness.py", str(repo), "billing")
        check(r.returncode == 0, "completeness.py exits 0")
        out = r.stdout
        check("GAP" in out, "partial note is flagged with a GAP")
        check("InvoiceCalc" in out and "refund" in out, "missing symbols are named (InvoiceCalc, refund)")
        check("completeness 50%" in out, "partial note scores 50%")

        # full note: mentions every declared symbol → 100%
        note.write_text("---\nname: Billing\nstatus: LIVING\n---\n# Billing\n"
                        "`BillingService` — BillingService.java:4. Methods `applyTax`, `refund`. "
                        "Helper `InvoiceCalc` with `total`.\n")
        out2 = run("completeness.py", str(repo), "billing").stdout
        check("completeness 100%" in out2, "full note reaches 100% completeness")
        check("GAP" not in out2, "full note has no gaps")

    if FAILS:
        print(f"\nFAILED ({len(FAILS)}): " + "; ".join(FAILS))
        return 1
    print("\ncompleteness: gap detection + 100% coverage pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
