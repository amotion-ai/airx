---
description: Prove the token/speed win on THIS repo — honestly (it may report "not worth it").
---

# /airx:benchmark

Measure what the memory/KB actually buys *on this repo* — the honest core of airx.

## Run (once a KB exists; memory-first repos add one only if this proves it pays)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/benchmark.py <wiki-dir>
```
Reads `<wiki>/ai_knowledge_base/benchmark.json` (your real questions); writes `results/token-reduction.json`.

Method (deterministic, token ≈ chars/4, no LLM):
- For ~6 **real** developer questions, compute tokens three ways: **bare** (grep the repo),
  **kb_mcp** (query the index -> matching items), **kb_files** (load the whole registry).
- Verifiers come from **source, never the index** (don't grade the index against itself).
- Report per-question + totals; write `results/token-reduction.json`; feed `MEASUREMENT-SCORECARD.md`.

Honest reads built in: precise lookups win big; broad/conceptual queries win little; on small/modern
repos a KB can cost *more* than grep. **If it doesn't pay, airx says so** — then you stay memory-only.

> Memory's win is *speed + fewer re-investigations* (measure via with/without-memory A/B + correctness),
> not per-query token cuts. The KB is the per-query token lever — and only where this benchmark proves it.
