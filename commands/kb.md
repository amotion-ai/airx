---
description: Opt-in KB layer — generate deterministic Java registries (endpoints/entities/services) as the per-stack token-lever.
---

# /airx:kb

Build the **knowledge-base layer**: deterministic registries of your code's symbols, so the agent can
answer "where is X / what endpoints exist / which entity maps to which table" by loading a tiny indexed
slice instead of grepping the whole repo. This is the **per-stack token-lever** (Java/Spring for now).

**Opt-in and measured.** Memory is the universal layer; the KB is heavier and only pays off on some
repos. Generate it, then **prove the win on THIS repo with `/airx:benchmark`** (KB win = tokens to query
the index vs. load the whole registry / grep the source). If it doesn't pay, stay memory-only.

## Run (deterministic — no LLM)
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/kb_registry.py <wiki-dir>
```
Reads `<wiki>/.ai-readiness.yml` for `target.repo_path` (resolved relative to the wiki) and
`target.code_ref`. Walks the target repo's `*.java` files once (skipping `build/`/`target/`/`.git/`/
`node_modules/`) and writes `<wiki>/ai_knowledge_base/registry/`:

- `endpoints.json` — `@RestController`/`@Controller` classes + their `@GetMapping`/`@PostMapping`/
  `@RequestMapping`/`@*Mapping` paths (class · HTTP method · path · file).
- `entities.json` — `@Entity` classes (class · `@Table` name · file).
- `services.json` — `@Service`/`@Component` beans (bean id if declared · class · file).

Each file is a JSON envelope: `{"_meta": {generated, code_ref, generator: "airx kb_registry",
source: "auto-generated", count}, "<items>": [...]}`.

## Rules
- **Deterministic: regenerate, never hand-edit.** If a registry is wrong, fix the script and re-run —
  a manual edit is lost on the next regen (and `/airx:check` flags it).
- The registries are generated artifacts (`code_ref` ties them to the commit they were extracted from).
- Java-only today; memory works on ANY stack, so a missing KB pack is never a blocker.

## Next
- `/airx:benchmark` — prove (honestly) whether the KB lever pays off on this repo.
- `/airx:view` — browse what you've built (static, no-server HTML over memory/docs/KB).
