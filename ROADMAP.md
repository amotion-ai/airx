# Roadmap

airx is **progressive AI-readiness**: a simple plugin that starts with verified project memory and grows,
by the user's choice, into richer layers — documentation, knowledge base, viewer. The through-line on every
layer is the thing the crowded memory/KB space lacks: **verification + measurement + governance.** Build on
Claude Code's official surface (plugins / skills / MCP / Agent SDK) — never a CLI wrapper.

## The progressive layer model
1. **Project memory** (shipping) — `/airx:init` + `/airx:memory`. Universal; the day-1 token win; no stack pack needed.
2. **Documentation** (`/airx:docs`) — human onboarding narrative. Opt-in.
3. **Knowledge base** (`/airx:kb`) — deterministic registries + JSON graphs; the per-query token lever;
   needs a per-stack generator pack; justified by `/airx:benchmark`. Opt-in.
4. **Viewer** (`/airx:view`) — static browse/explore over whatever layers exist. Opt-in.

## Phase 0 — Proof (in progress)
- A real case study: memory-first on a live legacy repo, with the measured speed/token delta.
  Evidence sells an honest tool more than features do.

## Phase 1 — Memory plugin (this repo, shipping)
- [x] Commands: `/airx:init`, `/airx:memory`, `/airx:check`, `/airx:refresh`, `/airx:benchmark`; `kb-curator`; freshness hook.
- [x] In-repo default + root `CLAUDE.md`/`AGENTS.md` so the agent auto-loads memory.
- [x] Memory-only footprint + candidate-module discovery + propose→verify→approve control harness.
- [ ] Ship predict-and-verify **seed bundles** beyond `enterprise-java` (e.g. spring-boot, flutter).
- [ ] Publish to a community marketplace.

## Phase 2 — Optional layers (added progressively, each measured)
- [ ] `/airx:docs` — scaffold `ai_documentation/` templates on demand.
- [ ] `/airx:kb` — generic KB core (registries + graphs) + first per-stack generator pack
      (`java-primefaces-hibernate`; a `java-quarkus-jaxrs-spi` pack for modern Java). Optional MCP query layer.
- [ ] `/airx:view` — static viewer over memory/docs/KB.
- [ ] Conformance + benchmark as a headless **CI gate** ("measured AI-readiness in CI").

## Phase 3 — Ecosystem
- [ ] Open seed-bundle + stack-pack contributions per stack/domain.
- [ ] Compose (not clone) existing memory MCPs for storage backends.
- [ ] Brownfield **alignment** (crosswalk + frontmatter normalizer) to migrate existing divergent wikis.

## Non-goals (progressive, not bloated)
- Not a CLI wrapper (fragile / ToS risk).
- **No layer is forced or stamped empty by default** — memory is the entry; docs/KB/viewer are opt-in,
  each justified by need or measurement. The repo may hold all the machinery; a user's footprint is only
  what they choose.
- Not a vector-RAG-by-default store — the KB is **deterministic** registries/graphs (vector search is an
  opt-in extra), and airx ships **generators**, never a pile of generated output.
- Terse beats bulky — the edge is discipline (verified + measured), not surface area.
