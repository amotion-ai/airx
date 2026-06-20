# airx — AI-readiness for coding agents

> **Verified project memory you can measure.** A Claude Code plugin (and portable method) that gives
> your repo *project memory* the agent can trust — every claim cites a real `file:line` or says `TBD`,
> and you can **prove** the speed/token win per repo instead of assuming it.

**Status:** v0.1 (early). `/airx:init`, `/airx:check`, `/airx:benchmark`, `/airx:memory` work today;
seed bundles and the alignment / CI-gate layers are on the [roadmap](ROADMAP.md).

---

## Why another one?

The memory/KB space is crowded — and most tools **store** or **index**, then **oversell** ("120× fewer
tokens!") with no per-repo proof. airx is different on purpose:

| Most tools | airx |
|---|---|
| Store/embed everything | **Predict-and-verify** — a claim is 🟢 family / 🟡 verify / 🔴 repo-specific; nothing is stated as fact until it cites `file:line` (else `TBD`) |
| "Huge token savings!" | **Measured** — `airx benchmark` proves the win on *your* repo, and tells you honestly when it doesn't pay |
| Greenfield only | **Aligns existing docs** *(roadmap)* — migrate divergent wikis onto one shape |
| One-off setup | **Governed** — `/airx:check` conformance today; versioned standard + CI gate on the roadmap |
| Rebuild storage | **Composes** — reuse existing memory MCPs; airx adds the *verification + measurement* layer |

> The honest pitch, in a field full of hype: **"We measure it per repo and tell you when it doesn't
> pay."** Memory makes the agent faster and stops it re-deriving context; a knowledge base is the token
> lever *only where agentic grep is too expensive* — and airx makes you prove which.

## What it is (architecture)

airx is a **Claude Code plugin** — not a CLI wrapper. (Wrapping the CLI is fragile; the supported
surface is plugins / skills / MCP / the Agent SDK.) It ships:

- **Slash commands** — `/airx:init`, `/airx:memory`, `/airx:check`, `/airx:benchmark`
- **A subagent** — `kb-curator` (regenerate registries, check freshness)
- **A hook** — warn when memory/KB drifts from `HEAD`
- **Seed memory** — predict-and-verify head-start bundles per stack/domain
- **`AGENTS.md`** — the cross-tool context file (works beyond Claude Code)

## Install & use

airx is a Claude Code plugin distributed as its own marketplace.

```bash
# add this repo as a plugin marketplace, then install
/plugin marketplace add amotion-ai/airx
/plugin install airx@airx
# (or, without installing: claude --plugin-dir /path/to/airx)
```

Then, **in your own repo**:
```bash
/airx:init <repo>      # stamp a memory-first wiki beside your repo (ai_memory/ + AGENTS.md + CLAUDE.md)
/airx:memory <module>  # capture one module's "why & what-changed" — cite file:line or TBD
/airx:check            # conformance (memory-first: ai_memory/ required)
/airx:benchmark        # only once a KB exists — prove the token win honestly (may say "not worth it")
```

Requires `python3` (stdlib only) and `git`. Stack-agnostic; built and first tested on **large legacy
Java** (Spring-XML / JSF / PrimeFaces / Hibernate beanstacks) where agents burn tokens and guess paths.

## The method
The discipline behind the tool: [`docs/THESIS.md`](docs/THESIS.md) — what/why/when for documentation,
knowledge base, and project memory, and the rule that you **rank by objective, size by leverage, and
prove by measurement.**

## Roadmap
See [`ROADMAP.md`](ROADMAP.md). TL;DR: Phase 1 plugin → Phase 2 conformance/benchmark as a CI gate →
Phase 3 community seed bundles.

## License
MIT — see [`LICENSE`](LICENSE).
