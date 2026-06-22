---
description: Content-hygiene lint for memory notes — secret scan (gate) + emoji/hype/filler (advisory).
argument-hint: "[wiki-dir] (default: ./ or sibling wiki)"
---

# /airx:lint

Keep memory notes clean and honest. Deterministic, no LLM — complements `/airx:check` (citations resolve)
and `/airx:score` (coverage/depth) with the third leg: a note must be **clean** (no leaked secrets) and
**factual** (no marketing fluff or generic AI filler).

## Run
```bash
# report-only (what the post-commit hook runs — edits nothing):
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/lint_notes.py <wiki>

# strict (any warning also fails — for a CI gate):
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/lint_notes.py <wiki> --strict
```

## What it checks
- **SECRET — hard gate (exit 1):** private keys, AWS/GitHub/Slack/Google tokens, JWTs, DB URLs with an
  inline password, and `secret="…"`-style hardcoded assignments. Placeholders (`TBD`, `<…>`, `${ENV}`,
  `your-…`, `example`) are ignored. An agent that read code can paste a credential into a note — this stops
  it before the note lands. (Also gated inside `/airx:check`.)
- **EMOJI — warn:** decorative emoji (airx rule: no icons in markdown). airx's own functional markers
  (`⚠ STALE`, `✓`/`✗`/`→`) are allowed; only pictographic emoji flag.
- **HYPE — warn:** marketing adjectives (`blazing`, `seamless`, `world-class`, `leverage`, …) — a memory
  note is a fact sheet, not a brochure.
- **AIGEN — warn:** generic LLM filler (`it's important to note`, `plays a crucial role`, `delve into`, …)
  — enforces airx's "cite or TBD, no generic claims" rule.

## Then
Remove any secret immediately (and rotate it — it was in a file). Trim hype/filler to keep notes terse.
Adopt `--strict` in CI to make hygiene a gate, not just a nudge.
