---
description: Scaffold the human-documentation layer (ai_documentation/) — narrative docs for engineers & on-call, opt-in and distinct from agent memory.
argument-hint: <wiki-dir>  (the airx wiki/repo with .ai-readiness.yml; defaults to the current repo)
---

# /airx:docs

Scaffold **human-narrative documentation** for this repo — the opt-in docs layer (Pillar 1). These are
written to be **read sequentially** by people (engineers, on-call, new joiners), and are deliberately
**distinct from `ai_memory/`** (dense agent context, queried not read). Memory is the universal entry
layer; docs are added only if you want them.

## Run (deterministic part)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/docs_init.py <wiki-dir>
```
`<wiki-dir>` is the airx wiki/repo containing `.ai-readiness.yml` (use `.` for the current repo). The
script reads `target.code_ref` from the manifest and stamps `ai_documentation/` with a README index plus
a SUBSET of the universal doc catalog: `ARCHITECTURE.md`, `MULTI-TENANCY.md`, `SECURITY.md`,
`DATABASE.md`, `TROUBLESHOOTING.md`, `CONFIGURATION-REFERENCE.md`. Each is a skeleton — YAML frontmatter
(`status: LIVING`), section headers, and `TBD` placeholders. It is **idempotent**: if `ai_documentation/`
already exists and is non-empty, it leaves your filled docs untouched.

## Then fill them (the actual work)
The scaffold is empty on purpose. Fill each doc with **cited** content:
1. Pick a doc.
2. Source each claim from the code (`/airx:memory`-style — read the code, then anchor the claim).
3. Replace `TBD` with prose that cites a real **`file:line`**. Where you cannot verify a claim, leave
   `TBD — needs human input`. **Never invent** paths, class names, or method signatures.
4. When a human has confirmed a doc against the code, set its `last_verified` date.

Rule (applies to every doc): cite `file:line` or say `TBD`. A confident-sounding guess is worse than `TBD`.
