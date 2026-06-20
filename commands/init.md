---
description: Stamp the memory-first AI-readiness skeleton into this repo (ai_memory/ + AGENTS.md + CLAUDE.md).
---

# /airx:init

Set up a repo for verified project memory, memory-first (no KB unless measurement later justifies it).

Steps:
1. Detect the stack (look for build files, framework markers) and confirm with the user.
2. Create a sibling `<repo>-wiki/` (never inside the client git tree) with `ai_memory/`
   (`MEMORY.md` + `_project_TEMPLATE.md` + `_reference_TEMPLATE.md`), plus `AGENTS.md` and `CLAUDE.md`.
3. Drop in the closest **seed-memory** bundle under `ai_memory/_seed/` (predict-and-verify; tagged 🟢/🟡/🔴).
4. Write `.ai-readiness.yml` pinning the standard version + `code_ref` (current `git rev-parse HEAD`).
5. Tell the user the next step is `/airx:memory` on one hot module.

## Run (deterministic part)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/init.py --repo <path-to-code-repo> [--stack S] [--domain D]
```
This stamps `ai_memory/` + `AGENTS.md` + `CLAUDE.md` + `.ai-readiness.yml` (memory-first; no KB/docs).
Then proceed with `/airx:memory` to fill the first note.

Rules: every concrete claim cites a real `file:line` or says `TBD — needs human input`. Never invent paths.
