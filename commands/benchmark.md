---
description: Prove the token/speed win on THIS repo — honestly (it may report "not worth it").
---

# /airx:benchmark

Measure what the memory/KB actually buys *on this repo* — the honest core of airx.

## Run (memory-first repos can run this with no KB — see the memory arm below)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/benchmark.py <wiki-dir>
```
Reads `<wiki>/ai_knowledge_base/benchmark.json` (your real questions); writes `results/token-reduction.json`.

Method (deterministic, token ≈ chars/4, no LLM):
- For ~6 **real** developer questions, compute tokens up to four ways: **bare** (grep the repo — the
  cold path), **memory** (load the verified note that answers it), **kb_mcp** (query the index ->
  matching items), **kb_files** (load the whole registry).
- Per question, `measure` may carry `grep_term`, `registry` (KB arm), and/or `memory_note` (memory
  arm, resolved under `ai_memory/`). **Memory-first repos run this with only `grep_term` +
  `memory_note` — no KB needed.**
- Verifiers come from **source, never the index** (don't grade the index against itself).
- Report per-question + totals; write `results/token-reduction.json`.

Honest reads built in: precise lookups win big; broad/conceptual queries win little; on small/modern
repos a KB can cost *more* than grep. **If it doesn't pay, airx says so** — then you stay memory-only.

> **Memory win** = `(bare − memory) / bare`: tokens saved by loading one verified note instead of
> re-deriving the answer from the repo. **KB win** = `(kb_files − kb_mcp) / kb_files`: the per-query
> index lever, justified only where this benchmark proves it.
