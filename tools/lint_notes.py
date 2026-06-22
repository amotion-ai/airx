#!/usr/bin/env python3
"""airx lint-notes — content-hygiene lints for memory notes. Deterministic, stdlib only, no LLM.

airx already verifies that citations RESOLVE (verify-citations) and that memory is well-COVERED/DEEP
(score). This adds the third leg the rules state but nothing enforced: that a note is CLEAN and HONEST —
  • SECRET (gate)   — no leaked credentials/keys/tokens. An agent that read code can paste a secret into a
                      note; for a 30-repo rollout that's the scariest failure. This is the one HARD lint.
  • EMOJI  (warn)   — no decorative emoji (CLAUDE.md: "no icons in markdown"). airx's own functional markers
                      (⚠ STALE, ✓/✗/→ in the U+2600–27BF block) are allowed; only pictographic emoji flag.
  • HYPE   (warn)   — no marketing/hype adjectives (a memory note is a fact sheet, not a brochure;
                      "terse beats bulky", evidence.py keeps token-% honest — same spirit).
  • AIGEN  (warn)   — no generic AI filler ("it's important to note", "plays a crucial role", "delve into")
                      — enforces airx's "cite or TBD, no generic claims" rule.

    python3 lint_notes.py <wiki-dir> [--strict]
Exit: 0 = clean (or warns only); 1 = a SECRET was found (or any warn, with --strict). Edits nothing.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

# --- shared non-note set (single source of truth; falls back if the verifier won't load) -------------
try:
    _spec = importlib.util.spec_from_file_location("airx_vc", Path(__file__).resolve().parent / "verify-citations.py")
    _vc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_vc)
    NON_NOTES = _vc.NON_NOTES
except Exception:
    NON_NOTES = {"MEMORY.md", "PENDING-ENHANCEMENTS.md", "VALIDATION-REPORT.md"}

# --- SECRET patterns (conservative — specific shapes, not "the word password") -----------------------
SECRET_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |PGP )?PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[0-9A-Za-z]{36}\b|\bgithub_pat_[0-9A-Za-z_]{22,}")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("JWT", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{6,}")),
    ("private key (PEM file ref w/ inline)", re.compile(r"-----BEGIN CERTIFICATE-----")),
    ("DB URL with password", re.compile(r"\b(?:jdbc:[a-z]+:|mongodb(?:\+srv)?://|postgres(?:ql)?://|mysql://|redis://)[^\s`]*:[^\s`:@/]+@")),
    # generic secret=value assignment with a quoted, long, non-placeholder value. The leading [a-z0-9_]*?
    # lets an identifier prefix through, so `aws_secret`/`db_password`/`x_token` match, not just bare keys.
    ("hardcoded secret assignment", re.compile(
        r"""(?ix)\b[a-z0-9_]*?(?:api[_-]?key|secret|access[_-]?token|auth[_-]?token|client[_-]?secret|
            password|passwd|pwd|private[_-]?key|token)\s*[:=]\s*["']([^"']{8,})["']""")),
]
# placeholders that make an otherwise-matching value NOT a real secret
_PLACEHOLDER = re.compile(r"(?i)\b(tbd|xxx+|todo|example|sample|placeholder|changeme|your[_-]?|redacted|dummy|"
                          r"fake|test|none|null|\*{3,}|<[^>]+>|\$\{[^}]+\}|env\.|process\.env)")

# --- EMOJI: pictographic ranges only (NOT the U+2600–27BF symbols block airx uses functionally) -------
EMOJI = re.compile(
    "[" "\U0001F000-\U0001FAFF"      # symbols & pictographs, emoticons, transport, supplemental, ext-A
        "\U0001F1E6-\U0001F1FF"      # regional indicators (flags)
    "]")

# --- HYPE: marketing adjectives that don't belong in a fact sheet ------------------------------------
HYPE = re.compile(r"(?i)\b(blazing(?:ly)?|seamless(?:ly)?|cutting[- ]edge|state[- ]of[- ]the[- ]art|"
                  r"world[- ]class|best[- ]in[- ]class|industry[- ]leading|next[- ]gen(?:eration)?|"
                  r"revolutionary|game[- ]chang(?:er|ing)|effortless(?:ly)?|supercharge[ds]?|"
                  r"lightning[- ]fast|unparalleled|turnkey|frictionless|synergy|delightful|"
                  r"powerful|robust|leverage[ds]?|seamlessly|out[- ]of[- ]the[- ]box)\b")

# --- AIGEN: generic LLM filler -----------------------------------------------------------------------
AIGEN = re.compile(r"(?i)("
                   r"it'?s important to note|it is important to note|it'?s worth noting|"
                   r"plays? a (?:crucial|vital|key|significant|pivotal) role|"
                   r"in today'?s fast[- ]paced|we will (?:explore|delve|dive)|delve into|"
                   r"a wide (?:range|variety) of|robust and scalable|"
                   r"this (?:section|document) provides an overview|as we can see|in conclusion)")


def _notes(mem: Path):
    return [p for p in sorted(mem.glob("**/*.md"))
            if not p.name.startswith("_") and p.name not in NON_NOTES and ".cache" not in p.parts
            and "_seed" not in p.parts]


def lint_text(text: str):
    """Return (secrets[], emoji_count, hype[], aigen[]) for one note's text."""
    secrets = []
    for label, pat in SECRET_PATTERNS:
        for m in pat.finditer(text):
            line = text[text.rfind("\n", 0, m.start()) + 1: text.find("\n", m.start())]
            if _PLACEHOLDER.search(m.group(0)) or _PLACEHOLDER.search(line):
                continue
            secrets.append((label, m.group(0)[:48]))
    emoji = len(EMOJI.findall(text))
    hype = sorted({m.group(0).lower() for m in HYPE.finditer(text)})
    aigen = sorted({m.group(1).lower() for m in AIGEN.finditer(text)})
    return secrets, emoji, hype, aigen


def lint_wiki(wiki: Path) -> dict:
    """Roll up lints across a wiki's notes. Pure-text — needs no repo/manifest."""
    out = {"notes": 0, "secrets": [], "emoji": 0, "hype": [], "aigen": [], "per_note": []}
    mem = wiki / "ai_memory"
    if not mem.is_dir():
        return out
    for md in _notes(mem):
        out["notes"] += 1
        s, e, h, a = lint_text(md.read_text(errors="ignore"))
        if s or e or h or a:
            out["per_note"].append((md.name, s, e, h, a))
        out["secrets"] += [(md.name, lbl, frag) for lbl, frag in s]
        out["emoji"] += e
        out["hype"] += [(md.name, w) for w in h]
        out["aigen"] += [(md.name, w) for w in a]
    return out


def main() -> int:
    strict = "--strict" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("usage: lint_notes.py <wiki-dir> [--strict]", file=sys.stderr)
        return 2
    wiki = Path(args[0]).resolve()
    if not wiki.is_dir():
        print(f"error: wiki {wiki} not found", file=sys.stderr)
        return 2

    r = lint_wiki(wiki)
    print(f"AIRX LINT-NOTES  {wiki.name}  ({r['notes']} note(s))")
    if r["notes"] == 0:
        print("  no memory notes to lint."); return 0

    if r["secrets"]:
        print(f"  SECRET   {len(r['secrets'])} possible secret(s) — FAIL (a note must never carry a credential):")
        for nm, lbl, frag in r["secrets"][:10]:
            print(f"             {nm}: {lbl} → {frag!r}")
    else:
        print("  SECRET   none ✓")
    if r["emoji"]:
        print(f"  EMOJI    {r['emoji']} decorative emoji (CLAUDE.md: no icons in markdown) — WARN")
    if r["hype"]:
        ws = sorted({w for _, w in r["hype"]})
        print(f"  HYPE     {len(r['hype'])} marketing word(s): {', '.join(ws[:8])} — WARN (a note is a fact sheet)")
    if r["aigen"]:
        ws = sorted({w for _, w in r["aigen"]})
        print(f"  AIGEN    {len(r['aigen'])} generic-filler phrase(s): {', '.join(ws[:5])} — WARN")
    if not (r["emoji"] or r["hype"] or r["aigen"] or r["secrets"]):
        print("  clean — no hygiene issues.")

    warns = bool(r["emoji"] or r["hype"] or r["aigen"])
    if r["secrets"]:
        return 1
    if strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
