---
description: Grade project-memory QUALITY — Coverage · Depth · Trust (token-% is not quality).
argument-hint: "[wiki-dir] (default: ./ or sibling wiki)"
---

# /airx:score

Answer the question conformance and token-reduction can't: **is this memory actually good?** A thin TBD
stub can score ~99% on tokens yet cover one module of eight. `score` grades what matters and is calibrated
so deep hand-curated memory scores HIGH and a thin stub scores LOW.

## Run
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/score.py <wiki>
```

## What it reports (0–100 each → weighted OVERALL + grade)
- **Coverage** — notes vs detected code modules (is most of the codebase documented?).
- **Depth** — verified citations/note · ticket history · traps · low TBD-ratio. *(Auto-landed `to-enrich`
  symbol stubs are excluded — so auto-enhance can't game the score; depth rises only when a human adds the why.)*
- **Trust** — share of citations (file:line + class/query/bean) that still resolve.
- **OVERALL** = 0.45·Coverage + 0.35·Depth + 0.20·Trust, with an honest verdict (e.g. *"NOT DONE — only
  1/8 modules; 23% TBD; little ticket history"*).

Each run appends a line to `ai_memory/.cache/score-trend.tsv`, so the trend rising **over commits** (as the
self-improve loop runs) is provable. Pair with `/airx:check` (drift gate) and `/airx:benchmark` (token win).
