---
description: Stamp the project-memory layer into this repo (ai_memory/ + root CLAUDE.md/AGENTS.md), and show what you can add later.
---

# /airx:init

Set up a repo for verified project memory. **Progressive: this stamps the memory layer only** — docs, a
knowledge base, and a viewer are optional layers you add later (and measure) *if you want them*.

Steps:
1. Detect the stack (build files / framework markers) and confirm with the user.
2. Stamp the **memory layer**: `ai_memory/` (`MEMORY.md` + `_reference_TEMPLATE.md` + `_project_TEMPLATE.md`),
   plus `CLAUDE.md` + `AGENTS.md` + `.ai-readiness.yml`. **Default `--layout in-repo`** puts `CLAUDE.md`/
   `AGENTS.md` at the **repo root** so the agent auto-loads memory every session. (An existing root
   `CLAUDE.md`/`AGENTS.md` is never clobbered — airx appends an idempotent block.)
3. `MEMORY.md` is seeded with **candidate modules** detected from repo structure, so the user sees where
   to start without knowing the module map.
4. Tell the user the next step is `/airx:memory` (it proposes the hottest modules) — and the optional
   layers (`/airx:docs`, `/airx:kb`, `/airx:view`).

## Run (deterministic part)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/init.py --repo <path-to-code-repo> \
    [--layout in-repo|sibling|ignored] [--stack S] [--domain D]
```
- `in-repo` (default): files inside the repo; agent auto-loads memory. Commit them to share with the team.
- `sibling`: everything in `../<repo>-wiki/` (keeps the git tree untouched; agent won't auto-load).
- `ignored`: in-repo but added to `.gitignore` (local-only trial).

Memory-first by design: **no `ai_documentation/` or `ai_knowledge_base/` folders are created** until you
opt in. Then proceed with `/airx:memory`.

Rules: every concrete claim cites a real `file:line` or says `TBD — needs human input`. Never invent paths.
