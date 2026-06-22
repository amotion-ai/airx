#!/usr/bin/env python3
"""airx test runner — runs every tests/test_*.py and reports a single pass/fail. Stdlib only, no deps.

    python3 tests/run.py

Exit 0 if all suites pass, 1 otherwise. This is what CI (and a contributor) runs to know the
deterministic surface still holds — the honest, reproducible answer to "do the checks pass?"."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    suites = sorted(HERE.glob("test_*.py"))
    if not suites:
        print("no test_*.py suites found", file=sys.stderr)
        return 1
    failed = []
    for s in suites:
        print(f"\n=== {s.name} " + "=" * (60 - len(s.name)))
        rc = subprocess.run([sys.executable, str(s)]).returncode
        if rc != 0:
            failed.append(s.name)
    print("\n" + "=" * 64)
    if failed:
        print(f"RESULT: FAIL — {len(failed)}/{len(suites)} suite(s) failed: {', '.join(failed)}")
        return 1
    print(f"RESULT: PASS — {len(suites)}/{len(suites)} suite(s) passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
