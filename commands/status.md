---
description: Memory dashboard — where am I / what to do next (layers · coverage · trust · token win · NEXT action).
argument-hint: <wiki-dir>  (the airx wiki/repo with .ai-readiness.yml; defaults to the current repo)
---

# /airx:status

The one "where am I / what do I do next" readout for an airx wiki — the self-driving heart of the memory
loop. Run it anytime to see what's covered and the single highest-leverage next step.

## Run (deterministic — no LLM)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/status.py <wiki-dir>
```
It composes the existing surface (module ranking + `verify-citations` + the benchmark result — never
re-derives) and reports:
- **Layers** present (memory always; docs/KB/viewer only if they exist — never pushed).
- **Memory coverage** — modules with a note vs detected modules, + authored note count.
- **Trust** — how many citations resolve.
- **Token win** — `memory_reduction_vs_bare` once `/airx:benchmark` has run, else "not measured".
- **NEXT** — the single best next action (author the hottest uncovered module → `/airx:memory <m>`;
  else `/airx:benchmark` / keep fresh).

Writes `.airx/STATUS.md` (a regenerable dashboard) and prints the same.

## The loop it drives (memory-first)
`/airx:init` → **`/airx:status`** (what next?) → `/airx:memory <module>` (author the NEXT note) →
`/airx:benchmark` · `/airx:score` (prove it) → repeat until coverage is complete, then `/airx:update`
after tickets. KB/docs/viewer are opt-in side-quests, justified only when they pay (`/airx:benchmark`).
