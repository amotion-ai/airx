---
description: Static, no-server viewer — browse memory/docs/KB in one self-contained HTML file (verification + score dashboard).
argument-hint: <wiki-dir>  (the airx wiki/repo with .ai-readiness.yml; defaults to the current repo)
---

# /airx:view

Generate a **static, no-server viewer** over whatever AI-readiness layers this wiki has — one
self-contained HTML file you open with a `file://` URL. No worker, no port (the roadmap's explicit
non-goal): it's a generated artifact you regenerate on demand.

The viewer's value is airx's **discipline made visible across layers**, not markdown prettiness:
- **per note** — the frontmatter card (status · last_verified · code_ref) + **citations resolved vs
  dangling** (green/amber) + TBD count;
- **across the wiki** — the **Coverage · Depth · Trust** headline + score trend;
- **KB** — registries (endpoints/entities/services) rendered as tables.

It **composes** the existing deterministic surface — `verify-citations.py` for per-note resolution and
`score.py` for the headline — rather than re-deriving either. Layers are **opt-in**: a section renders
only if that layer exists on disk; nothing is stamped empty.

## Run (deterministic — no LLM)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/view.py <wiki-dir>
```
`<wiki-dir>` is the airx wiki/repo containing `.ai-readiness.yml` (use `.` for the current repo). Writes
`<wiki>/ai_view.html` and adds it to `.gitignore` (it's a regenerable artifact). Open the printed
`file://` path in any browser — fully offline, zero JS, zero CDN.

## Rules
- **Regenerate, never hand-edit** the HTML — it's derived from your notes/docs/KB and the verifier.
- It **reflects** memory; it never authors or edits it. Run it anytime to see current state.
- Body text is shown raw on purpose — a confident-but-broken markdown render is worse than honest text;
  citations are highlighted and `TBD` gaps are flagged so the verification story reads at a glance.

## Next
- `/airx:score` · `/airx:benchmark` — the numbers behind the headline.
- `/airx:memory` — if the viewer shows thin coverage, document the next hot module.
