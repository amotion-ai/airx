#!/usr/bin/env python3
"""Fixture tests for verify-citations.py — the tool that backs airx's core claim ("every citation
mechanically resolves"). Builds a tiny throwaway repo + memory note in a temp dir, then asserts the
tool resolves the true citations and FLAGS the false ones. Stdlib only, no pytest, no network.

The cases that matter (and used to pass silently before structural resolution):
  • `Class.madeUpMethod`  — owner type exists but the method does not → must be FLAGGED, not resolved.
  • `UndeclaredService`   — a *file* by that name exists but declares no such type → must be FLAGGED.
  • an out-of-bounds `file:line` → must HARD-FAIL (exit 1).
"""
from __future__ import annotations

import importlib.util
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOOL = HERE.parent / "tools" / "verify-citations.py"


def load_tool():
    spec = importlib.util.spec_from_file_location("verify_citations", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write(p: Path, text: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def build_fixture(root: Path):
    """A minimal but realistic repo + a memory note that cites it (some cites true, some false)."""
    repo = root / "repo"
    src = repo / "src/main/java/com/acme"
    # A real service: declares the type, one real method, a real bean id.
    write(src / "BillingService.java", (
        "package com.acme;\n\n"
        '@Service("billingService")\n'
        "public class BillingService {\n"
        "    public Money applyTax(Order o) { return round2(o.total()); }\n"
        "    private double round2(double v) { return Math.round(v * 100) / 100.0; }\n"
        "}\n"
    ))
    # A file whose NAME says Service but which declares no such type (filename != declaration).
    write(src / "UndeclaredService.java", "package com.acme;\n// intentionally declares nothing\n")
    # An externalized named query.
    write(src / "queries.xml", (
        '<queries>\n  <query name="Billing.findUnpaid">FROM Invoice WHERE paid = 0</query>\n</queries>\n'
    ))

    wiki = root / "wiki"
    write(wiki / ".ai-readiness.yml", f"repo_path: {repo}\nstack: enterprise-java\n")
    # The memory note. Backticked symbols + one good and one bad file:line.
    write(wiki / "ai_memory" / "reference_billing.md", (
        "# Billing\n\n"
        "Core service is `BillingService` (`BillingService.java:4`).\n"
        "Tax is applied in `BillingService.applyTax`; it calls `BillingService.round2`.\n"
        "But `BillingService.madeUpMethod` does not exist.\n"
        "Unpaid invoices use named query `Billing.findUnpaid`.\n"
        'Wired as `@Service("billingService")`; there is no `@Service("ghostBean")`.\n'
        "Helper `UndeclaredService` is referenced but not declared anywhere.\n"
    ))
    write(wiki / "ai_memory" / "MEMORY.md", "# MEMORY\n- billing -> reference_billing.md\n")
    return wiki


# --- tiny assert harness -------------------------------------------------------------
FAILS: list[str] = []


def check(cond: bool, name: str):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}")
    if not cond:
        FAILS.append(name)


def joined(problems) -> str:
    return "\n".join(problems)


def main() -> int:
    mod = load_tool()
    with tempfile.TemporaryDirectory() as td:
        wiki = build_fixture(Path(td))
        r = mod.check_wiki(wiki)
        sp = joined(r["sym_problems"])

        print("structural symbol resolution:")
        check("madeUpMethod" in sp, "made-up Class.method is FLAGGED (was the silent gap)")
        check("ghostBean" in sp, "non-existent bean id is FLAGGED")
        check("UndeclaredService" in sp, "filename-only type (no declaration) is FLAGGED")
        check("applyTax" not in sp, "real Class.method resolves (not flagged)")
        check("round2" not in sp, "real private member resolves (not flagged)")
        check("`BillingService`" not in sp, "declared class resolves (not flagged)")
        check("findUnpaid" not in sp, "real named query resolves (not flagged)")

        print("file:line resolution:")
        # the good cite (:4) resolves; there are no bad file:line cites here, so no hard fail.
        check(r["resolved"] == r["total"] and r["total"] >= 1, "in-bounds file:line resolves")
        check(not any("dangling" in p for p in r["problems"]), "no dangling file:line in the good note")

        # now add an out-of-bounds file:line and confirm it HARD-FAILS via the real entry point.
        bad = wiki / "ai_memory" / "reference_billing.md"
        bad.write_text(bad.read_text() + "\nStale: `BillingService.java:9999`.\n")
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = _run_main(mod, wiki)
        print("hard-fail gate:")
        check(rc == 1, "out-of-bounds file:line returns exit 1 (CI gate)")

    if FAILS:
        print(f"\nFAILED ({len(FAILS)}): " + "; ".join(FAILS))
        return 1
    print("\nall verify-citations fixture checks passed")
    return 0


def _run_main(mod, wiki: Path) -> int:
    """Invoke the tool's main() as the CLI would, against the fixture wiki."""
    import sys
    argv = sys.argv
    sys.argv = ["verify-citations.py", str(wiki)]
    try:
        return mod.main()
    finally:
        sys.argv = argv


if __name__ == "__main__":
    raise SystemExit(main())
