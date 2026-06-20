---
description: Conformance check — is the wiki the right shape, fresh, and frontmatter-valid?
---

# /airx:check

Score the `<repo>-wiki/` against the airx standard and report drift. Deterministic; no LLM guessing.

## Run
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/check.py <wiki-dir>
```

Checks (memory-first):
- **manifest** — `.ai-readiness.yml` present.
- **structure** — `ai_memory/` **required** (MEMORY.md + ≥1 note); `ai_documentation/`/`ai_knowledge_base/` optional, noted if present.
- **frontmatter** — each note carries `name`, `owner`, `last_verified`, `code_ref`, `status`.
- **freshness** — `code_ref` vs `HEAD`; warn if stale.

Exit non-zero on FAIL so it can gate CI. Conformance PASS is *necessary but not sufficient* — the real
acceptance test is `/airx:benchmark` (the measured win) + human verification of [verify]/[fill] claims.
