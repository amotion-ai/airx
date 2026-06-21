---
description: Flag stale/dangling citations in memory notes (safe — never invents or deletes).
argument-hint: "[wiki-dir] (default: ./ or sibling wiki)"
---

# /airx:purify

Keep memory honest: find citations that no longer resolve and flag them for re-verification. **Safe by
construction** — it never invents a fix and never deletes a claim; it only marks what's stale.

## Run
```bash
# report-only (what the post-commit hook runs — edits nothing):
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/purify.py <wiki>

# apply inline flags (human reviews the diff):
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/purify.py <wiki> --apply
```
`--apply` appends `⚠️ STALE — re-verify` to each line with a dangling `file:line` citation and stamps
`needs_review: <date>` in frontmatter. If the repo can't be found it refuses (won't mass-flag).

## Then
Review the flagged lines and either re-verify against current code (fix the citation) or run
`/airx:enhance` to fold the fixes in. Symbol-level drift (class/query/bean) shows as the `drift` rate in
`/airx:check`.
