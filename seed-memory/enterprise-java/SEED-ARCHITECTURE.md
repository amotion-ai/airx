---
name: enterprise-java — Architecture (seed)
description: Family-trait architecture of a legacy Spring-XML/JSF/PrimeFaces/Hibernate beanstack. Verify against code.
type: reference
owner: TBD
status: SEED
last_verified: TBD
code_ref: TBD
---

# enterprise-java — Architecture (seed)

> Tags: [family] = holds for any repo in this archetype; [verify] = confirm against your code (`file:line`); [fill] = repo-specific.

## Stack ([family] unless noted)
- **UI:** JSF + PrimeFaces, server-rendered `*.xhtml`; navigation often via `faces-config.xml`. [verify] confirm PrimeFaces version.
- **Beans:** session/view-scoped `*Bean.java` extending a shared base (`AbstractBean`/`BaseBean`) that centralizes session/context/utility access. [verify] confirm the base class name.
- **Services:** interface + impl pair per area; impls can grow into large "god services." [verify]
- **Persistence:** Hibernate via a **hand-rolled generic DAO** (e.g. `GenericHibernateDAO`/`BaseDAO`); **no Spring Data**. [verify] confirm the DAO class.
- **Queries:** externalized **named queries in `queries.xml`**, referenced by name (HQL/SQL). [verify] locate the files.
- **Config:** **Spring XML** (`applicationContext*.xml`, `web.xml`) — not Spring Boot. [verify] confirm entrypoints.
- **DB:** relational (often MySQL/Oracle). [fill] confirm.

## Request path ([family])
`XHTML action -> backing bean method -> service -> generic DAO -> named query (queries.xml) -> DB`,
with the **tenant filter** silently applied on the Hibernate session. Edit = touch all layers.

## Multi-tenancy ([family] — load-bearing)
- Entities use **composite keys** carrying tenant/branch codes (e.g. company/branch/distributor code). [verify] confirm the key shape.
- Hibernate **`@FilterDef` + `@Filter`** restrict rows by tenant; the filter is **enabled per request** from a ThreadLocal context. [verify] find the `@FilterDef` name(s) and where `enableFilter(...)` is called (`file:line`).
- [fill] List your exact filter name(s) and the activation point — this is the single most important thing to get right.

## Topology / build ([verify])
- A **WAR monolith**, often with a few standalone satellite services (reports, ETL, integrations). [verify]
- Build: Maven and/or Gradle. [fill] confirm modules.

## To verify next (drop the [verify])
Base bean class / generic DAO class / `queries.xml` locations / `@FilterDef` name(s) + activation / Spring XML entrypoints / DB engine / satellite services.
