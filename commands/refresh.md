---
description: Re-verify project memory against current code, then report freshness — one step.
---

# /airx:refresh

Bring the airx wiki (the repo itself, or a sibling `<repo>-wiki/`) back in sync with `HEAD` after code
has moved. Convenience over the existing pieces, with no new engine: it delegates to the `kb-curator`
subagent, then runs the deterministic conformance check.

## Steps
1. **Curate.** Delegate to the `kb-curator` subagent, passing the wiki dir. It runs `check` ·
   `verify-citations` · `purify` · `memdiff`, judges each flagged claim against the code (moved → re-cite,
   gone → `TBD`, library type → leave it), and regenerates any registry from code. Its context stays
   separate, so the tool output doesn't fill the main session.
2. **Review** its ≤15-line report with the user. The needs-human list (unconfirmable *why* claims) is
   theirs to answer. Nothing there is guessed.
3. **Check.** Run the conformance gate:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}"/tools/check.py <wiki-dir>
   ```

## When to run
After material code changes to a documented module, or once per sprint — not every commit. The
SessionStart hook already tells the agent which notes have code changes under them; this is the deliberate catch-up. **A stale note is worse than
none** — refresh or downgrade to `TBD`, don't leave it asserting outdated facts.
