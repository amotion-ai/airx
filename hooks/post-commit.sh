#!/usr/bin/env bash
# airx post-commit — self-improve loop, scoped to the just-made commit. NON-BLOCKING, REPORT-ONLY.
# Installed via `git config core.hooksPath .airx-hooks/` (see init.py). Safe no-op without an airx wiki.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"          # airx plugin root (hooks/..)
REPO="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# locate the wiki: in-repo, else sibling <repo>-wiki. Manifest lives in .airx/ (legacy: wiki root).
is_wiki() { [ -f "$1/.airx/.ai-readiness.yml" ] || [ -f "$1/.ai-readiness.yml" ]; }
WIKI="$REPO"
is_wiki "$WIKI" || WIKI="$(dirname "$REPO")/$(basename "$REPO")-wiki"
is_wiki "$WIKI" || exit 0                                        # no airx → no-op

# skip merge commits (HEAD~1 ambiguous)
[ "$(git -C "$REPO" rev-list --parents -n1 HEAD | wc -w)" -gt 2 ] && exit 0
# skip commits that only touched memory (no code → nothing to learn; avoids commit→enhance→commit loop)
CHANGED="$(git -C "$REPO" diff --name-only HEAD~1..HEAD 2>/dev/null || true)"
echo "$CHANGED" | grep -qvE '^(\.airx/|ai_memory/|\.airx-hooks/)' || exit 0

# run analysis in the BACKGROUND so the commit returns instantly; report-only (never edits notes)
(
  python3 "$ROOT/tools/purify.py"    "$WIKI" >/dev/null 2>&1 || true
  python3 "$ROOT/tools/memdiff.py"   "$WIKI" >/dev/null 2>&1 || true
  python3 "$ROOT/tools/score.py"     "$WIKI" >/dev/null 2>&1 || true
  python3 "$ROOT/tools/lint_notes.py" "$WIKI" >/dev/null 2>&1 || true   # report-only hygiene/secret scan
) </dev/null >/dev/null 2>&1 &

echo "airx: scanning commit for memory drift in background → .airx/ai_memory/PENDING-ENHANCEMENTS.md (then /airx:enhance)" >&2
exit 0
