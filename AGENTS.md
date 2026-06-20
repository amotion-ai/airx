# AGENTS.md — airx

> The cross-tool context file (read by Claude Code, Codex, Cursor, etc.). Terse on purpose: bulky or
> auto-generated context measurably *hurts*. This file describes how to work in **this** repo (airx itself).

## What airx is
A Claude Code plugin + portable method for **verified, measured project memory**. The differentiator is
discipline, not surface area: predict-and-verify, measure-don't-assume, govern with conformance.

## Working rules (apply to all contributors, human and agent)
- **Cite or `TBD`.** Every concrete claim about code carries a real `file:line`, or says `TBD — needs human input`. Never invent paths/classes/methods.
- **Predict-and-verify.** Seed content is tagged [family] family / [verify] verify / [fill] repo-specific. A [verify]/[fill] line is a hypothesis until confirmed against code.
- **Measure, don't assume.** Don't claim token/speed wins without `/airx:benchmark` on a real repo. Report honestly when it doesn't pay.
- **Terse beats bulky.** Keep docs and notes dense and scoped; sprawling context reduces agent performance.
- **Don't wrap the CLI.** Build on plugins / skills / MCP / the Agent SDK — not a fragile CLI shim.
- **Compose, don't clone.** Reuse existing memory MCPs for storage; airx adds verification + measurement + governance.

## Layout
`commands/` (slash commands) / `agents/` (subagents) / `hooks/` (freshness) / `docs/THESIS.md` (the method) /
`seed-memory/` (archetype head-start bundles) / `.claude-plugin/plugin.json` (manifest).

## Roadmap
`ROADMAP.md`. Phase 1 plugin -> Phase 2 conformance/benchmark CI gate -> Phase 3 community seeds.
