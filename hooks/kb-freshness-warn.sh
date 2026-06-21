#!/usr/bin/env bash
# PostToolUse hook: after a code edit, warn if project memory / KB lags the working tree.
# Stamped by airx; safe no-op when the manifest or git is absent.
set -euo pipefail

MANIFEST=".ai-readiness.yml"
[ -f "$MANIFEST" ] || MANIFEST="../$(basename "$PWD")-wiki/.ai-readiness.yml"
[ -f "$MANIFEST" ] || exit 0

CODE_REF=$(grep -m1 'code_ref:' "$MANIFEST" | sed -E 's/.*code_ref:[[:space:]]*([^[:space:]]+).*/\1/' || true)
HEAD_REF=$(git rev-parse --short HEAD 2>/dev/null || echo unknown)

if [ -n "${CODE_REF:-}" ] && [ "$CODE_REF" != "TBD" ] && [ "$CODE_REF" != "$HEAD_REF" ]; then
  echo "airx: memory verified at $CODE_REF; repo HEAD is $HEAD_REF - may be stale. Run /airx:update <module> after a ticket, or /airx:refresh for a full re-verify, before trusting it." >&2
fi
exit 0
