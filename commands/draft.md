---
description: Auto-DRAFT a CANDIDATE memory stub of code-derived facts to accelerate /airx:memory (UNVERIFIED — the human verifies).
argument-hint: "[module] (optional — picks the hottest undocumented module if omitted)"
---

# /airx:draft [module]

Run the deterministic auto-extractor to produce an **UNVERIFIED draft** scaffold for a module — a head
start for `/airx:memory`, **not** a finished note. This is the "AI fills the memory" half done the
verify-first way: code-derived facts are emitted as `[verify]` hypotheses; intent (why / what-changed /
traps) is left `TBD` because **code cannot source intent**. Nothing here is asserted as truth.

## Run
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/extract.py <wiki> [module]
```
- With a module name → drafts that module.
- Without one → picks the **hottest undocumented** module (git-churn ranked; skips ones that already
  have `reference_<module>.md`).

## What it writes
`ai_memory/_draft_<module>.md` — a CANDIDATE stub:
- frontmatter `status: DRAFT`, `last_verified: TBD`;
- a big banner: *DRAFT — auto-extracted, UNVERIFIED*;
- mirrors the 11 `reference_` sections;
- code-derived facts tagged `[verify]` — class names + annotations (`@RestController`/`@Service`/
  `@Component`/`@Entity`…), public method signatures, named-query names under the module, `@Table`
  hints, and ticket IDs from the module's git log;
- intent sections left `TBD — needs human input`.

> The filename starts with `_`, so airx's existing tools (`/airx:check`, `/airx:score`,
> verify-citations) **do NOT count it as a real note**. It is scaffolding, not memory.

## Then — the human verifies (this is the point)
The draft is a hypothesis list, never truth. Run `/airx:memory <module>`: confirm each `[verify]` line
against the code (cite `file:line` or a durable symbol), fill the `TBD` intent sections from tickets /
team knowledge, then **rename** `_draft_<module>.md` → `reference_<module>.md`. Verify with
`/airx:check` and prove recall with `/airx:memtest`.
