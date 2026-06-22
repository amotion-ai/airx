# Try airx on your repo (5 minutes) + send a field report

airx is validated on **one** repo so far (see [BETA-EVIDENCE](BETA-EVIDENCE.md)). A method claims to
generalize — so the single most useful thing you can do is run it on **your** painful repo and tell us
what happened, good or bad. Negative results are *more* valuable than positive ones.

## The 5-minute trial

Prereqs: Claude Code, **Python 3.7+**, **git**. Works best on a **large/legacy** repo (that's where the
win is; on a small modern repo airx will honestly tell you it doesn't pay).

```
# 1. install the plugin (from a clone you've cd'd into)
/plugin marketplace add .
/plugin install airx@airx

# 2. in your repo: stamp memory + the self-improve hook
/airx:init --repo . --install-hook

# 3. author ONE note for your hottest module (airx proposes candidates by churn)
/airx:memory

# 4. prove it — does the note resolve, score, and beat cold grep?
/airx:check        # citations + drift gate
/airx:score        # Coverage · Depth · Trust
/airx:benchmark    # token delta vs grepping cold

# 5. the real test: open a fresh agent on a real bug in that module, with the note loaded.
#    Did it reach the right root cause / avoid a wrong change faster than without it?
```

## What we most want to know

The behavioral question matters more than the token number:

- **Did it avoid a wrong change** or reach a root cause faster on a real task? (The whole point.)
- **Where did it break?** Install step, `init` on your stack, a tool that errored, a note that was wrong.
- **Did `/airx:check` flag anything real** — a stale citation, a drifted symbol?
- **Stack fit:** language/framework, repo size (files), and whether `init` detected your stack.
- **Did it waste your time** on a repo where it shouldn't have? (We want to detect & warn on that.)

## Send the report

Open a **Field report** issue (the template prompts for exactly the above), or if you can't share
specifics, even a one-line "tried it on a 4k-file Django repo, install worked, note helped on a caching
bug, score 62/C" is gold. No client names or proprietary code needed — genericize freely; airx itself is
built to never require them.
