# Team start

The steps are in **[docs/GETTING-STARTED.md](docs/GETTING-STARTED.md)** — install, `/airx:init`,
`/airx:memory`, work, `/airx:benchmark`. This page is just the **team-specific** bits on top.

## Make it a habit (the part that actually compounds)
- **Definition-of-Done:** after each ticket, append one line to that module's note —
  `updated_date: <date> (<ticket>: what changed + the trap to avoid)`. This is the highest-leverage habit.
- **One repo, one module to start.** Add modules as you touch them. Don't try to document everything.
- **Commit the memory** (`--layout in-repo`, the default) so the whole team — and every agent session —
  auto-loads it. Use `--layout ignored` if you want to trial it without touching the repo's history.

## Keep it fresh & trustworthy
- The freshness hook warns when a note's `code_ref` drifts from `HEAD`; `/airx:refresh` re-verifies.
- The rules that make it safe to trust: cite `file:line` or `TBD` (never invent); predict-and-verify
  (`[family]`/`[verify]`/`[fill]`); keep notes dense. A human approves every claim before it's written.

## When to add the optional layers (later, measured — not now)
- **`/airx:docs`** — when *people* (not the agent) need onboarding docs.
- **`/airx:kb`** — only when grep on a large repo is the real bottleneck **and** `/airx:benchmark` proves
  the token win. Needs a generator pack for your stack.
- **CI conformance gate** (`/airx:check` exit code) — when several teams must stay aligned mechanically.

Memory-first is the entire method to start. Everything else is opt-in, and only if measurement says it pays.
