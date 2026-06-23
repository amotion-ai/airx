# Changelog

All notable changes to airx. Versions follow [SemVer](https://semver.org/).

## [0.0.1] — 2026-06-23

First public release — re-baselined to `0.0.1` (the prior `v0.1.0` tag was premature and has been
retired). airx is a Claude Code plugin for **progressive AI-readiness**: verified, measured project
memory for coding agents, with optional docs / KB / viewer layers.

### Added
- **Memory loop** — `/airx:init`, `/airx:draft`, `/airx:memory`, `/airx:validate`, `/airx:check`,
  `/airx:score`, `/airx:benchmark`, `/airx:evidence`, `/airx:memtest`, `/airx:refresh`.
- **Self-improving memory** — `/airx:purify`, `/airx:enhance`, `/airx:update` + a non-blocking
  `post-commit` hook (auto-purify stale citations, build an enhancement worklist; zero model tokens).
- **Symbol-aware verification** — `verify-citations` resolves `file:line` **and** durable symbols
  (class / `queries.xml` name / bean id), with a HEAD-keyed index cache.
- **Quality + drift scoring** — `/airx:score` (Coverage · Depth · Trust) and a drift gate in
  `/airx:check` (dangling `file:line` → hard FAIL).
- **Optional layers** — `/airx:docs` (human-narrative scaffold), `/airx:kb` (deterministic Java
  registries), and **`/airx:view`** — a static, no-server HTML viewer over memory/docs/KB (a
  verification + Coverage·Depth·Trust dashboard; renders only the layers that exist).
- Stdlib-only deterministic tools (no servers, no embeddings); `enterprise-java` seed bundle.

### Notes
- `airx` is a **working name** and may change before a stable release.
- Behavioral evidence is **n=1** so far (one blind A/B on a real Spring Boot repo) — field reports welcome.
