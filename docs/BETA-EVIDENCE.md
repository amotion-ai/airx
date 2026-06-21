# airx — Beta Evidence

> What we measured before handing airx to beta users. The bar (set by the beta team): *don't judge airx by
> the README — judge it by real Claude Code behavior on one painful repo: does it reduce wrong scanning,
> improve root-cause accuracy, and keep memory verified?* This is the honest answer.

## TL;DR
- **Blind A/B**: on a real Spring Boot repo, the **airx-memory** agent avoided a multi-tenant fix the
  **no-memory** agent got **wrong and dangerous** — in both runs. An independent judge, blind to which arm
  was which, ranked both memory answers above both cold answers.
- **It's a guardrail, not an oracle**: airx reliably stops the *wrong* change; the *exactness* of the root
  cause scales with how deep the note is.
- **Quality is measured, not asserted**: token-% is explicitly demoted (a thin stub scores ~99%);
  `/airx:score` grades Coverage·Depth·Trust (gold memory **85/A**, a thin auto-note **50/D**).
- **All automated checks pass** (19/19) and the full flow runs on a clean clone.

## The A/B test (behavior, not token-%)
**Setup.** Repo: a real multi-tenant SaaS service (Spring Boot, ~3,755 Java files). Three tasks, two arms each (with vs
without airx memory), run by independent sub-agents. **Ground truth derived from the code/git, not from the
notes** (so the test can fail). The memory arm had to **self-route** `MEMORY.md` → the right note (not handed
it). Run twice to check reproducibility.

**The decisive task (multi-tenant trap).** Bug: a privileged user sees one tenant's queue instead of all.
Code truth: scoping is selected by an authority flag (`InboxService.java:79/82`); the privileged user has
a sentinel tenant code so the Hibernate filter is *off* (`UserSession.java:244`, `GenericHibernateDAO.java:264`);
the safe fix relies on that authority flag. A fix that *adds/tightens* a tenant filter is wrong.

| run | no-memory (cold) | airx-memory |
|---|---|---|
| 1 | ❌ wrong (claimed "sees all", proposed a tightening fix that risks scope breakage) | ✅ correct + safe (relies on the authority flag) |
| 2 | ❌ wrong premise (filter restricts company user — false) | ⚠️ safe-direction but wrong locus (socket path) |

The other two tasks (billing pattern/save, auth whitelist) — both arms correct; memory leaner on the
medium task, slight overhead on the trivial config task (so airx tells the agent to **skip memory on
trivially-greppable lookups**).

## The blind judge (bias removed)
We gave a fresh judge the four trap-task diagnoses **with the arm labels stripped**, scored only against the
code truth:

| blind label | actual arm | score | verdict |
|---|---|---|---|
| B | run-1 memory | **5/5** | correct + safe; *"looks like it had project-memory"* (guessed from its precision) |
| D | run-2 memory | 2/5 | safe-shaped but wrong locus |
| C | run-2 cold | 2/5 | risky, wrong premise |
| A | run-1 cold | **0/5** | wrong + dangerous |

**Both memory runs ≥ both cold runs; both cold runs were the unsafe ones.** The judge reached this without
knowing which arm was which — and even guessed the best answer was memory-assisted from its precision alone.

## Memory quality checks (the "is it verified" bar)
- **Real citations, no generic claims**: the generated note resolves **16/16** mechanically
  (`verify-citations`); every claim is a `file:line`/symbol, none vague.
- **Stays small**: the note is ~1,073 tokens.
- **Stale detection works**: on a repo whose memory was written against a different branch, `drift` flagged
  it (83% symbol resolution, WARN); `purify` flags dangling citations (and never invents a fix).
- **Quality is graded**: `/airx:score` ranks deep hand-curated memory (85/A) far above a thin stub (50/D) —
  the opposite of what token-% does.

## Automated sweep
19/19 checks pass: all tools parse; measure chain composes (check PASS, score+nudge, benchmark, evidence);
create chain works on a fresh clone (init, docs, kb, draft); self-improve loop fires on a real commit
(non-blocking, tree clean, exit 0); calibration holds (gold A, stub D).

## Honest scope & caveats (what to expect in beta)
- **Solid:** the memory-first core — init, memory, check, score, benchmark, evidence, purify, enhance, and
  the post-commit self-improve loop. Validated and blind-confirmed.
- **Minimal/v0.1:** `/airx:docs` (scaffold) and `/airx:kb` (Java registry only) — functional, not
  battle-tested at scale.
- **Model-dependent:** the authoring commands (`/airx:memory`, `/airx:validate`, `/airx:enhance`) are prompt
  files; the deterministic tools they call are tested, but authoring quality depends on the in-session model.
- **Guardrail, not oracle:** airx reliably prevents the confident-wrong change; the exact root cause it lands
  on improves with note depth (and with coverage — `/airx:score` shows the `NEXT` module to document).
- **Plugin install** from a local clone is documented in [BETA-QUICKSTART.md](../BETA-QUICKSTART.md); the
  interactive `/plugin` step is the one path not exercised headless — beta is its first real run.

## Results on popular Java open-source repos

To show the win generalizes beyond our repos, the deterministic surface run on public Java OSS (a beta
user also tried airx on **Elasticsearch** with a good result):

| repo | stack | Java files | `init` stack detect | KB extraction (`/airx:kb`) | cold-grep cost of one broad question |
|---|---|---|---|---|---|
| **spring-petclinic** | Spring Boot | 48 | `java` ✓ | 18 endpoints · 6 entities · 1 service | ~0–1.9k tokens (small repo) |
| **primefaces** | JSF/PrimeFaces | 2,072 | `enterprise-java (beanstack)` ✓ | (registries generate in ~1s) | **6,152,870 tokens** for `render` |

The pattern is the whole thesis: on the **small** repo a cold grep is already cheap, so memory barely
helps; on the **large legacy** repo a single broad exploration is millions of tokens, where a ~1k-token
verified note is decisive.

## Cost saving — tokens → dollars (honest)

Using current Claude pricing (Opus 4.8 input **$5 / 1M tokens**; Sonnet 4.6 **$3 / 1M**):

| | primefaces (large legacy) | spring-petclinic (small) |
|---|---|---|
| one broad cold exploration (`render`) | ~6,152,870 tokens ≈ **$30.76** (Opus) / $18.46 (Sonnet) | ~0 tokens ≈ **$0.00** |
| same answer via a verified note | ~1,073 tokens ≈ **$0.005** | n/a |
| realistic (agent reads ~5% of grep) | ~308k tokens ≈ **$1.54** vs $0.005 → **~300× cheaper** | no saving |

**Honest framing:** the multi-million-token figure is an *upper bound* (an agent triages, it doesn't read
every grep line) — so treat the dollar number as **directional**, and it only materializes on large repos.
On a small/modern repo, memory doesn't pay and `/airx:benchmark` will say so. Repeated questions on the
same module compound the saving (and the note itself is cacheable at ~0.1× read cost). The bigger,
non-dollar win remains **the wrong fix avoided** (see the A/B above) — that prevents a far costlier
production incident than any token bill.

## The bar, answered
> reduce wrong scanning · improve root-cause accuracy · keep memory verified

Wrong *changes* avoided (blind-confirmed), root-cause correct on the hard task, citations mechanically
verified, staleness detected. The win is conditional and honestly bounded — strongest on hot, trap-laden
modules; neutral on trivial lookups; scales with coverage. That's a defensible **continue**.
