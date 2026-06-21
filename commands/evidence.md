---
description: One report — is the project memory actually working? Quality + Trust headline, tokens secondary.
argument-hint: "[wiki-dir] (default: ./ or sibling wiki)"
---

# /airx:evidence

The single report to show the beta team: **is memory earning its place, and why?** It aggregates the other
tools into one plain-English verdict so you don't have to run four commands and reconcile them.

## Run
```bash
python3 "${CLAUDE_PLUGIN_ROOT}"/tools/evidence.py <wiki>
```
Pairs with `/airx:benchmark` — **run that first** so the token arm has data; without it the report just says
"run /airx:benchmark". The verdict itself does not depend on tokens.

## What it reports
- **QUALITY** *(headline)* — Coverage · Depth · Trust + OVERALL/grade, straight from `/airx:score`.
- **TRUST** *(headline)* — share of citations that resolve to real code: `file:line` (hard) + symbols
  (class/query/bean, advisory).
- **DRIFT** — has the code moved out from under the notes? (the symbol resolution rate `/airx:check` uses).
- **TOKEN WIN** *(secondary)* — `memory_reduction_vs_bare` from `/airx:benchmark`. **Explicitly not a quality
  measure** — a thin TBD stub scores ~99% on tokens yet documents one module of eight.
- **VERDICT** — `GOOD` / `NOT YET` with the reason, keyed off **quality + trust, never token-%**.

## How to read it
Top-down. QUALITY and TRUST decide whether memory is good and trustworthy; token-% is a bonus, not the bar.
A high token-% with low quality means "fast but useless" — that's why it's printed last. Advisory only
(always exits 0); use `/airx:check` to gate CI.
