# airx — Beta Quickstart

Verified, **measured** project memory for coding agents. This is the one-page first-run flow.
Clone the repo, open Claude Code in it, install the plugin, then drive `/airx:*`.

## Prereqs
- **Claude Code** (plugin host with `/plugin` support).
- **python3** — standard library only, no pip installs. The deterministic tools (`init`, `benchmark`,
  `score`, `purify`) are pure stdlib.
- **git** — airx is repo-aware; `--install-hook` needs a git repo, and `in-repo` layout assumes you commit.

## Install from a local clone
You already `cd`'d into the clone. Inside Claude Code, run:

```text
/plugin marketplace add .
/plugin install airx@airx
```

- `add .` registers *this* checkout as a local marketplace (`marketplace.json` has `"source": "."`).
  Equivalent fallback: `/plugin marketplace add /absolute/path/to/airx`.
- `install airx@airx` = plugin `airx` from marketplace `airx` (both names confirmed in
  `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`).
- **Fallback (from GitHub, not the local clone):** `/plugin marketplace add amotion-ai/airx`
  then `/plugin install airx@airx`.

After install, type `/airx:` and the 11 commands below should autocomplete.

## First 10 minutes
Run these in order, in the repo you want to make AI-ready (use `.` for the current repo):

1. `/airx:init --repo . --install-hook`
   Stamps the memory layer: `ai_memory/` + root `CLAUDE.md`/`AGENTS.md` + `.ai-readiness.yml`, seeded with
   candidate modules. `--install-hook` adds the post-commit self-improve hook. Under the hood it runs
   `python3 tools/init.py --repo . --install-hook` (supported flags: `--repo`, `--layout`, `--stack`,
   `--domain`, `--install-hook`).
2. `/airx:memory <hottest-module>`
   Author ONE verified, ticket-linked note for your busiest module. Omit the name and airx proposes modules.
   **This is the step that creates value — empty memory helps nothing.**
3. `/airx:benchmark`
   Honest token/speed measurement on *this* repo (token ≈ chars/4, no LLM). It may report "not worth it" —
   that's the point.
4. `/airx:score`
   Grades memory **quality**: Coverage · Depth · Trust. A thin stub can win on token-% yet still score LOW.
5. `/airx:memtest <module>`
   The acceptance test: answer 5 real developer questions from the note **alone**, no grepping. Each
   "NOT IN MEMORY" is a gap to fill with `/airx:memory`. *(There is no `/airx:evidence` command yet —
   `memtest` is how you prove a note actually works.)*

## Full command surface
| Command | What it does |
|---|---|
| `/airx:init` | Stamp the project-memory layer into this repo. |
| `/airx:memory` | Create a verified, ticket-linked memory note for one module. |
| `/airx:memtest` | Prove a note works — answer real questions from memory alone. |
| `/airx:benchmark` | Prove the token/speed win on THIS repo, honestly. |
| `/airx:score` | Grade memory QUALITY (Coverage · Depth · Trust). |
| `/airx:validate` | Validate EXISTING memory — coverage, drift, freshness, discipline. |
| `/airx:check` | Conformance check — right shape, fresh, frontmatter-valid. |
| `/airx:purify` | Flag stale/dangling citations (never invents or deletes). |
| `/airx:refresh` | Re-verify memory against current code, report freshness. |
| `/airx:update` | After a ticket/change, update the affected module's note. |
| `/airx:enhance` | Fold what a commit changed into memory (verified additions only). |

## What to expect (honest caveats)
- **Memory needs ≥1 authored note to help.** Right after `init`, memory is empty — `benchmark`/`score`
  will look thin until you run `/airx:memory`.
- **Quality scales with coverage.** One note covers one module; numbers climb as you author more.
- **Judge by behavior + `score`, not token-% alone.** A TBD stub can score ~99% on tokens while covering
  one module of eight. Trust `memtest` behavior and the `score` grade over the token percentage.

## Troubleshooting
- **`/airx:*` commands don't show:** confirm `/plugin marketplace add .` + `/plugin install airx@airx`
  both succeeded; reopen Claude Code so commands reload.
- **`python3: command not found`:** install Python 3 (stdlib only — no pip needed) and ensure it's on PATH.
- **"not a git repo" / hook fails:** run `git init` first, or re-run `/airx:init --repo .` without
  `--install-hook`.
- **Wrong stack detected:** re-run with `/airx:init --repo . --stack <yourstack>`.
- **Don't want files in your tree (trial):** use `/airx:init --repo . --layout ignored` (or `sibling`).
