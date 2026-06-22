# tests

The honest, reproducible version of "the checks pass." Stdlib only — no pytest, no network, no deps.

```
python3 tests/run.py
```

Exit 0 = all suites pass. This is what CI and a contributor run.

## What's covered

| suite | proves |
|---|---|
| `test_verify_citations.py` | the **core claim** — that citations resolve *structurally*, not by filename. Builds a throwaway repo + memory note in a temp dir and asserts the tool **flags** a made-up `Class.method`, a non-existent bean id, and a file that's named like a type but declares none — while **resolving** the real class, method, named query, and bean. Also asserts an out-of-bounds `file:line` hard-fails (exit 1). |
| `test_tools_smoke.py` | every tool in `tools/` parses and has a CLI entry point — the committed form of the "all tools parse" line in `docs/BETA-EVIDENCE.md`. |

## Conventions

- **Hermetic.** Fixtures are written to a `tempfile.TemporaryDirectory()` at runtime, not committed —
  no path rot, no stale git state, each run starts clean.
- **A test names what it pins.** The verify-citations suite exists because those exact cases
  (`BillingService.madeUpMethod`, a filename-only type) used to resolve *silently* before structural
  resolution landed — the test is the guardrail against that regressing.

## Adding a suite

Drop a `test_*.py` next to the others. It must be runnable standalone and exit non-zero on failure;
`run.py` discovers and aggregates it automatically.
