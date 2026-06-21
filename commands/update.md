---
description: After a ticket/change, update the affected module's memory note so memory stays living (P-UPDATE).
argument-hint: "[module] [ticket-id] — what changed"
---

# /airx:update [module] [ticket]

Keep memory **living** across the SDLC: right after a ticket lands, fold what changed into the module's
note. This is the freshness half of the loop — without it, notes rot and the drift signal climbs. **A stale
note is worse than none.**

## Steps
1. Identify the changed module + ticket (from `$ARGUMENTS`, the latest commit subject, or `git diff`).
2. Edit `ai_memory/reference_<module>.md`:
   - **Append a Ticket History entry** under that section: `<TICKET> — cause · flows touched ·
     queries/methods changed · UI line`. Cite the changed files (`file:line` or symbol).
   - **Update any section the change affected** (methods, queries, flows, geo-variants), re-verifying each
     touched claim against the new code. Anything you can't confirm → `TBD`, never assert.
   - **Bump** `updated_date: <date> (<ticket>: what changed)`, `last_verified`, and `code_ref` to current HEAD.
   - Refresh the note's one-line `description` and its `ai_memory/MEMORY.md` entry.
3. Show the diff (preserve human edits — never blind-overwrite).
4. Re-verify:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}"/tools/verify-citations.py <wiki>
   python3 "${CLAUDE_PLUGIN_ROOT}"/tools/check.py <wiki>      # citations + drift should improve
   ```

> Triggered by you after a ticket, or prompted by the freshness hook when `code_ref` falls behind HEAD.
> For a whole-wiki catch-up across many notes, use `/airx:refresh` instead.
