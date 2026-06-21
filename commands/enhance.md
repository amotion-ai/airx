---
description: Fold what a commit changed into memory — verified additions only (self-improve, human-in-loop).
argument-hint: "[module] (default: from PENDING-ENHANCEMENTS.md)"
---

# /airx:enhance [module]

Self-improve memory from the work just done. Consumes the deterministic worklist
`ai_memory/PENDING-ENHANCEMENTS.md` (produced by the post-commit hook / `memdiff.py`) and folds it in —
**without ever asserting an unverified claim.**

## Steps
1. Read `ai_memory/PENDING-ENHANCEMENTS.md` (or run `python3 "${CLAUDE_PLUGIN_ROOT}"/tools/memdiff.py <wiki>`).
2. **Drift** (note claims that no longer resolve): re-verify each against code; fix the citation or downgrade
   to `TBD`. Never leave a stale claim asserting.
3. **Enhance candidates** (new symbols missing from memory): for each, add a line to the right note section
   citing the real symbol (`Class` / `Class.method` / `queries.xml` name). The *why/what-changed/trap*
   comes from the human or the commit message — never invent it.
4. **Toggle** (`self_improve.auto_enhance` in `.ai-readiness.yml`):
   - **off (default)** → propose every addition; the human accepts/rejects (Claude Code diff gate).
   - **on** → auto-land additions whose symbol citation resolves, **tagged `to-enrich`** (a stub awaiting
     the human's *why*). Semantic claims (why/traps) are still proposed, never auto-landed.
   > `to-enrich` stubs do NOT count toward the Depth score — so auto-enhance can't game quality with bare
   > symbol mentions. They're a worklist for the human to enrich, not finished memory.
5. Append a **Ticket-History** entry (`<TICKET> — what changed`) from the commit subject; bump
   `updated_date` / `last_verified` / `code_ref`.
6. Re-verify and show the delta:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}"/tools/verify-citations.py <wiki>
   python3 "${CLAUDE_PLUGIN_ROOT}"/tools/check.py <wiki>     # drift should drop
   python3 "${CLAUDE_PLUGIN_ROOT}"/tools/score.py <wiki>     # Coverage/Depth trend should rise
   ```
