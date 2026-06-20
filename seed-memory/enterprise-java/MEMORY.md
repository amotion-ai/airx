---
name: enterprise-java — Seed Memory Index
description: Predict-and-verify index for a legacy Spring-XML / JSF / PrimeFaces / Hibernate beanstack.
type: reference
owner: TBD
status: SEED
last_verified: TBD
code_ref: TBD
---

# enterprise-java — Seed Memory Index

> The spine the agent should internalize, plus the module notes to build. 🟢 family · 🟡 verify · 🔴 fill.

## Spine (verify each against code)
- 🟢 Every feature is **full-stack**: `XHTML → backing bean → service → DAO → tenant filter → named query`. Trace the whole chain before editing.
- 🟢 **Multi-tenancy is implicit and load-bearing** — composite keys + Hibernate `@Filter` activated per request via a ThreadLocal context. Bypassing it leaks across tenants.
- 🟢 **Named queries are externalized** (`queries.xml`) and referenced by name — change the query there, not inline.
- 🟡 Config is **Spring XML** (`applicationContext*.xml`) — confirm the bean wiring entrypoints (`file:line`).
- 🟡 **Geo/region variants** may fork query or routing logic — confirm whether your repo branches by country/region.
- 🔴 The "one load-bearing fact" specific to your repo — fill after reading code.

## Module notes to build (one per hot module)
> Start with the module your recent tickets actually touch. For each: `reference_<module>.md` with the
> bean/service/named-queries, the hot computation, the tenant rule, and the ticket-linked "what changed & why".
- 🔴 `reference_<module-1>.md` — TBD
- 🔴 `reference_<module-2>.md` — TBD

## Cross-cutting references
- 🟡 `reference_multi_tenancy.md` — the exact `@FilterDef` name(s) + where the filter is enabled (`file:line`).
- 🟡 `reference_money_and_rounding.md` — if the domain handles money: where amounts/rounding are computed (a classic bug magnet).
