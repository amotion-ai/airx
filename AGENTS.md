# AGENTS.md — airx

> The cross-tool context file (read by Claude Code, Codex, Cursor, etc.). Terse on purpose: bulky or
> auto-generated context measurably *hurts*. This file describes how to work in **this** repo (airx itself).

## What airx is
A Claude Code plugin for **progressive AI-readiness**: start with verified, measured **project memory**,
then opt into documentation, a knowledge base, and a viewer — each layer verified and measured, never
forced (memory-first by default). The differentiator is discipline, not surface area: predict-and-verify,
measure-don't-assume, govern with conformance.

## Working rules (apply to all contributors, human and agent)
- **Cite or `TBD` (symbol-first).** Every concrete claim about code carries a real anchor — `file:line` **or** a durable symbol (class / method / `queries.xml` name / bean id / table) — or says `TBD — needs human input`. Symbols are preferred (they survive churn in large files and are verified mechanically by `tools/verify-citations.py`). Never invent paths/classes/methods.
- **Predict-and-verify.** Seed content is tagged [family] family / [verify] verify / [fill] repo-specific. A [verify]/[fill] line is a hypothesis until confirmed against code.
- **Measure, don't assume.** Don't claim token/speed wins without `/airx:benchmark` on a real repo. Report honestly when it doesn't pay.
- **Terse beats bulky.** Keep docs and notes dense and scoped; sprawling context reduces agent performance.
- **Don't wrap the CLI.** Build on plugins / skills / MCP / the Agent SDK — not a fragile CLI shim.
- **Compose, don't clone.** Reuse existing memory MCPs for storage; airx adds verification + measurement + governance.

## Layout
`commands/` (slash commands: init · memory · draft · validate · check · score · benchmark · evidence ·
memtest · purify · enhance · update · refresh · docs · kb · view) / `tools/` (deterministic, stdlib:
init · verify-citations [symbol-aware] · check · score · benchmark · evidence · purify · memdiff ·
extract · seed_apply · docs_init · kb_registry · view) / `agents/` (subagents) / `hooks/` (freshness +
`post-commit.sh` self-improve) / `docs/THESIS.md` (method) · `docs/BETA-EVIDENCE.md` (blind A/B proof) /
`BETA-QUICKSTART.md` (first-run) / `seed-memory/` (archetype bundles) / `.claude-plugin/plugin.json`.

## Roadmap
`ROADMAP.md`. Memory layer (now) -> optional layers `/airx:docs`, `/airx:kb` (per-stack), `/airx:view`
(progressive, each measured) -> ecosystem. Memory-first; nothing heavier forced or stamped empty by default.
