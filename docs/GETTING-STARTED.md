# Getting started with airx

airx makes any codebase AI-ready **progressively**. You start with project memory in ~5 minutes; you add
documentation, a knowledge base, or a viewer **only if you want them**. Every layer is verified (cite
`file:line` or `TBD`) and measured (prove the token win). Nothing heavy is forced on you.

## Prerequisites
- **Claude Code** — airx is a plugin; `/airx:*` runs in a Claude Code session (memory steps need model access).
- **Python 3.7+** (stdlib only) and **git**. That's it — no servers, no embeddings.

## The steps (project memory — the universal win)

> Prefer to learn by doing? [FIRST-NOTE.md](FIRST-NOTE.md) is a paste-one-prompt-per-step first run.

**Step 1 — Init in your repo.**
```
/airx:init <repo>
```
Stamps `ai_memory/` + `CLAUDE.md`/`AGENTS.md` at the repo root (so the agent auto-loads memory) + a
manifest. It also seeds `MEMORY.md` with **candidate modules** detected from your repo, and prints a menu
of optional layers. No docs/KB folders are created — memory only.

**Step 2 — Capture your hottest module.**
```
/airx:memory
```
You don't need to know your module names — run it bare and **airx proposes them**, ranked by git churn
(the areas your recent commits actually touch). Pick one (or name an area in plain words). The agent maps
the code (`file:line`), mines git for the "why & what-changed", and **shows you each unverified claim to
confirm** before writing. You approve; it writes the note.

**Step 3 — Work normally.**
The agent now auto-loads that note (via the root `CLAUDE.md`) instead of re-grepping your repo — so it
spends fewer tokens on that module. After a ticket, run `/airx:update <module>` to fold the change in.

**Step 4 — Prove it (token win) and grade it (quality).**
```
/airx:benchmark   # measured token delta — note vs grepping cold (says so if it doesn't pay)
/airx:score       # quality — Coverage · Depth · Trust → GOOD or NOT DONE (token-% is NOT quality)
/airx:check       # conformance + drift gate (exit-codes; gates CI)
/airx:memtest     # answer real questions from the note alone — proves recall
```
Already have memory from before? Run `/airx:validate` to audit it (coverage / drift / freshness / discipline).

**Step 5 — Let it self-improve (opt-in).**
```
/airx:init <repo> --install-hook
```
Installs a git `post-commit` hook (shared via `core.hooksPath`) that, on each commit, **auto-purifies**
stale citations and lists what to enrich (`PENDING-ENHANCEMENTS.md`) — deterministic, non-blocking, **zero
model tokens, never edits your notes**. Fold it in with `/airx:enhance` (human-in-loop; an `auto_enhance`
toggle can auto-land *verified* symbol facts). Memory then gets fresher and deeper as you ship — and
`/airx:score` proves the trend.

## You stay in control (the harness)
Creating or modifying memory is always **propose → verify → approve**: the agent drafts and surfaces every
`[verify]`/`[fill]` prediction for you to confirm against code; it writes only what you accept (Claude
Code's accept/reject is the gate); on edits it shows a diff and **preserves your changes** — never a blind
overwrite. That human-in-the-loop is what makes "verified" true.

## Add more later — only if you want it (optional layers)
| Command | Layer | When |
|---|---|---|
| `/airx:docs` | Human documentation | When people (not the agent) need onboarding |
| `/airx:kb` | Knowledge base (registries + graphs) | Large repo where grep is the bottleneck **and** `/airx:benchmark` proves it pays. Needs a generator pack for your stack |
| `/airx:view` | A viewer to browse memory/docs/KB | When you want to explore it visually |

## Honest FAQ
- **"I ran init and nothing got faster."** Expected — there's **zero benefit until you write the first
  note**. Memory is something you author (with the agent's help), not magic that appears.
- **"Does it auto-reduce tokens?"** Yes, *once a note exists for the module you're touching and the agent
  loads it* — there's no runtime interceptor; it's the agent reading a small verified note instead of
  grepping. And you can measure it.
- **"Do I need a knowledge base / graphs / an MCP server?"** No, not to start. Memory is the universal
  layer. The KB is an opt-in token-lever that needs a per-stack generator — and only where measurement
  justifies it.
- **"My stack has no KB pack."** Fine — memory works on **any** stack (init will tell you). The KB layer
  is added per-archetype over time.
- **"Does it create a standard skeleton / scaffolds?"** Yes. `/airx:init` stamps the skeleton (`ai_memory/`
  + note templates + root `CLAUDE.md`/`AGENTS.md` + `.ai-readiness.yml`); `/airx:draft` scaffolds an
  *unverified* per-module stub to author from; `/airx:docs` and `/airx:kb` scaffold their layers on demand.
- **"Can I bring in seed memory I already have?"** Two ways. **(a) airx's seed bundles** — copy a
  `seed-memory/<archetype>/` bundle into `ai_memory/`, then confirm each `[family]`/`[verify]`/`[fill]` line
  against code with `/airx:memory` (the seed predicts; your code proves). **(b) your own existing notes** —
  drop them into `ai_memory/`, run `/airx:validate` for a prioritized remediation list, then
  `/airx:memory`/`/airx:update` to fix. Either way every claim ends **cited or `TBD`**. A one-command
  importer/normalizer (brownfield *alignment*) is on the [roadmap](../ROADMAP.md), not shipped — today it's
  **drop-in + verify**.
- **"Is there an airx MCP server?"** Not today. The roadmap is an optional MCP *query layer* over the KB and
  **composing** existing memory MCPs for storage — never cloning one. airx's value-add is verification +
  drift + measurement, not another store.
