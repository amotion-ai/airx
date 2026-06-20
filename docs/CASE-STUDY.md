# Case study — memory-first on a legacy DMS (Phase 0 proof)

> Sanitized result from applying airx to a real, large legacy codebase. No client names, paths, or
> ticket IDs — just the method and the outcome.

## The repo
A legacy enterprise **Java / PrimeFaces "beanstack" DMS**: ~5,500 Java files, ~1,300 XHTML views,
~300 named-query files, multi-tenant via Hibernate `@Filter`. Every change is full-stack
(XHTML → bean → service → DAO → `queries.xml` → tenant filter). It had **no AI memory**.

## What we did (memory-first, one module)
Targeted the team's **hottest module** (the one their recent tickets actually touched). One command to
stamp `ai_memory/` (`/airx:init`), then one dense, verified note (`/airx:memory <module>`):
1. Mapped the bean / service / save-flow / the hot computation / the tenant filter from code.
2. Mined git for the module's ticket history — *what changed and why*, including a **"do-not-revert"** lesson.
3. Wrote a dense, frontmattered note — **every claim cites `file:line` or says `TBD`.**

## The result — and why it's the differentiator
- **9 verified `file:line` citations 🟢, 10 explicitly marked "verify" 🟡.** Nothing fuzzy was stated as fact.
- **Predict-and-verify caught 2 would-be errors** before they shipped: a method whose name is *misspelled
  in the codebase* (grep the typo, not the correct spelling), and a round-off method whose line/signature
  didn't match the first mapping — flagged 🟡, not asserted. *A store/index tool would have embedded both.*
- **Captured tacit knowledge that lives nowhere in the code:** a ticket where a change was silently
  auto-reverted and had to be re-committed — exactly the "why / what-changed" an agent re-derives every
  session. That is the value layer; grep can't find it.
- **`/airx:check` → structure PASS** (conformant, memory-first).

## The honest part
- We did **not** build a knowledge base here — memory-first, KB deferred until `/airx:benchmark` proves
  it pays on this repo.
- Memory's win is **speed + fewer re-investigations + not re-breaking business rules**, not a per-query
  token cut. We report it that way on purpose.

## Takeaway
airx didn't *store* or *embed* the codebase. It produced a small, **verified, honest** note that gives
the agent the *why* — and **refused to assert what it couldn't cite.** That discipline (predict-and-verify
+ measure-don't-assume) is the wedge, not storage.
