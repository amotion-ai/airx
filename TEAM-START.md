# Team start

How a team adopts airx without over-complicating it. Memory-first: capture the "why and what-changed"
the agent re-derives every session. Everything else (knowledge base, MCP, docs site) is optional and
added later, only if measurement says it pays.

## The whole loop (four steps)

```
1. Install (once):
   /plugin marketplace add amotion-ai/airx
   /plugin install airx@airx

2. In a repo:
   /airx:init <repo>        stamps ai_memory/ + AGENTS.md + CLAUDE.md beside the repo

3. Pick ONE hot module (the one your recent tickets actually touch):
   /airx:memory <module>    a dense, verified note: where the code is, the hot logic,
                            the tenant/scoping rule, and what changed and why (ticket-linked)

4. Work normally. After each ticket, append one line to that module's note:
   updated_date: <date> (<ticket>: what changed + the trap to avoid)
```

Start with one repo and one module. Add more modules as you touch them. That is the entire method.

## What you need vs do not need (to get started)

| Question | Answer |
|---|---|
| Identify the tech stack | Light: `/airx:init --stack <x>` just picks a seed for a head start. No detection tooling. |
| Identify load / size (tiers) | Skip. Tiers matter only for a full KB/docs build. Memory-first needs no sizing. |
| A crosswalk / migration step | Only if you already have divergent docs to align. Starting fresh: not needed. |
| More commands / levels | No. Four commands is plenty; most days you use init + memory. |
| An MCP server | No. MCP is only for the knowledge-base layer. Memory notes are plain markdown the agent reads. |
| A knowledge base | No, not to start. Add one later only if `/airx:benchmark` shows it beats grep on your repo. |
| A separate wiki tool (Obsidian/Confluence-style) | No. Memory lives as markdown in `ai_memory/` beside the repo. |
| Write custom skills | No. The plugin commands are the skills. |
| Human documentation site | Optional and separate; defer until people (not the agent) need onboarding docs. |

## How memory stays fresh

Two lightweight mechanisms, no machinery:

1. Habit (the important one): after each ticket, update the module note (`updated_date: ...`). Make it
   part of Definition-of-Done.
2. Nudge: the freshness hook warns when a note's `code_ref` no longer matches `HEAD`. The `kb-curator`
   subagent can re-check on demand.

## The rules that make it trustworthy

- Cite a real `file:line`, or write `TBD - needs human input`. Never invent a path, class, or method.
- Predict-and-verify tags: `[family]` (true of any repo in this archetype), `[verify]` (confirm against
  your code), `[fill]` (repo-specific, you fill it). A `[verify]`/`[fill]` line is a hypothesis until cited.
- Keep notes dense and scoped. Bulky context measurably hurts the agent.

## Get a head start

Copy the closest seed bundle from `seed-memory/` (e.g. `enterprise-java/` for a legacy
Spring-XML/JSF/Hibernate beanstack) into your repo's `ai_memory/_seed/`, then confirm each `[verify]`/`[fill]`
line against code before trusting it.

## When to add more (later, measured)

- Knowledge base + MCP: only when grep on a large repo is the real bottleneck, and `/airx:benchmark`
  proves the token win on that repo.
- Documentation site: only when human onboarding (not the agent) needs it.
- CI conformance gate: when several teams must stay aligned mechanically.
