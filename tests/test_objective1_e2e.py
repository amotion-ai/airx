#!/usr/bin/env python3
"""End-to-end test for the Objective-1 flow: a memory-only user can LIST modules, author a note, and
PROVE impact — without ever growing an ai_knowledge_base/ folder.

Pins the behaviour added for the "stuck after init" beta feedback:
  • modules.py lists churn-ranked modules (the gap: /airx:memory asked "which?" blind),
  • benchmark_init.py scaffolds ai_memory/benchmark.json from a note's resolved citations,
  • benchmark.py then reports a real memory token win, writing to ai_memory/.cache/ (NOT
    ai_knowledge_base/), with accuracy "-" until expect is filled (no vanity yes),
  • evidence.py reads that result from the new location.

Hermetic: builds a throwaway git repo + airx wiki in a tempdir. Invokes tools via subprocess (the exact
`python3 tools/X.py` path the commands use). Stdlib only."""
from __future__ import annotations

import json
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


def build_repo(root: Path) -> Path:
    repo = root / "repo"
    (repo / "src/main/java/billing").mkdir(parents=True)
    (repo / "src/main/java/orders").mkdir(parents=True)
    (repo / "src/main/java/billing/BillingService.java").write_text(
        "package billing;\n"
        "import org.springframework.stereotype.Service;\n"
        '@Service("billingService")\n'
        "public class BillingService {\n"
        "  public int applyTax(int amt) { return amt; }\n"
        "}\n")
    (repo / "src/main/java/orders/OrderService.java").write_text(
        "package orders;\npublic class OrderService {}\n")
    git(repo, "init")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=t@e.st", "-c", "user.name=t", "commit", "-m", "init")
    return repo


NOTE = """\
---
name: Billing — Developer Reference
status: LIVING
---
# Billing
The `BillingService` bean computes charges via `BillingService.applyTax` — BillingService.java:5.
"""


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        repo = build_repo(root)

        # 1) init stamps the memory layer
        r = run("init.py", "--repo", str(repo))
        check(r.returncode == 0, "init.py exits 0")
        check((repo / ".airx" / "ai_memory" / "MEMORY.md").is_file(), "init created ai_memory/MEMORY.md")

        # 2) modules.py lists churn-ranked modules (the 'which module?' fix)
        r = run("modules.py", str(repo))
        check(r.returncode == 0, "modules.py exits 0")
        check("AIRX MODULES" in r.stdout, "modules.py prints the ranked list header")
        check("billing" in r.stdout and "orders" in r.stdout, "modules.py lists both modules")
        check("/airx:memory" in r.stdout, "modules.py suggests a NEXT module")

        # author one verified note
        (repo / ".airx" / "ai_memory" / "reference_billing.md").write_text(NOTE)

        # modules.py now marks billing covered
        r = run("modules.py", str(repo))
        check("note ✓" in r.stdout, "modules.py marks the documented module covered")

        # 3) benchmark_init scaffolds questions from the note's resolved citations
        r = run("benchmark_init.py", str(repo))
        check(r.returncode == 0, "benchmark_init.py exits 0")
        bj = repo / ".airx" / "ai_memory" / "benchmark.json"
        check(bj.is_file(), "benchmark_init wrote ai_memory/benchmark.json")
        check("BillingService" in bj.read_text(), "scaffold derived a grep_term from the note")
        _q = json.loads(bj.read_text())["questions"]
        check(all(not q.get("measure", {}).get("expect") for q in _q),
              "scaffold leaves expect unset (accuracy not asserted)")

        # idempotent — never clobbers
        r = run("benchmark_init.py", str(repo))
        check("already exists" in r.stdout, "benchmark_init is idempotent")

        # 4) benchmark reports a real memory win, in the right place
        r = run("benchmark.py", str(repo))
        check(r.returncode == 0, "benchmark.py exits 0")
        check("MEMORY:" in r.stdout and "fewer tokens" in r.stdout, "benchmark reports a memory token win")
        check((repo / ".airx" / "ai_memory" / ".cache" / "token-reduction.json").is_file(),
              "benchmark wrote results to ai_memory/.cache/")
        check(not (repo / ".airx" / "ai_knowledge_base").exists(),
              "memory-only repo never grows an ai_knowledge_base/ folder")

        # 5) evidence reads the token arm from the new location
        r = run("evidence.py", str(repo))
        check(r.returncode == 0, "evidence.py exits 0")
        check("fewer tokens" in r.stdout, "evidence surfaces the token win from ai_memory/.cache/")

        # 6) back-compat: a legacy ai_knowledge_base/benchmark.json is still read
        (repo / ".airx" / "ai_memory" / "benchmark.json").unlink()
        legacy = repo / ".airx" / "ai_knowledge_base"
        legacy.mkdir(parents=True, exist_ok=True)
        (legacy / "benchmark.json").write_text(json.dumps({"questions": [
            {"id": "q1", "measure": {"grep_term": "BillingService",
                                     "memory_note": "reference_billing.md"}}]}))
        r = run("benchmark.py", str(repo))
        check(r.returncode == 0 and "N/A" not in r.stdout,
              "benchmark falls back to legacy ai_knowledge_base/benchmark.json")

    if FAILS:
        print(f"\nFAILED ({len(FAILS)}): " + "; ".join(FAILS))
        return 1
    print("\nObjective-1 e2e: list → author → prove all pass")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
