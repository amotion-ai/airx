---
description: Create a verified, ticket-linked project-memory note for one module (Track B of the playbook).
argument-hint: "[module-name] (optional — airx proposes modules if omitted)"
---

# /airx:memory [module]

Author one **dense, verified** memory note so the agent stops re-investigating a module. This is **Track B
(Create)** of the AI-Readiness playbook, delivered in-session. The note's value is the *why & what-changed*
an agent re-derives every session — sourced, then anchored to code.

> **The trust rule (symbol-first).** What to look for comes from sourcing; **the code is what you cite.**
> Every concrete claim carries a real anchor — `file:line` **or** a durable symbol (class / method /
> `queries.xml` name / bean id / table) — or it says `TBD — needs human input`. Never invent. Symbols are
> preferred over line numbers (they survive churn in big files; `/airx:check` verifies them mechanically).

## 0 · Locate the playbook + seed (dynamic)
Read `.ai-readiness.yml` for `stack` + `domain`. If the **ai-readiness-standard** is available
(env `AIRX_STANDARD`, or a sibling/parent `ai-readiness-standard/`), load its
`method/prompt-library.md` and the **domain seed** `domains/<domain>/` (e.g. `dms`: `MODULE-MAP.md`,
`SEED-*.md`, `DOMAIN-GLOSSARY.md`) — the seed is your *prediction* to verify, and the coverage rubric.
If the standard isn't found, proceed with the generic structure below. **Client/domain seeds live in the
standard, not in airx.**

## 1 · Pick the module (propose → confirm)
If `$ARGUMENTS` is empty/vague, propose the hottest modules from `ai_memory/MEMORY.md` (seeded by
`/airx:init` from git churn) and let the user pick, or resolve a plain-language area ("the billing flow").
**Confirm scope before mapping.**

> **Steering (optional).** Pass focus areas / domain terms / a ticket id as `$ARGUMENTS` to bias which
> module gets picked and what to emphasize — e.g. `/airx:memory billing PH-fork JIRA-1234` weights the
> billing module and the PH geo-fork, and pulls the named ticket into step 9 (Ticket history).

> **Start from an archetype prediction.** To seed this module from a predict-and-verify bundle first, run
> `python3 "${CLAUDE_PLUGIN_ROOT}"/tools/seed_apply.py <wiki>` (seed_apply.py), then verify each
> `[verify]`/`[fill]` line against code here before promoting it into the note.

## 2 · Source first (don't draft from code alone)
Per the standard's `sourcing-playbook.md`: the *meaning/why* comes from the human (tickets, PH/MY
forks, "don't touch X"), the *code* makes it true. Ask the user for any raw notes / ticket IDs; capture
them as `[verify]` until anchored. Reading code alone yields plausible, context-free nonsense.

## 3 · Fill the note structure, **stop-and-show after each section**
Write `ai_memory/reference_<module>.md` from `_reference_TEMPLATE.md`. Run these as steps; pause for the
user to approve each (Claude Code accept/reject is the gate):
1. **Package & class overview** — table: class · annotations · purpose (only classes you open + cite).
2. **Types & statuses** — single-char codes etc.: the CODE enum AND the labelled BUSINESS meaning.
3. **Key methods** — grouped, exact signatures, cite each (bean then service; note `@Transactional`).
4. **Models & screens** — key fields + the XHTML pages / REST paths.
5. **Named queries & tables** — `queries.xml` names (incl. geo-specific) + DB tables, with counts.
6. **Business-logic flows & formulas** — numbered steps (method per step); paste real calc code blocks.
7. **Geo-variants** — every fork (e.g. PH/MY): query prefix, differing fields, routing method. **Verify
   each in `queries.xml`.**
8. **Inter-module deps & config flags** — cite each.
9. **Ticket history** — per ticket ID: cause · flows · queries/methods · UI line. The crown-jewel knowledge.

## 4 · Verify, link, prove
- Run `python3 "${CLAUDE_PLUGIN_ROOT}"/tools/verify-citations.py <wiki>` — fix any dangling `file:line`;
  review unresolved symbols (renamed vs external library).
- Run `python3 "${CLAUDE_PLUGIN_ROOT}"/tools/check.py <wiki>` — `citations` + `drift` must be green.
- Add the dense one-line entry to `ai_memory/MEMORY.md`; stamp `last_verified` + `code_ref` on sign-off.
- Prove recall with `/airx:memtest` (answer 5 real questions from the note alone).
