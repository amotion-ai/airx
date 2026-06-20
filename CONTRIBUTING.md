# Contributing to airx

Thanks for your interest. airx is early (Phase 1), so contributions, issues, and ideas are all welcome.

## Working rules

This repo follows [`AGENTS.md`](AGENTS.md) — read it first. The non-negotiables:

- **Cite `file:line` or say `TBD`.** Never state a repo-specific claim as fact without a real citation.
- **Predict-and-verify ([family]/[verify]/[fill]).** Mark confidence; verify before asserting.
- **Measure, don't assume.** No token/speed claims without `/airx:benchmark` on a real repo — and report honestly when it doesn't pay.
- **Terse beats bulky.** Dense, frontmattered notes over walls of prose.
- **Build on the supported surface** — plugins / skills / MCP / the Agent SDK. Never wrap the CLI. Compose existing tools; don't clone them.

## How to contribute

1. **Open an issue first** for anything non-trivial, so we can agree on shape before you build.
2. **Fork and branch** off `main` (e.g. `feat/...`, `fix/...`, `docs/...`).
3. **Keep changes focused.** One concern per PR.
4. **Check before you push:**
   - Python tools parse: `python3 -m py_compile tools/*.py`
   - JSON is valid: `python3 -c "import json; [json.load(open(f)) for f in ['.claude-plugin/plugin.json','.claude-plugin/marketplace.json','hooks/hooks.json']]"`
   - Hooks pass `bash -n hooks/*.sh`
   - Run `/airx:check` if your change touches memory/KB shape.
5. **Conventional commits** (`feat:`, `fix:`, `docs:`, `chore:`) — match the existing history.

## Reporting bugs

Open an issue with: what you ran, what you expected, what happened, and your environment (OS, Claude Code version). A minimal repro is worth a thousand words.

## License

By contributing, you agree your contributions are licensed under the [MIT License](LICENSE).
