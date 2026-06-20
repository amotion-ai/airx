# airx

**Verified, measured project memory for coding agents.** A Claude Code plugin (and a portable method)
that gives a codebase project memory the agent can trust: every claim cites a real `file:line` or says
`TBD`, and you can prove the speed/token win per repo instead of assuming it.

**Status:** v0.1 (early). `/airx:init`, `/airx:memory`, `/airx:check`, `/airx:refresh`, and
`/airx:benchmark` work today; the alignment / CI-gate layers are on the [roadmap](ROADMAP.md).

New team? Start with [TEAM-START.md](TEAM-START.md) — the whole adoption loop in four steps.

## Why another one

The memory/KB space is crowded, and most tools store or index, then oversell ("120x fewer tokens!")
with no per-repo proof. airx is different on purpose:

| Most tools | airx |
|---|---|
| Store/embed everything | Predict-and-verify: a claim is `[family]` / `[verify]` / `[fill]` and is never stated as fact until it cites `file:line` (else `TBD`) |
| "Huge token savings" | Measured: `/airx:benchmark` proves both the memory win and the KB win on your repo, and says so honestly when it does not pay |
| Greenfield only | Aligns existing docs (roadmap): migrate divergent wikis onto one shape |
| One-off setup | Governed: `/airx:check` conformance today; versioned standard + CI gate on the roadmap |
| Rebuild storage | Composes: reuse existing memory MCPs; airx adds the verification + measurement layer |

The honest pitch, in a field full of hype: "We measure it per repo and tell you when it does not pay."
Memory makes the agent faster and stops it re-deriving context — and `/airx:benchmark` now measures
that directly (tokens to answer from a verified note vs grepping the repo cold). A knowledge base is a
further token lever only where agentic grep is too expensive, and airx makes you prove which.

## What it is (architecture)

airx is a Claude Code plugin, not a CLI wrapper. (Wrapping the CLI is fragile; the supported surface is
plugins / skills / MCP / the Agent SDK.) It ships:

- Slash commands: `/airx:init`, `/airx:memory`, `/airx:check`, `/airx:refresh`, `/airx:benchmark`
- A subagent: `kb-curator` (regenerate registries, check freshness)
- A hook: warns when memory/KB drifts from `HEAD`
- Seed memory: predict-and-verify head-start bundles per stack (e.g. `enterprise-java`)
- `AGENTS.md`: the cross-tool context file (works beyond Claude Code)

## Install

airx is a Claude Code plugin distributed as its own marketplace.

```
/plugin marketplace add amotion-ai/airx
/plugin install airx@airx
```

(Or run without installing: `claude --plugin-dir /path/to/airx`.)

## Use (in your own repo)

```
/airx:init <repo>      stamp a memory-first wiki beside your repo (ai_memory/ + AGENTS.md + CLAUDE.md);
                       auto-detects the stack from build files (override with --stack)
/airx:memory <module>  capture one module's "why and what-changed" (cite file:line or TBD)
/airx:check            conformance (memory-first: ai_memory/ required)
/airx:refresh          re-verify memory against current code, then report freshness (one step)
/airx:benchmark        prove the token win honestly (may say "not worth it"); measures the memory win
                       with no KB, and the KB win once one exists
```

Requires `python3` (stdlib only) and `git`. Stack-agnostic; built and first tested on large legacy Java
(Spring-XML / JSF / PrimeFaces / Hibernate beanstacks) where agents burn tokens and guess paths.

## The method

The discipline behind the tool: [docs/THESIS.md](docs/THESIS.md) — what/why/when for documentation,
knowledge base, and project memory, and the rule that you rank by objective, size by leverage, and prove
by measurement. A sanitized result is in [docs/CASE-STUDY.md](docs/CASE-STUDY.md).

## What's included

```
commands/      the five slash commands
agents/        kb-curator subagent
hooks/         KB-freshness hook
tools/         deterministic stdlib scripts (init, check, benchmark)
seed-memory/   archetype head-start bundles (enterprise-java)
docs/          THESIS (method) + CASE-STUDY
```

## Roadmap

See [ROADMAP.md](ROADMAP.md). Phase 1 plugin (now) -> Phase 2 conformance/benchmark as a CI gate ->
Phase 3 community seed bundles.

## License

MIT - see [LICENSE](LICENSE).
