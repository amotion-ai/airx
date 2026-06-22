# airx — QA Report

> QA/testing pass before beta handoff. Method: 3 parallel static audits (tools / commands / hooks) →
> every high-severity lead **re-verified at the source** → **dynamic sweep**: all deterministic tools run
> against 3 real repos, **twice each** (idempotency), plus scale, fail-open, dirty-tree, and hook-clobber
> probes. Static labels are *leads*; only items reproduced or read at source are reported as bugs.
> One audit "CRITICAL" was a **false positive** — see Disproven.

## Repos under test (code repos kept pristine via sibling-wiki layout)
| repo | Java files | HEAD | memory | dirty before/after |
|---|---|---|---|---|
| csng-jnj | 7,932 | 9d9da5f9 | external gold (35 notes, flat) | 1 / 1 ✓ |
| dms-saas-service | 3,755 | b1d554c2 | sibling wiki, 2 notes | 100 / 100 ✓ (pre-existing) |
| dms-brillon | 5,509 | bf2a1332 | sibling wiki, 2 notes + seed | 1 / 1 ✓ |

All three code repos unchanged after the full sweep.

## Matrix — exit codes reproducible across both runs (idempotency PASS)
| tool | dms-saas (r1/r2) | brillon (r1/r2) | notes |
|---|---|---|---|
| check | 0 / 0 (0.47/0.32s) | 1 / 1 (**75.2s** cold / 0.5s warm) | rc=1 correct (brillon has a real dangling cite) |
| score | 0 / 0 | 0 / 0 | appends `.cache/score-trend.tsv` each run |
| verify-citations | 0 / 0 | 1 / 1 | rc=1 = dangling file:line (correct) |
| evidence | 0 / 0 | 0 / 0 | **also** writes score-trend.tsv (calls score.main) |
| purify (report) | 0 / 0 | 0 / 0 | edits nothing ✓ |
| memdiff | 0 / 0 | 0 / 0 | writes PENDING-ENHANCEMENTS.md |
| extract | 0 / 0 | 0 / 0 | overwrites `_draft_<mod>.md` (deterministic) |
| kb_registry | 0 / 0 | 0 / 0 | writes ai_knowledge_base/ |
| docs_init | 0 / 0 | 0 / 0 | run 2 correctly skips (non-empty dir) ✓ |
| seed_apply | 0 / 0 | 0 / 0 | idempotent (skips existing) ✓ |
| benchmark | 0 / 0 (~14.5s) | 0 / 0 (**~87s** cold) | cold grep cost scales with repo |

---

## CONFIRMED bugs (reproduced empirically)

### 1. [CRITICAL] `check.py` trust gate fails open — and exits 0
`tools/check.py:110-139` wraps the citations+drift verification in `try: … except Exception: pass`.
**Repro:** appended `raise RuntimeError` to a copy of `verify-citations.py`, ran check on the brillon wiki
(which has a genuine dangling `Distributor.java:35`). With the working tool: `OVERALL FAIL, exit 1`. With the
broken tool: the `citations`/`drift` lines **vanished**, `OVERALL WARN, exit 0`. A missing/moved/throwing
verifier silently downgrades a *failing* wiki to passing — and passes CI. This negates airx's core promise.
**Fix:** on exception emit a visible `citations = ERROR` (non-pass) + nonzero exit; never silently continue.

### 2. [HIGH] `score-trend.tsv` grows unbounded; `evidence` writes it too
`tools/score.py:143-150` appends a line every run; `evidence.py` calls `score.main()`, so `/airx:evidence`
appends as well. **Repro:** 4 new lines after score×2 + evidence×2 (timestamps confirm both sources).
No cap/rotation. **Fix:** document the write; cap/rotate the trend file; make it append intentionally only.

### 3. [HIGH] In-repo layout → dirty working tree (gitignore only on `--install-hook`)
`tools/init.py:255` adds `.cache/` + `PENDING-ENHANCEMENTS.md` to `.gitignore` **only** when installing the
hook. **Repro:** init in-repo (no hook) → commit `ai_memory/` → run score → `git status`:
` M ai_memory/.cache/score-trend.tsv` + `?? ai_memory/.cache/index-*.json`. The HEAD-keyed index JSON can
even be `git add`-ed by accident. Contradicts the "tree stays clean" design claim.
**Fix:** always write the two gitignore entries on in-repo init, independent of `--install-hook`.

### 4. [PERF, HIGH] Cold `build_index` blocks interactive commands for 29–75s
HEAD-keyed cache means a cold build on **every commit's first** check/verify/score.
**Measured cold:** brillon check **75.2s** (5,509 Java); csng-jnj verify **29.2s** (7,932 Java).
Warm: 0.3–0.7s. `benchmark` (separate cold grep) **87s** on brillon. A 75s blocking `/airx:check` is exactly
the kind of thing a team disables on day one. **Fix:** background/stream the build with progress; or warm the
cache in the post-commit hook so the next interactive call is warm; cap grep breadth.

### 5. [LOW] `benchmark.py` exits 2 when `benchmark.json` is absent
A "not-applicable-yet" state returns an error code (would fail a CI gate that runs benchmark). **Fix:** exit 0
with a "N/A — no KB yet" message.

### 6. [LOW] `/airx:view` referenced but unimplemented
`commands/kb.md:39`, `commands/init.md:19` point users to `/airx:view`; no `commands/view.md` exists.
**Fix:** mark "coming soon" or drop the references until it ships.

### 7. [LOW] `verify-citations.py:234` mislabels `Class.method` as `class`
Dotted tokens whose owner type exists are counted under `class` instead of method/named-query — skews the
per-kind stats only. Cosmetic.

### 8. [LOW] Shared-constant drift across tools
`_non_notes` re-defined locally in `check.py:77` (vs `verify-citations.NON_NOTES`); `_CODE_EXT` (init, dotted,
8) ≠ `_CODE_EXTS` (verify-citations, bare, 16+); `_IGNORE_DIRS` differ across init / kb_registry /
verify-citations. Behaviour can silently diverge. **Fix:** one shared source of truth.

---

## Validated working at scale (not bugs — positive results)
- **Symbol-aware verification holds at scale:** gold (35 notes) vs csng-jnj (7,932 Java) → **239/287 symbols
  resolve (83.3%)**, file:line all resolve, exit 0 (symbols advisory). Hundreds resolve, not ~0 — the thesis.
- **Trust gate works when the verifier works:** brillon's dangling `Distributor.java:35` → `OVERALL FAIL`,
  exit 1, both runs. (Bug #1 is specifically the *verifier-broken* path.)
- **Idempotency:** all 11 tools × 2 runs gave identical exit codes; docs_init/seed_apply skip on re-run.
- **Quality score calibrates:** brillon sparse memory → 48/100 grade D with a correct `NEXT:` nudge.

## Suspected → DISMISSED (probed, not reproduced)
- **`--install-hook` clobbering `core.hooksPath`:** pre-set `.myhooks`; after install it stayed `.myhooks`
  (no clobber). Good.
- **`docs_init` clobber on re-run:** skips when target is non-empty. Good.
- **Silent subprocess timeout:** did not trigger at 7,932 Java (29s ≪ 120s timeout). Latent only on
  extreme repos; low priority — but should still surface a warning instead of swallowing `TimeoutExpired`.

## DISPROVEN (do not action)
- **`docs_init.py:104` "CRITICAL IndexError":** false. Line 102 (`if not line.strip(): continue`) guarantees
  `line` is non-empty before `line[0]`. Cannot IndexError.

---

## Fix todo (9 FIXED, #4 mitigated — verified by re-run, see next section)
- [x] **#1 check.py fail-open** — broken/missing verifier now reports `citations = ERROR` → `OVERALL FAIL`,
  exit 1 (`tools/check.py`: verifier loaded once at module level; exception/None → ERROR+fail).
- [~] **#4 cold build latency — MITIGATED (not eliminated)** — exclude `target/.git/build/...` from the grep
  passes (75.2s→42.5s) + a visible stderr "building index… cached after" notice; the post-commit hook warms
  the cache so the next interactive call after a *commit* is sub-second. Honest caveat: a **fresh clone's
  first** `check` is still ~42s (raw scan cost). Full elimination (async/streamed build) is future work.
- [x] **#3 in-repo dirty tree** — `init.py` always gitignores `ai_memory/.cache/` + `PENDING-ENHANCEMENTS.md`
  on in-repo layout, independent of `--install-hook`.
- [x] **#2 score-trend** — capped to last 1000 rows; docstring documents the write (`tools/score.py`).
- [x] **#5 benchmark exit code** — exit 0 with an "N/A — no KB yet" message when `benchmark.json` is absent.
- [x] **#6 /airx:view refs** — marked "planned, not yet shipped" in `commands/kb.md` + `commands/init.md`.
- [x] **#8 constant drift** — `check.py` now imports `NON_NOTES` from the verifier (removed the local dup).
  (`_IGNORE_DIRS`/`_CODE_EXT` divergence between `init.py` and `verify-citations.py` is intentional —
  different scopes: module detection vs symbol indexing — left as-is by design.)
- [x] **#7 symbol label** — `Class.method` dotted tokens now counted in the named-query (dotted) bucket,
  no longer inflating `class` (`verify-citations.py:234`).
- [x] **N1 input validation** — `score`/`verify-citations`/`evidence`/`purify`/`memdiff`/`benchmark` now
  exit 2 on a nonexistent wiki path (uniform with the others).
- [x] **N2 scaffolder guards** — `kb_registry`/`docs_init`/`seed_apply` refuse (exit 2) a directory with no
  `.ai-readiness.yml` instead of scaffolding/scanning the wrong tree.
- [x] **(latent) silent drift truncation** — `memdiff` now prints "…and N more" when the drift list is
  truncated at 40.

## Fix verification (re-run results)
- `py_compile` all 12 tools — **OK**.
- **#1:** new `check.py` + deliberately-broken verifier on the failing brillon wiki → `citations ERROR`,
  `OVERALL FAIL`, **exit 1** (previously WARN/exit 0).
- **N1:** nonexistent path → **exit 2** for all of score/verify/evidence/purify/memdiff/benchmark/check.
- **N2:** kb/docs/seed on a no-manifest dir → **exit 2** (no files created).
- **#5:** benchmark on a valid wiki without a KB → **exit 0**.
- **#3:** in-repo init (no hook) → commit → score → `git status` **CLEAN**; `.gitignore` carries both entries.
- **#4:** cold brillon check **42.5s** (was 75.2s) + progress notice on stderr.
- **Happy-path (post-guard) regression:** all 11 tools **exit 0** on the valid dms-saas wiki — the new
  manifest guards do NOT false-reject a real wiki; `check` renders `citations PASS 16/16` + `drift PASS 23/23`
  → `OVERALL PASS`. Calibration intact — gold wrapped wiki **85/A**, brillon still **FAIL/exit 1** on its real
  dangling citation.

---

## Round 2 — negative / edge-input testing (new)
Every tool run with: **(A) no args, (B) nonexistent path, (C) dir without `ai_memory`, (D) empty `ai_memory`.**

**POSITIVE — no crashes:** zero tracebacks across all 44 bad-input invocations; no-arg prints a usage line and
exits 2 for every tool. The gold memory in a properly wrapped wiki **passes `check` and scores 85/100 (A)**
end-to-end on csng-jnj — full-pipeline calibration confirmed.

### N1. [MEDIUM] Inconsistent exit-code contract — nonexistent wiki path returns **exit 0**
On `/no/such/dir/xyz`: `check`, `extract`, `kb_registry`, `docs_init`, `seed_apply`, `benchmark` correctly
return **rc=2 "not found"** — but `score`, `verify-citations`, `evidence`, `purify`, `memdiff` print a header
and return **rc=0**. A typo'd path silently "succeeds" (no stray files left, but no error either). Half the
tools validate the wiki dir; half don't. **Fix:** a shared `require_wiki(path)` that exits non-zero when the
path or `ai_memory/` is absent, applied uniformly.

### N2. [MEDIUM] `kb_registry` / `docs_init` / `seed_apply` scaffold into ANY directory, no manifest check
On a dir with no `.ai-readiness.yml`, all three return rc=0 and **create** `ai_knowledge_base/` /
`ai_documentation/` / `ai_memory/_seed/`. `kb_registry` with no manifest resolves `repo_path` to the wiki dir
(or cwd) and **scans the wrong tree silently** (0 Java here, but would index the wrong repo elsewhere). A user
who runs `/airx:kb` from the wrong place gets a registry built off the wrong code. **Fix:** require a manifest
(or an explicit `--force`/confirmation) before scaffolding; refuse rather than scan an unconfirmed tree.

### Added to fix todo
- [ ] **N1** — uniform `require_wiki()`; nonexistent/no-`ai_memory` path must exit non-zero everywhere.
- [ ] **N2** — kb/docs/seed must verify an airx manifest before creating files / scanning a tree.

---

---

## Round 3 — OSS legacy-Java sweep (fixed tools on 4 fresh public repos)
Shallow-cloned 4 well-known legacy Java repos, ran `init`+`kb_registry`+`check`/`verify` (sibling layout).
**All clones stayed pristine (0 dirty); every tool exited 0; no crashes** — the fixes generalize to repos
airx had never seen.

| repo | Java files | stack detect | endpoints | @Entity | @Service | cold build | clone clean |
|---|---|---|---|---|---|---|---|
| **openmrs-core** | 1,282 | java (Hibernate) | 1 | **85** | 86 | n/a (0 notes) | ✓ |
| **fineract** | 6,399 | java (JAX-RS) | 3 | **251** | **1,613** | **3.0s** cold / 0.2s warm | ✓ |
| **BroadleafCommerce** | 2,985 | java (Spring MVC) | **73** | 159 | 649 | fast | ✓ |
| **ofbiz-framework** | 1,187 | java (entity-engine) | 0 | 0 | 0 | fast | ✓ |

### New findings (coverage/UX gaps on legacy stacks — not regressions)
- **L1 [KB stack-pack gap]** — `kb_registry` only recognizes **Spring-MVC `@RequestMapping` + JPA `@Entity` +
  Spring beans**. On legacy stacks it under-reports: fineract has **166 JAX-RS `@Path`** files but only 1
  `@RequestMapping` (→ 3 endpoints detected); ofbiz uses its own engine (**14 `entitymodel*.xml` + 114
  `services*.xml`** → 0 detected). The **memory layer is stack-agnostic and still applies**; only the KB
  *lever* needs per-stack packs (JAX-RS / OFBiz / JSF / Struts). Already on the roadmap — now evidenced. Fix:
  add JAX-RS + entity-engine extractors, or `kb_registry` should print "0 found — Spring/JPA pack; this repo
  looks like JAX-RS/<engine>" so a 0 isn't mistaken for "nothing here."
- **L2 [shallow-clone churn]** — all 4 clones are shallow (`--depth 1`); with no history, churn ranking
  misfires (ofbiz hottest = `buildSrc (2 changes)` instead of `applications/`/`framework/`). Fix (small):
  `init` detects `git rev-parse --is-shallow-repository` and warns that module ranking is unreliable on a
  shallow clone. **(Implemented this round.)**
- **Confirmed (not a bug):** cold `build_index` cost is **repo-shape**, not Java-count, driven — fineract
  (6,399 Java, few XML) cold = 3.0s vs brillon (5,509 Java, query-XML-heavy) = 42s.

### Added to fix todo
- [x] **L2** — `init` warns when the repo is a shallow clone (churn ranking unreliable).
- [x] **L1 — JAX-RS + entity-engine KB extractors added & verified** (`tools/kb_registry.py`):
  - **JAX-RS** (`@Path` + `@GET/@POST/...`): fineract endpoints **3 → 955** (952 jax-rs + 3 spring),
    real routes (e.g. `GET /v1/accounttransfers`, `PUT /{accountNumberFormatId}`).
  - **entity-engine** (OFBiz `entitymodel*.xml` / `services*.xml`): ofbiz **0/0/0 → 10 endpoints ·
    1,132 entities · 3,576 services**. Cross-checked exact: entities **1,132 = 858 `<entity>` + 274
    `<view-entity>`**; services **3,576 = 3,576 `<service>`**.
  - Each item now carries a `framework`/`source` tag (spring-mvc | jax-rs | jpa | entity-engine |
    spring-bean | service-engine); a 0-count prints a "this repo may use another stack" note.
  - **No regression**: Spring repos unchanged (broadleaf 73/159/649; dms-saas 2536/672/530).
  - Self-caught bug during impl: the first tag regex `<(entity|view-entity)\b` also matched `<entity-one>`
    refs (would over-count); tightened to `(?=[\s>])`.
  - Remaining (future): JSF/Struts/MyBatis packs.

---

---

## Round 4 — adopted from repo-mind: note-hygiene lint suite (`tools/lint_notes.py` + `/airx:lint`)
After reviewing `timolabs-ai/repo-mind` (a close cousin — same space, more governance/lint machinery), adopted
the one on-thesis, deterministic piece it had and airx lacked: **content-hygiene lints** enforcing rules airx
*stated but never checked*. New `tools/lint_notes.py` (stdlib, no LLM, pure-text — needs no repo/manifest):
- **SECRET — hard gate** (private keys, AWS/GitHub/Slack/Google tokens, JWTs, DB-URL-with-password, and
  `*secret/token/password = "…"` assignments; placeholders like `${ENV}`/`your-`/`example` skipped).
- **EMOJI / HYPE / AIGEN — advisory warns** (decorative emoji; marketing words; generic LLM filler).

Wired in: `/airx:check` (secrets = FAIL/gate, rest = WARN), the post-commit hook (report-only), and a new
`/airx:lint` command (`--strict` = warns also fail, for CI). Skipped from repo-mind as clone/scope-creep:
Linear/MkDocs sync, the Karpathy-"paper" factory, the MCP server, multi-tool exporter (airx has equivalents
or has them roadmapped).

**Verified:**
- Secret gate fires: a planted note → **4 secrets caught** (GitHub token, `api_key`, `aws_secret`,
  `github_token`); `lint_notes` exit 1 **and** `check` → `secrets FAIL` → `OVERALL FAIL` exit 1.
- Placeholder skip works (`${DB_PASSWORD}`, `your-token-here` not flagged).
- **No false positives on real hand-curated memory**: gold (34 notes) and dms-saas (2) → clean, exit 0.
- True-positive on real notes: brillon flagged **23 decorative emoji** (🟢🟡🔴 status icons) — a correct WARN.
- airx's own `⚠ STALE` marker (purify) and `✓/✗/→` are NOT flagged (emoji lint matches only pictographic
  U+1F000+ ranges, not the U+2600–27BF symbols block).

## Test artifacts created (regenerable; in sibling wikis, not code repos)
- dms-saas-service-wiki: added `ai_documentation/`, `ai_knowledge_base/`; +trend lines.
- dms-brillon-wiki: added `ai_knowledge_base/`, `_seed/`, drafts, PENDING; +trend lines.
- `/tmp/airx-qa/` scratch (throwaway git repos for dirty-tree + fail-open + hook tests).
