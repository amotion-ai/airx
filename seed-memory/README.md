# seed-memory — predict-and-verify head-start bundles

A **seed** gives a new repo of a known archetype a ~50% head start instead of a blank page. Each line is
tagged so nothing is mistaken for fact:

- 🟢 **family** — true for any repo in this archetype (the stack inherently works this way)
- 🟡 **verify** — likely true here, confirm against code (versions, class names)
- 🔴 **repo-specific** — fill from *your* code

Rule: a 🟡/🔴 line is a **hypothesis** until it cites a real `file:line`. The seed predicts; your code proves.

## Planned bundles (Phase 1)
Each is a 6-file shape (`README`, `MEMORY`, `SEED-ARCHITECTURE`, `SEED-DOMAIN`, `SEED-GOTCHAS`, `CLAUDE`):
- `enterprise-java/` — Spring-XML · JSF/PrimeFaces · Hibernate · MySQL (legacy beanstack)
- `spring-boot/` — modern Spring Boot REST backend
- `flutter/` — offline-first mobile (Flutter)

> Contributions welcome — new archetypes are the network effect. Keep them code-verified and terse.
