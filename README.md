# airx

**Your coding agent forgets your codebase every session. airx gives it memory it can trust.**

Point Claude Code (or any agent) at a large repo and watch it re-derive the same context every time:
grep thousands of files, guess the wrong path, re-break a business rule a ticket fixed last month — and
burn tokens doing it. The usual fix is another vector store that promises "120x fewer tokens" and never
proves it on *your* repo.

airx takes a different bet. It writes your repo a small, **verified** project memory — every claim cites
a real `file:line` or says `TBD`, never a guess — and then **measures** the token win on your actual repo
instead of asserting one. Built for **large legacy codebases** (first proven on a 5,500-file
Java/PrimeFaces monolith), where agents waste the most.

**It grows with you.** Start with project memory (works on *any* codebase). Add documentation, a
knowledge base, or a viewer **only if you want them** — each layer verified and measured, never forced,
never bloating your repo by default. New here? See [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md).

## Prerequisites

- **Claude Code** — airx is a plugin; the `/airx:*` commands run inside a Claude Code session (the
  agent-driven `/airx:memory` and `/airx:refresh` need model access).
- **Python 3.7+** — the deterministic tools (`init` / `check` / `benchmark`) are stdlib-only; nothing
  to `pip install`.
- **git** — point it at a git repo; airx anchors freshness to `HEAD` and mines ticket history for the
  "why / what-changed". Without git, `init` still runs but `code_ref` falls back to `TBD`.

## Try it in 60 seconds

Install the Claude Code plugin:

```
/plugin marketplace add amotion-ai/airx
/plugin install airx@airx
```

Then, in your repo:

```
/airx:init <repo>   stamp project memory INSIDE your repo so the agent auto-loads it (detects your stack)
/airx:memory        capture a hot module — don't know your modules? airx proposes them, ranked by git churn
```

That's the whole first run. No servers, no embeddings, no config — just `python3` (stdlib) and `git`.

## The loop

| command | what it does |
|---|---|
| `/airx:init` | stamp `ai_memory/` + root `CLAUDE.md`/`AGENTS.md` *inside* the repo (agent auto-loads it); detect the stack; seed candidate modules |
| `/airx:memory` | propose your hottest modules, then write one dense verified note (you approve each claim) |
| `/airx:check` | conformance — right shape, fresh, frontmatter valid (exit-codes, so it gates CI) |
| `/airx:refresh` | re-verify memory against current `HEAD` in one step |
| `/airx:benchmark` | prove the token win honestly — measures the memory win with no KB, the KB win once one exists, and says so when it doesn't pay |

Optional layers you can add later, only if you want them: **`/airx:docs`** (human documentation) ·
**`/airx:kb`** (knowledge base — the per-stack token lever) · **`/airx:view`** (browse what you've built).

## Does it actually work?

We ran it memory-first on one hot module of a real legacy Java enterprise application (~5,500 Java files, ~1,300 XHTML
views, multi-tenant Hibernate). One `/airx:init`, one `/airx:memory`:

- **9 verified `file:line` citations; 10 flagged "verify" — nothing fuzzy was stated as fact.**
- **Predict-and-verify caught 2 bugs before they shipped:** a method name *misspelled in the codebase*
  (you have to grep the typo, not the correct spelling), and a rounding method whose signature didn't
  match. A store-everything tool would have embedded both as truth.
- **Captured a "do-not-revert" ticket lesson** that lives nowhere in the code — exactly the context an
  agent re-derives every session.

Full writeup: [docs/CASE-STUDY.md](docs/CASE-STUDY.md).

## Why it's different

Most memory/KB tools **store or embed**, then oversell. airx adds the layer they skip —
**verification + measurement**:

- **Verified, not vibes.** Every claim is tagged `[family]` / `[verify]` / `[fill]` and isn't treated as
  fact until it cites `file:line`; otherwise it says `TBD`. A stale or hallucinated note is worse than none.
- **Measured, not promised.** `/airx:benchmark` computes the real token delta on your repo — memory vs
  grepping cold, KB vs registry-load — and tells you honestly when it doesn't pay.
- **Composes, doesn't clone.** It's a Claude Code plugin on the supported surface (plugins / skills /
  MCP), not a fragile CLI wrapper or yet another storage engine. Reuse your memory MCP; airx adds the trust layer.

The method behind it: [docs/THESIS.md](docs/THESIS.md) — rank by objective, size by leverage, prove by
measurement.

## Where we are

v0.1, early and honest about it. The memory layer (the five commands above) works today. The optional
layers — `/airx:docs`, `/airx:kb` (with per-stack generator packs), and `/airx:view` — are on the
[roadmap](ROADMAP.md), added progressively and only where measurement justifies them. New?
[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md). Adopting with a team? [TEAM-START.md](TEAM-START.md).

## License

MIT — see [LICENSE](LICENSE).
