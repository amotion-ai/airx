# Verifiable Project Memory — a spec (v0.1, draft)

> A small, implementation-agnostic convention for AI agent memory you can trust. airx is one
> implementation; this spec is not airx. Adopt it in any tool, any language, with or without our code.

## Why this exists

A coding agent re-derives a codebase's context every session — and the common fix (store/embed
everything) has a fatal property: **a stale memory that reads as current is worse than none.** Once an
agent trusts a wrong "fact," it ships the wrong change confidently.

The fix isn't more storage. It's a discipline that makes every remembered claim **checkable by a
machine** — so memory can be flagged when it goes wrong, automatically, with no model in the loop.

This document specifies that discipline. It is deliberately tiny.

## The five rules

1. **Cite or `TBD`.** Every concrete claim carries a citation to real source, **or** the literal token
   `TBD`. A claim with neither is non-conformant. *A visible gap beats an invisible lie.*

2. **Symbol-first.** Prefer a durable symbol (a type name, a method, an externalized query name, a bean
   id) over a line number. Symbols survive refactors that move every line; line numbers don't.

3. **Mechanical verification.** Every citation MUST be resolvable by a deterministic checker — no model
   inference. "Resolvable" means *structural*: a class resolves only if a type of that name is **declared**
   (not merely a file named that); a `Class.member` resolves only if the owning type is declared **and the
   member name appears in that type's declaring source** (a textual member check — stronger than "the owner
   exists," weaker than a full parse; an implementation MAY tighten this to a real declaration check); a
   `file:line` resolves only if the line exists in range. The checker is the source of truth, not the prose.

4. **Grade quality separately from tokens.** Token reduction is not quality — a one-line `TBD` stub can
   "save 99% of tokens" and be useless. Conformance MUST report a quality signal (coverage / depth / trust)
   distinct from any token metric, and MUST NOT present a token number as proof of usefulness.

5. **Automation may remove a lie, never add one.** Any automatic step (drift flagging, purify, a
   post-commit hook) may **downgrade or flag** a claim that no longer resolves. It MUST NOT invent, edit, or
   promote a claim. Adding a *why* is a human act.

## Citation grammar (normative for this spec's checker)

```
file:line     path.ext:N            or path.ext:N-M        # line(s) exist in the file
class         CamelCaseName                                 # a type by this name is DECLARED in the repo
Class.member  OwnerType.identifier                          # OwnerType is declared AND identifier appears in its source
named query   Namespace.queryName                           # name="…" exists in an externalized query file
bean id       @Component("beanId") (or @Service/@Repository/@Controller/@Named)
```

A checker MAY support a subset; it MUST document which kinds it resolves and treat unknown kinds as
unverified (not as resolved).

## Conformance levels

- **L0 — Cited.** Every claim has a citation or `TBD`. (Rule 1.)
- **L1 — Verified.** A deterministic checker resolves every citation; dangling `file:line` is a hard
  failure. (Rules 1–3.)
- **L2 — Maintained.** Drift is detected automatically against the current commit and quality is graded
  separately from tokens. (Rules 1–4.)
- **L3 — Self-healing.** An automatic, model-free step flags stale claims on change without ever adding an
  unverified one. (Rules 1–5.)

A tool states its level by what it actually does, verified by tests — not by what it markets.

## Note shape (informative)

One dense note per hot module: package/class overview, key methods (cited), data model + screens/paths,
externalized queries + tables, business-logic flows (with real code), gotchas/traps, and a dated,
ticket-linked history of *what changed & why*. Dense and cited beats long and vague — bulky or
model-generated context measurably degrades agent performance.

## Relationship to retrieval (informative)

This is a **verified-intent** layer; it composes on a structure layer (call graph / LSP / code index),
it does not replace it. Structure answers *where* a symbol is and *what calls it*. Memory answers *why* —
"this method is misnamed; it drives tenant scoping; don't revert it" — which a graph is structurally blind
to. Keep your index; layer verified intent on top.

## Adopting this without airx

You need three things, none airx-specific:
1. a note format that carries citations (any Markdown convention works);
2. a deterministic checker that resolves the grammar above against your repo and exits non-zero on a
   dangling `file:line` (a few hundred lines of any language — airx's `tools/verify-citations.py` is one
   reference, MIT);
3. a quality signal reported separately from tokens.

If you build one, the goal is the spec spreading, not the implementation. PRs that sharpen these rules are
more valuable than stars.

## Status

v0.1 draft. The rules are stable; the grammar will grow (more languages, more symbol kinds). Reference
implementation + conformance tests: this repo (`tools/verify-citations.py`, `tests/`). Discussion and
revisions welcome via issues.
