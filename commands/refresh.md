---
description: Re-verify project memory against current code, then report freshness — one step.
---

# /airx:refresh

Bring the `<repo>-wiki/` back in sync with `HEAD` after code has moved. Convenience over the existing
pieces — no new engine: it runs the `kb-curator` subagent, then the deterministic conformance check.

## Steps
1. **Curate** — invoke the `kb-curator` subagent on `<repo>-wiki/`. It compares each note's `code_ref`
   to repo `HEAD`, flags stale notes and uncited claims (`TBD` candidates), and regenerates any
   registry from code (never hand-edited). It does **not** invent paths/classes/methods.
2. **Re-verify touched notes** — for each flagged note, confirm its `file:line` citations still hold;
   update `updated_date`/`last_verified` and bump `code_ref` to current `HEAD`. Anything unconfirmed
   becomes `TBD` — never assert.
3. **Check** — run the conformance gate:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}"/tools/check.py <wiki-dir>
   ```

## When to run
After material code changes to a documented module, or once per sprint — not every commit. The
freshness hook already warns on drift; this is the deliberate catch-up. **A stale note is worse than
none** — refresh or downgrade to `TBD`, don't leave it asserting outdated facts.
