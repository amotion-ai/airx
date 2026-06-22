#!/usr/bin/env python3
"""Smoke test: every tool in tools/ must parse and expose a CLI entry point. This is the committed,
reproducible version of the "all tools parse" line in docs/BETA-EVIDENCE.md — run it, don't trust it.

Catches the most common breakage (a syntax error or a bad edit) across the whole deterministic surface
in one cheap pass. Stdlib only."""
from __future__ import annotations

import ast
from pathlib import Path

TOOLS = (Path(__file__).resolve().parent.parent / "tools")
FAILS: list[str] = []


def check(cond: bool, name: str):
    print(f"  {'ok  ' if cond else 'FAIL'}  {name}")
    if not cond:
        FAILS.append(name)


def main() -> int:
    pys = sorted(TOOLS.glob("*.py"))
    check(len(pys) >= 10, f"found {len(pys)} tools to check")
    for p in pys:
        src = p.read_text(errors="ignore")
        try:
            tree = ast.parse(src)
            ok = True
        except SyntaxError as e:
            ok = False
            print(f"        {e}")
            tree = None
        check(ok, f"{p.name} parses")
        if tree is not None:
            has_main = any(isinstance(n, ast.FunctionDef) and n.name == "main" for n in tree.body)
            has_guard = "__main__" in src
            check(has_main or has_guard, f"{p.name} has a CLI entry point")
    if FAILS:
        print(f"\nFAILED ({len(FAILS)}): " + "; ".join(FAILS))
        return 1
    print(f"\nall {len(pys)} tools parse and are runnable")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
