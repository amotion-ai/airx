---
description: Validate EXISTING project memory — coverage, drift, freshness, discipline (Track A of the playbook).
argument-hint: "[wiki-or-memory-dir] (default: ./ai_memory or the sibling wiki)"
---

# /airx:validate

**Track A (Validate)** of the AI-Readiness playbook: score memory that already exists and produce a
prioritized remediation list. Use this on a repo that *has* memory/KB (the common case for adopted repos).
Mechanical checks do the heavy lifting; the agent judges meaning. **Stale memory that reads as current is
worse than none — this audit is the point.**

## 0 · Detect & locate
Find the memory dir (arg, `./ai_memory`, or sibling `*-wiki/ai_memory`). Read `.ai-readiness.yml` for
`stack`/`domain`. If **ai-readiness-standard** is available, load `domains/<domain>/` (MODULE-MAP +
SEED-*) as the **coverage rubric**.

## 1 · Mechanical backbone (run these first — deterministic, cheap)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/verify-citations.py <wiki>   # symbol-aware: file:line + class/query/bean
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/check.py <wiki>             # structure/frontmatter/freshness/citations/DRIFT
```
The `drift` line (symbol resolution rate) and any dangling `file:line` are your accuracy signal — quote them.

## 2 · The four dimensions (score each 0–5)
- **Coverage** — modules present in code (grep base package) but with NO note; notes for things no longer
  in code (orphans). Cite evidence for each "in code, undocumented." Use the seed's MODULE-MAP as expected set.
- **Drift / accuracy** — from `verify-citations`: which class/method/query/table claims no longer resolve.
  Sample ≥20 concrete claims; mark ✅ true / ⚠️ moved / ❌ gone, with evidence. Report the drift rate.
- **Freshness** — each note's `last_verified`/`code_ref` vs current HEAD; how many commits behind. Notes
  with no anchor at all = treat as stale.
- **Discipline** — concrete claims anchored (not "in the service layer")? business meaning labelled vs
  asserted as code fact? geo-variant claims verified in `queries.xml`? frontmatter complete? `MEMORY.md`
  index matches files on disk (no dead links/orphans)?

## 3 · Report
Write `<wiki>/VALIDATION-REPORT.md`: the four 0–5 scores, the **top-10 prioritized actions** (highest risk
first — which notes to re-verify, which modules to create, which stale claims to fix), and a one-paragraph
verdict: *is this memory trustworthy for an AI to act on today?* Every action names a note/module + cites
evidence. For MISSING modules, hand off to `/airx:memory`; for stale notes, hand off to `/airx:update`.
