# The airx thesis — what / why / when

Every codebase an AI agent works on needs a **deliberate mix** of three artifacts — ranked by
objective, sized by leverage, **proven by measurement**. Not a checklist; a method.

## The three artifacts
| | **Documentation** | **Knowledge Base** | **Project Memory** |
|---|---|---|---|
| **What** | Human narrative (architecture, business logic) | Machine-queryable index (registries/graphs, exact `file:line`) | Dated, ticket-linked notes of *what changed & why* |
| **Why** | Humans understand the system | The agent finds code cheaply | The agent stops re-deriving context each session |
| **When** | Onboarding, audits, stakeholders | Big/legacy repo where agentic grep is too expensive — **and the index is kept fresh** | Tacit rules (business logic, past fixes) that live nowhere in code; recurring work on the same modules |
| **Tokens** | neutral | the lever — **must be measured** | avoids re-discovery (notes *grow*) |
| **One line** | *explains* | *indexes* | *remembers* |

## The meta-rules
1. **Layers, not a checklist.** Small modern repo -> memory + light docs. Legacy monolith -> eventually all three.
2. **Rank by objective.** human-readiness / faster-dev-via-memory / token-cut-via-KB — the #1 sets shape and depth.
3. **Size by leverage.** Modern repo -> KB is polish. Legacy full-stack -> KB load-bearing; memory pays fastest.
4. **Prove per repo.** Token reduction is earned, not assumed. Measure; report honestly when it doesn't pay.

## How airx delivers this: progressively (not all at once)
The three artifacts aren't a big-bang deliverable — they're **opt-in layers a developer adds in order of
leverage**, so the entry stays simple and nothing empty is forced:
1. **Project memory** — the universal entry layer. Works on *any* stack (legacy or modern); the day-1
   token win; needs no generators.
2. **Documentation** — opt-in, when humans need onboarding.
3. **Knowledge base** — opt-in, when grep is the bottleneck *and* `/airx:benchmark` proves it pays. It is
   **per-archetype**: the registry/graph generators are stack-specific, so a stack with no pack yet is
   honestly "memory-only," not faked.
4. **Viewer** — opt-in presentation over whatever layers exist (not a fourth artifact — a way to browse them).

The product principle that follows: the repo may hold all the machinery, but **a user's footprint is only
what they opt into.** Memory-first by default; everything heavier is a deliberate, measured choice.

## The headline result: behavior, not token-%
On a real Spring Boot repo we ran a controlled A/B — same bug, with vs without airx memory. The **cold**
agent produced a confident, scope-risky multi-tenant fix that was **wrong**, in *both* runs. The
**airx-memory** agent avoided it **both times**, reaching the company-vs-distributor scoping model.
Reproducible directionally; precision scales with note depth. The proof airx works is **"the agent
avoids the wrong fix" — not a token reduction number.** Token-% is reported, never the headline.

## Position: the verified-INTENT layer (composes on graph/LSP)
airx is **not** a retrieval competitor. A graph/LSP foundation (CodeGraph, Serena) indexes *structure* —
symbols, call edges, definitions. airx records *intent*: "this method is misnamed; it drives tenant
scoping; don't revert it." The A/B trap is exactly the seam — **a call graph is structurally blind** to a
mislabeled symbol or a do-not-revert rule, no matter how complete its edges. airx layers verified human
"why" **on** that foundation, not against it.

Against the memory camp (agentmemory, codebase-memory-mcp), the differentiator is **verification + drift +
the self-improve loop**: those store/embed; airx mechanically resolves every citation, flags drift when
code moves, and keeps memory honest across commits — automation may *remove* a lie, never *add* one.

## SOTA alignment (2026)
- **Memory is the rising layer** (mem0/Letta/Zep) — lead with it.
- **Agentic search is replacing code-RAG.** Agents grep by default; a *structured, fresh* index earns
  its place only where grep is too expensive. A **stale index is worse than none.** airx's KB is a
  deterministic registry (cite `file:line`), **not** vector RAG.
- **Terse + novel + verified context wins.** Bulky or LLM-generated context measurably *reduces*
  performance — so airx enforces dense, cited, `TBD`-not-guessed notes.

## The discipline that makes it trustworthy
Predict-and-verify ([family] family / [verify] verify / [fill] repo-specific) / cite **symbol-or-`file:line`
or `TBD`** / deterministic extractors (no LLM inference of facts) / conformance + benchmark to keep it honest.

- **Symbol-first citation.** The best memory cites by *durable symbol* — class, method, `queries.xml` name,
  bean id — not brittle line numbers (which break on churn in a 12k-line god-service). `verify-citations`
  resolves both styles mechanically; symbols survive refactors that move every line.
- **Quality ≠ tokens.** A thin TBD stub can score ~99% on token-reduction yet be useless. So airx grades
  memory on **Coverage · Depth · Trust** (`/airx:score`) and surfaces a **drift** rate (`/airx:check`) —
  separating "didn't lie" from "is actually good." Token-% is reported, never mistaken for quality.
- **Self-improving, never self-lying.** A `post-commit` hook makes memory improve as the developer works:
  **purify is automatic** (deterministic — only flags/downgrades stale claims, never invents), while
  **enhancement is verified + human-in-loop** (an `auto_enhance` toggle may auto-land *mechanically-verified*
  symbol facts, tagged `to-enrich`, which don't count toward Depth until a human adds the *why*). The line
  is absolute: automation may *remove* a lie, never *add* an unverified claim.
