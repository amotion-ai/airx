---
name: enterprise-java — Domain shape (seed)
description: Generic enterprise line-of-business shapes common to this archetype. Your actual domain is repo-specific.
type: reference
owner: TBD
status: SEED
last_verified: TBD
code_ref: TBD
---

# enterprise-java — Domain shape (seed)

> The business domain is **repo-specific ([fill])** — capture *yours* from code/tickets. What's generic ([family])
> is the *shape* legacy enterprise LOB apps tend to share. Don't assume specifics; verify.

## Common enterprise-LOB shapes ([family] patterns, not facts about your repo)
- **Master data** (parties, products, locations, price/tax setup) vs **transactions** (orders, invoices, receipts, returns, adjustments).
- **Document lifecycle**: draft -> validate -> approve -> post -> (cancel/return). Status is often a **single-char/code column** — build a code->meaning map.
- **Money math**: gross -> discounts/schemes -> tax -> net -> **rounding**. Rounding rules are configurable and a frequent bug source.
- **Multi-branch / multi-entity**: the same flow runs per company/branch; behavior can fork by **geo/region**.
- **Batch/period operations**: day-end/period-close style jobs that lock or roll up data.

## How to capture your domain ([fill] — fill from your repo)
- [fill] Glossary: the 10–20 domain terms a newcomer hears week one (with the code symbol each maps to).
- [fill] The 3–5 **hot modules** your tickets actually touch (start memory notes there).
- [fill] Status/type **code tables** (single-char codes -> meaning), cited to the enum/constant/query.
- [fill] Any **geo/region forks** in business rules.

> Rule: a domain claim is *business context*, labelled as such — not stated as a code fact unless it cites `file:line`.
