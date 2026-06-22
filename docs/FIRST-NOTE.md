# Your first verified note — a hands-on first run

Paste one prompt per step into Claude Code, watch it work, then confirm the checkpoint. **The agent does
the typing; you make three decisions.** In ~15 minutes you go from an empty repo to **one verified memory
note you've proven** — and you'll *feel* the one thing that makes airx different: a claim that can't be
backed by real code is caught mechanically, not trusted.

> **The mental model.** Your repo's root `CLAUDE.md` is the dashboard your agent auto-loads every session.
> The **note** is the work. Every claim in it cites real code — a durable symbol or `file:line` — or it
> says `TBD`. **Never a guess.** That rule is the whole product.

**The three decisions you'll make** (everything else is the agent typing):
1. **Accept or reject each claim** while the note is authored.
2. When a citation **fails the gate**, decide: fix it, or downgrade it to `TBD`.
3. Read the **quality + token verdict** and pick the next module.

Markers below: `✓` something now exists · `○` nothing changed yet (expected) · `🔒 GATE` a reproducible,
mechanical block.

> First time installing? See [BETA-QUICKSTART.md](../BETA-QUICKSTART.md). This page assumes the `/airx:*`
> commands already autocomplete. Prereqs: Claude Code, Python 3, git. Run every step **in the repo you
> want to make AI-ready** (use `.` for the current repo).

---

## Step 1 · Stamp memory into the repo

```text
/airx:init --repo . --install-hook
```

Creates `ai_memory/`, a root `CLAUDE.md` / `AGENTS.md` (so the agent auto-loads memory), a
`.ai-readiness.yml` manifest, and seeds `MEMORY.md` with **candidate modules ranked by git churn** — the
areas your recent commits actually touch. `--install-hook` wires the self-improve `post-commit` hook (via
`git core.hooksPath`; it chains into any existing hook, never clobbers it).

`✓` `ai_memory/` exists; root `CLAUDE.md` has an airx block; `MEMORY.md` lists candidate modules.
`○` **Nothing is faster yet — memory is empty until you author a note.** That's expected; the next steps
fix it.

---

## Step 2 · (Optional) Jump-start a draft

```text
/airx:draft
```

Writes `_draft_<module>.md` — an **UNVERIFIED** scaffold of code-derived facts tagged `[verify]`, with the
intent sections left as `TBD`. The leading `_` means airx's tools do **not** count it as real memory: it's
a *hypothesis list, never truth*. Skip this if you'd rather author from scratch.

`✓` A `_draft_*.md` appears — and `/airx:check` / `/airx:score` ignore it until you promote it.

---

## Step 3 · Author the real note — the discipline

```text
/airx:memory
```

Run it **bare** and airx proposes the hottest modules (the churn ranking from Step 1); pick one, or name an
area in plain words. The agent maps the code and **stops to show you each section** — package overview,
key methods, models, flows, ticket history. You **accept or reject each claim** — Claude Code's
accept/reject *is the gate* (**decision 1**).

The trust rule you'll see enforced:

- Every concrete claim cites a **durable symbol** (a class, a method, a table) — **preferred over a line
  number**, because symbols survive churn in big files — or a `file:line`.
- When a fact **can't** be cited, airx writes **`TBD — needs human input`** instead of guessing. A `TBD` is
  a *visible gap, not a lie* — that's the point.

`✓` `ai_memory/reference_<module>.md` is written, every line either cited or marked `TBD`.

---

## Step 4 · Feel the gate 🔒 — break a citation on purpose

You just trusted the note. Now watch airx refuse to. Open `ai_memory/reference_<module>.md` and change one
real citation to a **fake** line that can't exist, e.g.:

```text
SomeFile:99999
```

Then run:

```text
/airx:check
```

`🔒 GATE` — it **FAILs with a non-zero exit code** (this is what gates CI) and prints:

```text
FAIL - dangling file:line citations (hallucinated or stale). Fix the note or mark TBD.
```

**That hard FAIL is the method working** — and notice its own message points you back to the Step-3 rule:
fix it, or mark it `TBD` (**decision 2**). This is reproducible every single run — it's not the agent
politely declining, it's a mechanical check. **Now revert the fake line** so the note is honest again.

> This is the difference from a store-everything memory tool: airx can't silently carry a claim that no
> longer resolves to real code.

---

## Step 5 · Prove it works — behavior first

The real proof of memory is **behavior**: can the agent answer real questions from the note *without*
re-reading the source?

```text
/airx:memtest
```

The agent answers **5 real developer questions from the note alone — no grep**, citing the symbol/line for
each. Any answer it can't give says **"NOT IN MEMORY"** — that's a concrete gap to fill with another
`/airx:memory` pass.

`✓` *N* of 5 answered from memory alone, with a gap list for the rest.

---

## Step 6 · Grade quality, then (last) the token delta

```text
/airx:score
```

Grades the note on **Coverage · Depth · Trust** with an honest verdict. Quality is **not** the token
number — a thin `TBD` stub can win on token-% and still be useless, so airx grades the thing that matters.

```text
/airx:benchmark
```

*Then*, and only then, the measured token delta on **your** repo — note vs. grepping cold. It **reports**
the win; it never headlines it, and it will plainly say **"not worth it"** when a note doesn't pay.

**Honest about its own numbers** (same discipline applied to the tools): `score` is *a nudge, not a
calibrated measurement*; `benchmark` is *directional — an upper bound*; and airx's headline behavioral
result (the agent avoiding a wrong fix) is **n=1 so far**. These steps prove the note on your repo today;
they don't promise you'll reproduce that A/B.

`✓` A quality grade + a token verdict you can trust *because you measured it*, not because we claimed it.

---

## Step 7 · Stay honest as you ship

You installed the hook in Step 1. From now on, **every commit** runs it: it auto-flags stale citations and
writes a `PENDING-ENHANCEMENTS.md` worklist — **deterministic, zero model tokens, and it never edits your
notes**. When you're ready to fold a commit's changes into memory:

```text
/airx:enhance
```

Re-verifies flagged claims and adds new verified facts — **human-in-loop** (you approve the diff). It can
correct a stale citation or downgrade it to `TBD`, but it will never assert something unverified. The line
is absolute: automation may *remove* a lie, never *add* one.

`✓` Memory stays fresh as you work; `/airx:score` trends up across commits.

---

## The loop, closed

- Your agent now **auto-loads the note** instead of re-deriving that module every session.
- Every claim is **cited or `TBD`** — and a broken citation **fails the gate**, mechanically.
- The note gets **fresher and deeper as you ship**, and you can prove the trend.

**Three decisions made:** you approved each claim, you resolved a failed citation, and you read the verdict
to pick what's next.

### Honest caveats
- **No benefit until the first note.** `init` alone changes nothing — memory is authored, not magic.
- **Coverage scales with notes.** One note covers one module. Author your hottest modules first (airx ranks
  them for you), and the quality grade climbs as you go.

Next: repeat Step 3 on your next-hottest module. Auditing memory that already exists? Run `/airx:validate`.
