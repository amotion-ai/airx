---
description: Prove a memory note works — answer real questions from memory ALONE, no grepping (P-MEMTEST).
argument-hint: "[module] (the note to test)"
---

# /airx:memtest [module]

The acceptance test for a memory note: can the agent answer real developer questions using **only** the
note (and the spine docs it links), without reading source? This is how you know memory will actually save
the cold-grep tokens in the ADLC loop instead of the agent re-deriving anyway.

## Steps
1. Load `ai_memory/reference_<module>.md` (and only the spine notes it links). **Do not grep the source
   tree during the test.**
2. Answer 5 **real** questions a developer asks about this module — not toy questions. Include at least:
   - one "where is X" lookup, one geo-variant (e.g. PH/MY) question, one "add-a-field / change impact"
     question, one "what did ticket <ID> change", and one business-rule/status-code question.
   - Cite the class / method / query / table **from the note** for each answer.
3. If the note lacks an answer, say **"NOT IN MEMORY"** — do not fall back to grep. Each "NOT IN MEMORY"
   is a gap to fix via `/airx:memory`.
4. Report: how many of 5 answered from memory alone, and the gap list.

> Pair with `python3 "${CLAUDE_PLUGIN_ROOT}"/tools/benchmark.py <wiki>` to put a token number on the win
> (note vs cold grep), and `/airx:check` to confirm the cited symbols actually resolve.
