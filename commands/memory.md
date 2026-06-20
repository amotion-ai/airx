---
description: Capture one module's "why & what-changed" as a verified project-memory note.
argument-hint: <module-name>
---

# /airx:memory <module>

Produce a dense, ticket-linked memory note for `$ARGUMENTS` so the agent stops re-investigating it.

Steps:
1. Map the module from code: backing beans/controllers, services, queries, the hot computation, the
   tenant/scoping rule — each with a real `file:line`.
2. Mine git for the module's recent tickets (`git log` grep) — capture *what changed and why*, the traps,
   the "do not revert" lessons, with ticket IDs.
3. Write `ai_memory/reference_<module>.md` from `_reference_TEMPLATE.md`:
   frontmatter (`name`, `type`, `origin_session_id`, `updated_date`), then dense facts — **`file:line` or `TBD`**.
4. Link it in `ai_memory/MEMORY.md`.
5. Verify with `/airx:check`, then prove recall: fresh-session answer 5 real questions from the note alone.

This is the value layer: documentation explains *how it works*; this records *what changed, why, and what bit us*.
