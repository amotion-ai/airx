# CLAUDE.md — enterprise-java (seed constitution)

> Drop-in agent constitution for a legacy Spring-XML / JSF / PrimeFaces / Hibernate beanstack.
> Fill the [fill] TBDs from your code; keep it terse.

## Ground truth
Before answering about this codebase:
1. Read `ai_memory/MEMORY.md` and the relevant `reference_<module>.md` for "what changed & why."
2. **Cite a real `file:line`.** If you can't, say `TBD — needs human input`. Never invent a path, class, or method.
3. Business claims are labelled as business context, not stated as code fact.

## This repo specifically
- **Every change is full-stack:** `XHTML -> bean -> service -> generic DAO -> tenant filter -> named query`. Trace the chain first.
- **Multi-tenancy is implicit and load-bearing.** Composite keys + Hibernate `@Filter` enabled per request. [fill] your filter name(s) + activation point: TBD (`file:line`).
- **Named queries are externalized** in `queries.xml` — change them there, never inline.
- [fill] The one load-bearing fact unique to this repo: TBD.

## Forbidden patterns
- **Never** write raw SQL / `JdbcTemplate` / native queries without an explicit tenant predicate — it bypasses the Hibernate filter.
- **Never** query before the per-request tenant/ThreadLocal context is set.
- **Never** duplicate a named query inline; reuse the one in `queries.xml`.
- Don't assume Spring Data — this is a hand-rolled generic-DAO codebase.

## Posture
- Search before writing; reuse existing services/DTOs/utilities. One change-aspect at a time; show the plan before large edits.
- After each ticket, update the module's memory note.
