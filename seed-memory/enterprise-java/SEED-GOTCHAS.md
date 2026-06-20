---
name: enterprise-java — Gotchas (seed)
description: Family footguns of the legacy Spring-XML/JSF/Hibernate beanstack. Verify each applies to your repo.
type: reference
owner: TBD
status: SEED
last_verified: TBD
code_ref: TBD
---

# enterprise-java — Gotchas (seed)

> 🟢 traps inherent to this stack. Confirm each against your code, then make them repo-specific (🔴 with `file:line`).

## Forbidden / dangerous (🟢)
- **Tenant-filter bypass.** Raw SQL / `JdbcTemplate` / native queries without an explicit tenant predicate **skip the Hibernate `@Filter`** → cross-tenant data leak. Always go through the filtered session, or add the predicate explicitly. 🔴 list the bypass sites in your repo.
- **Session timing.** Calling `getCurrentSession()` / running queries **before** the per-request filter/ThreadLocal context is set yields unfiltered or wrong-tenant results. 🟡
- **Duplicating named queries.** Re-typing HQL inline instead of reusing the one in `queries.xml` → drift and divergence. Change the named query, not a copy. 🟢
- **Assuming Spring Data.** This is a hand-rolled generic-DAO codebase; there are no magic repositories. 🟢
- **God services.** A few service impls may be huge; the method you want can be buried and have side effects. Read the whole method before editing. 🟡

## Correctness magnets (🟡 — verify if relevant)
- **Money & rounding** recomputed at **multiple call sites** — change the shared method, not one caller, or totals diverge.
- **Geo/region forks** — a flow may pick a different query/branch by country/region; don't assume one path.
- **Composite keys** — equality/lookup needs the full key (tenant codes included), not just the "id".
- **Misspelled / non-obvious symbol names** — legacy code has typos baked into method/column names; grep the actual spelling, not the "correct" one.

## Process (🟢)
- Every concrete claim cites a real `file:line` or says `TBD`. Never invent a path, class, or method.
- After a ticket, append to the module note: `updated_date: <date> (<ticket>: what changed + the trap)`.
