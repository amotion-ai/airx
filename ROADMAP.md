# Roadmap

airx ships the layer the crowded memory/KB space lacks: **verification + measurement + governance.**
Build on Claude Code's official surface (plugins / skills / MCP / Agent SDK) — never a CLI wrapper.

## Phase 0 — Proof (in progress)
- A real case study: memory-first on a live legacy repo, with the measured speed/token delta.
  Evidence sells an honest tool more than features do.

## Phase 1 — Plugin MVP (this repo)
- [x] Plugin skeleton: `/airx:init`, `/airx:memory`, `/airx:check`, `/airx:benchmark`, `kb-curator`, freshness hook.
- [ ] Validate `.claude-plugin/plugin.json` against the current Claude Code plugin spec.
- [ ] Wire the commands to real, deterministic implementations (scaffold / conformance / benchmark).
- [ ] Ship 3 predict-and-verify **seed bundles** (enterprise-java, spring-boot, flutter).
- [ ] Publish to a community marketplace.

## Phase 2 — Verification harness (the moat)
- [ ] Conformance + benchmark as a headless **Agent-SDK / CI gate** ("measured AI-readiness in CI").
- [ ] `AGENTS.md` cross-tool support so it isn't Claude-only.
- [ ] Brownfield **alignment** (crosswalk + frontmatter normalizer) to migrate existing divergent wikis.

## Phase 3 — Community network effect
- [ ] Open seed-bundle contributions per stack/domain.
- [ ] Compose (not clone) existing memory MCPs for storage backends.

## Non-goals
- Not a CLI wrapper (fragile / ToS risk). Not another memory store or KB-graph clone (saturated).
- Not a 30-command mega-framework — terse beats bulky; the edge is discipline, not surface area.
