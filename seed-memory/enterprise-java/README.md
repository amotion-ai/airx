# Seed — enterprise-java (legacy Spring-XML · JSF/PrimeFaces · Hibernate)

> A **predict-and-verify head start** for a legacy enterprise Java "beanstack." The seed *predicts*
> what your repo looks like; **your code proves it.** Every line is tagged — confirm 🟡/🔴 against code
> with a real `file:line`, then keep it. Nothing here is client-specific; it's the archetype's family traits.

**Legend:** 🟢 family (true of any repo in this archetype) · 🟡 verify (likely true here — confirm) ·
🔴 repo-specific (create/fill from your code).

## Is this your archetype? (fit check)
You're here if you see **most** of:
- `*.xhtml` views + `*Bean.java` backing beans extending a shared base (e.g. `AbstractBean`/`BaseBean`).
- **Spring XML** config (`applicationContext*.xml`, `web.xml`) — *not* `@SpringBootApplication`.
- A hand-rolled generic Hibernate DAO + **externalized named queries** (`queries.xml`) — not Spring Data repos.
- **Composite-key** entities + Hibernate `@FilterDef`/`@Filter` for multi-tenancy.
- A WAR monolith, often plus a few standalone satellite services.

If you have `@RestController` + no `.xhtml` → use the **`spring-boot`** seed instead.

## How to use
1. Copy this folder into your `<repo>-wiki/ai_memory/_seed/`.
2. Skim `MEMORY.md`, then run predict-and-verify on each `SEED-*.md`: confirm every 🟡/🔴 with `file:line`.
3. Promote confirmed lines into real `reference_<module>.md` notes; drop the `SEED-` prefix.
4. Adopt `CLAUDE.md` as the repo's agent constitution.

## Contents
`MEMORY.md` (index) · `SEED-ARCHITECTURE.md` · `SEED-DOMAIN.md` · `SEED-GOTCHAS.md` · `CLAUDE.md`.

> The seed predicts; the target repo's code proves. Never present a 🟡/🔴 prediction as fact.
