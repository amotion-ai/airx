# Changelog

All notable changes to airx. Versions follow [SemVer](https://semver.org/).

## [Unreleased]

### Changed — agent flow
- **Memory state now reaches the agent.** Before, the PostToolUse freshness warning went to stderr with exit 0,
  so Claude Code never showed it to the model. It also looked for the manifest at the wiki root, so it never
  fired on `.airx/` installs. It's replaced by `tools/agent_hooks.py`:
  - **SessionStart** (`startup|resume|clear|compact`) prints the router path, the note count, the pending
    worklist size, and which notes had code change under them since their `code_ref`. "Under them" means
    in a directory named for the module, or in a file the note cites. Commit count alone would flag every
    note in an active repo. It runs no citation scan: ~100 ms on a 1.3k-file repo.
  - **PostToolUse(Write|Edit)** citation-checks a memory note the moment it's written and returns
    `additionalContext` listing dangling `file:line` and unresolved symbols. Drafts, code edits, and clean
    notes produce no output. Non-memory edits exit in ~65 ms. A note write takes ~0.3 s with the symbol
    index cached, and ~9 s on the first write after a new HEAD (1.3k files). Timeout is 60 s.
    Uncommitted classes are overlaid on the HEAD-keyed index, so a note citing code the agent just wrote
    isn't flagged.
- **`kb-curator`** now runs `check` / `verify-citations` / `purify` / `memdiff` instead of re-deriving them,
  knows the `.airx/` layout, follows symbol-first citations, and pins `model: sonnet`, `effort: medium`.
- **New `memtest-examiner` subagent.** `/airx:memtest` delegates to it. It runs in a fresh context with only
  Read/Glob, so recall is tested without the author's source knowledge leaking in.

### Fixed
- `post-commit.sh` didn't find `.airx/` manifests, and its memory-only-commit skip matched only
  `ai_memory/`. On `.airx/` installs it could loop commit → scan → commit.
- The `.airx-hooks/post-commit` shim checks that the plugin's `post-commit.sh` exists before calling it.
  The shim stores an absolute path, which a plugin update or a teammate's clone can invalidate.
- Command docs (`check`, `refresh`, `validate`, `memtest`, `update`, `enhance`, `draft`, `benchmark`,
  `score`, `init`) and README/quickstart now point at `.airx/ai_memory/` and `.airx/.ai-readiness.yml`.

### Added
- `tests/test_agent_hooks.py`: a hermetic test covering both hooks, in-repo and sibling layouts, and the
  post-commit skip.

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
