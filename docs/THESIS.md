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
1. **Layers, not a checklist.** Small modern repo → memory + light docs. Legacy monolith → eventually all three.
2. **Rank by objective.** human-readiness / faster-dev-via-memory / token-cut-via-KB — the #1 sets shape and depth.
3. **Size by leverage.** Modern repo → KB is polish. Legacy full-stack → KB load-bearing; memory pays fastest.
4. **Prove per repo.** Token reduction is earned, not assumed. Measure; report honestly when it doesn't pay.

## SOTA alignment (2026)
- **Memory is the rising layer** (mem0/Letta/Zep) — lead with it.
- **Agentic search is replacing code-RAG.** Agents grep by default; a *structured, fresh* index earns
  its place only where grep is too expensive. A **stale index is worse than none.** airx's KB is a
  deterministic registry (cite `file:line`), **not** vector RAG.
- **Terse + novel + verified context wins.** Bulky or LLM-generated context measurably *reduces*
  performance — so airx enforces dense, cited, `TBD`-not-guessed notes.

## The discipline that makes it trustworthy
Predict-and-verify (🟢 family / 🟡 verify / 🔴 repo-specific) · cite `file:line` or `TBD` ·
deterministic extractors (no LLM inference of facts) · conformance + benchmark to keep it honest.
