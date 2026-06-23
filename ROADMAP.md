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
- [x] **Symbol-aware verification** — `verify-citations` resolves class / `queries.xml` name / bean id, not
      just `file:line` (symbol-first citation policy); HEAD-keyed index cache.
- [x] **Quality + drift scoring** — `/airx:score` (Coverage · Depth · Trust) + a `drift` dimension in
      `/airx:check`; token-% is reported but never mistaken for quality.
- [x] **Playbook delivery** — `/airx:validate` (Track A), `/airx:memory` (Track B stop-and-show),
      `/airx:memtest`; references the standard's domain seeds.
- [x] **Self-improving memory** — `/airx:purify`, `/airx:enhance`, `/airx:update` + a non-blocking
      `post-commit` hook (auto-purify safe/auto; enhance verified + human-in-loop; `auto_enhance` toggle).
- [ ] Ship predict-and-verify **seed bundles** beyond `enterprise-java` (e.g. spring-boot, flutter).
- [ ] Publish to a community marketplace.

## Phase 2 — Optional layers (added progressively, each measured)
- [x] `/airx:docs` — **minimal** scaffold of `ai_documentation/` templates on demand (v0.1; depth grows).
- [x] `/airx:kb` — **minimal** deterministic Java registry generator (endpoints/entities/services). Graphs +
      more per-stack packs + optional MCP query layer still to come.
- [x] `/airx:view` — static, **no-server** viewer over memory/docs/KB (one self-contained HTML file;
      a verification + Coverage·Depth·Trust dashboard, not a worker/port).
- [ ] Progressive-disclosure retrieval (index-first, fetch-on-demand) — **gated on multi-note coverage**
      (on 1-note repos the agent already self-routes; only pays off at scale). `<private>` exclusion tags.
- [ ] Conformance + benchmark + score as a headless **CI gate** ("measured AI-readiness in CI").

## Phase 3 — Ecosystem
- [ ] **Multi-tool support — Cursor, Codex, and more (coming soon).** The output is already cross-tool:
      memory writes `AGENTS.md` (the shared standard) and the deterministic surface is stdlib-only Python
      with no Claude-Code dependency. What's Claude-Code-specific today is the *command packaging*
      (`/airx:*` slash commands / plugin manifest); the plan is first-class integration for other coding
      agents so the same verified-memory loop runs natively wherever you work.
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
