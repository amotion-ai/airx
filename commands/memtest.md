---
description: Prove a memory note works — answer real questions from memory ALONE, no grepping (P-MEMTEST).
argument-hint: "[module] (the note to test)"
---

# /airx:memtest [module]

The acceptance test for a memory note: can the agent answer real developer questions using **only** the
note (and the spine docs it links), without reading source? This is how you know memory will actually save
the cold-grep tokens in the ADLC loop instead of the agent re-deriving anyway.

## Steps
1. **Write the 5 questions** a developer actually asks about this module. Don't use toy questions. Include
   a "where is X", a geo-variant (e.g. PH/MY), an "add-a-field / change impact", a "what did ticket <ID>
   change", and a business-rule/status-code question. The user can supply or edit them.
2. **Delegate to the `memtest-examiner` subagent**, passing the module, the note path
   (`.airx/ai_memory/reference_<module>.md`), and the 5 questions. It runs in a **fresh context with only
   Read/Glob and no Grep or Bash**. That makes the test blind: you (the author) have just read the code,
   so if you answered yourself, source knowledge would leak into a "from memory alone" score.
3. Relay its `N/5` line and `GAPS`. Each `NOT IN MEMORY` is a gap to close with `/airx:memory` or
   `/airx:update`.

> Pair with `python3 "${CLAUDE_PLUGIN_ROOT}"/tools/benchmark.py <wiki>` to put a token number on the win
> (note vs cold grep), and `/airx:check` to confirm the cited symbols actually resolve.
