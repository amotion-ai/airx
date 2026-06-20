---
description: Capture one module's "why & what-changed" as a verified project-memory note.
argument-hint: "[module-name] (optional — airx proposes modules if omitted)"
---

# /airx:memory [module]

Produce a dense, ticket-linked memory note so the agent stops re-investigating a module. The module name
is an **optional hint, not a prerequisite** — if you don't know your modules, airx proposes them.

This runs as a **propose → verify → approve** loop (you stay in control; nothing is asserted unsigned):

### 1. Module discovery — *how you know which modules exist*
If `$ARGUMENTS` is empty or vague, **propose** the candidate modules, then let the user pick:
- Read `ai_memory/MEMORY.md` "Candidate modules" (seeded by `/airx:init` from repo structure), and
- Rank by **git churn / recency** — the "hottest module" is the one recent commits actually touch:
  `git log --since="6 months ago" --name-only --pretty=format:` → aggregate top-level dirs by hit count.
- Present a short ranked list (e.g. `billing (47 commits) · auth · inventory`) and ask which to capture.
- The user may instead name an area in plain language ("the payment flow") → resolve it to code.
**Confirm the chosen scope before mapping.**

### 2. Map the module from code (cite `file:line`)
Backing beans/controllers, services, queries, the hot computation, the tenant/scoping rule — each a real
`file:line`. Anything you can't cite is `TBD — needs human input`, never invented.

### 3. Mine git for the "why & what-changed"
`git log` the module's paths — capture *what changed and why*, the traps, the "do not revert" lessons,
with ticket IDs.

### 4. Verify with the human, then write
- Draft the note and **surface every `[verify]`/`[fill]` (🟡/🔴) prediction** for the user to confirm
  against code (or downgrade to `TBD`). Don't state a prediction as fact.
- Write `ai_memory/reference_<module>.md` from `_reference_TEMPLATE.md` only on approval (Claude Code's
  accept/reject is the gate). Set `owner`/`last_verified` only when the human signs off.
- **Modifying an existing note?** Show a diff, preserve human edits (never blind-overwrite), and update
  `updated_date: <date> (<ticket>: what changed)`.

### 5. Link & prove
Link it in `ai_memory/MEMORY.md`; run `/airx:check`; prove recall — fresh-session, answer 5 real
questions from the note alone.

> This is the value layer: documentation explains *how it works*; this records *what changed, why, and
> what bit us* — the context an agent otherwise re-derives every session.
