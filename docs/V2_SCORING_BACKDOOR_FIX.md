# Phase 2A — The `score > 0` Backdoor Fix

**Scope: this one fix only.** No composite reporting, no confidence tags,
no recruiter UI changes, no methodology/planner/scoring-weight changes.

---

## 1. Every consumer of `.probed` / `probed_dimensions` / `probed_count()`, traced exhaustively

Grepped across the full `api/` tree, not assumed from prior audits:

| Consumer | File:line | What it does with `.probed` |
|---|---|---|
| **The source itself** | `signals.py:746` | `entry.probed = dimension in probed or entry.score > 0` — the backdoor |
| `probed_count()` | `scoring.py:192-193` | Counts `.probed is True` entries — feeds `ClaimScore.probed_dimensions` |
| `candidate_dimension_profile()` | `scoring.py:287` | `probed_any = probed_any or entry.probed` — candidate-level metadata only, not read back into that function's own score arithmetic |
| `recompute_claim()` | `orchestrator.py:1666` | Persists `stored.probed_dimensions = scoring.probed_count(dimensions)` |
| `ClaimState.weakest_dimension()` | `orchestrator.py:396-410` | **Primary sort key** — `.probed` decides which dimension the legacy planner treats as "weakest" |
| `plan_next()` | `orchestrator.py:890-984` (calls `weakest_dimension()` at lines 919, 974) | **Real planner logic** — see §2, legacy-path-only |
| `build_candidate_graph()` | `graph.py:398` | Copies `stored.probed_dimensions` onto `ClaimGraph.probed_dimensions` for display |
| `_dimension_totals()` | `graph.py:606` | Builds the `probed` set behind `_why_ranked()`'s "N of 6 dimensions probed" sentence |
| WhatsApp candidate message | `whatsapp.py:371-377` | `probed = sum(1 for d in graph.dimension_profile if d.probed)` — the candidate-facing coverage sentence |
| `job_fit.py` COMPETENCY matching | `job_fit.py:107` | `dp.score if dp.probed or dp.gate_open else 0` — **a real scoring input**, not just display |
| `job_fit.py` risk-area text | `job_fit.py:260` | `[d for d in graph.dimension_profile if d.score < 35 and d.probed]` — feeds generated "Lower score in X" explanatory text |
| Interview trace summary (dev diagnostic) | `orchestrator.py:1975` | Counts `dimension.probed` across all claims for a log/trace line — diagnostic only |
| Evaluation finalize log | `evaluation.py:196` | `log.info(..., "probed_dimensions": c.probed_dimensions, ...)` — log line only, not a stored comparison or replay check |

## 2. Impact by surface

**Recruiter-facing:** `graph.dimension_profile` and each `ClaimGraph.probed_dimensions`
(single-candidate detail page, `recruiter.py:84`) will show fewer dimensions
as "probed" wherever the old flag was backdoor-credited. `_why_ranked()`'s
"N of 6 dimensions probed" sentence (shown on the ranked list,
`recruiter.py:73`) will report a lower, more honest number for the same
reason.

**Candidate-facing:** the WhatsApp close-out message's "Evidence covered N
of 6 competency areas" sentence will also drop for the same candidates —
the exact number `COVERAGE_REACHABILITY_AUDIT.md` already measured as
inflated by up to 33 percentage points corpus-wide.

**job_fit impact — real, not cosmetic.** Two direct consumers:
1. `job_fit.py:107` uses `.probed or .gate_open` to decide whether a
   dimension's score counts toward COMPETENCY-category matching, or is
   zeroed out. A dimension that loses backdoor-crediting but has
   `gate_open=False` will now contribute 0 to job-fit scoring where it
   previously contributed its real score — a genuine, direct, numeric
   change to `job_fit_score` for some candidates, not merely a display
   change. `gate_open` is an independent OR condition, so the practical
   size of this effect depends on how often the two diverge — not
   measured here, flagged as the one thing worth checking on real data
   before this reaches production job-fit scoring.
2. `job_fit.py:260` builds a "low score, flagged as a risk" explanatory
   list gated on `.probed`. Fewer backdoor-credited low scores means fewer
   (less informative, but less falsely-alarming) entries in this list —
   a text-generation change, not a score change.

**Ranking impact: none.** `rank_candidates()`'s sort key is
`(-competence_score, -weighted_evidence_score, name)`. Neither
`claim_score()` nor `weighted_evidence_score()` reads `.probed` anywhere in
their arithmetic — confirmed by reading both functions in full, and proved
directly in `tests/test_probed_backdoor_fix.py`. Ranking order is
byte-identical before and after this fix.

**Planner impact: confirmed real, but confined to a non-default, legacy
path.** `ClaimState.weakest_dimension()` uses `.probed` as its *primary*
sort key, and is called twice — both inside `plan_next()`
(`orchestrator.py:890`), the **pre-forensic legacy planner**. `ask_next()`'s
dispatch (`orchestrator.py:1222-1231`) only reaches `plan_next()` when
**both** `settings.evidence_planner_v2` and `settings.forensic_questions`
are `False` — and `forensic_questions` defaults to `True`
(`config.py:96`). Under the default, live production configuration, this
fix has **zero** effect on which question gets asked next — `plan_next()`
never runs. It would change `plan_next()`'s behavior if that legacy flag
combination were ever active (tests, a deliberate rollback, or a future
config change) — named here precisely rather than either claimed as
"zero planner impact" or left undiscovered.

**Dev/diagnostic only, no behavior change:** the interview trace summary
(`orchestrator.py:1975`) and the evaluation-finalize log line
(`evaluation.py:196`) both just report the number — neither compares it
against anything or gates any decision on it.

---

## 3. The fix

One line, `api/engine/signals.py:746`:

```diff
-        entry.probed = dimension in probed or entry.score > 0
+        entry.probed = dimension in probed
```

`entry.basis = "not probed"` (the line immediately after) is unchanged —
it already correctly overwrites the basis string whenever `.probed` is
`False`, which now fires in more (correct) cases.

## 4. Files changed

- `api/engine/signals.py` — the one-line fix
- `tests/test_probed_backdoor_fix.py` — new, dedicated test file (7 tests)

## 5. Test results

**7/7 new tests pass. Full suite: 552/552 passed** (545 pre-existing + 7
new), zero regressions — no existing test asserted the backdoor's
specific behavior, so nothing needed updating.

## 6. Before / after example

Constructed directly from the fix's own target case (`test_a` in the new
test file): an answer containing only a `process_steps` entry, scored
under `ProbeLevel.DECISION` (which targets JUDGMENT only,
`PROBE_LEVEL_DIMENSIONS`).

| | Before | After |
|---|---|---|
| EXECUTION score | 50 (from the incidental `process_steps`) | 50 — **unchanged**, the score itself is still real |
| EXECUTION `.probed` | `True` (backdoor) | `False` |
| EXECUTION `.basis` | the real scoring rubric text | `"not probed"` |
| JUDGMENT `.probed` (genuinely targeted, scored 0) | `True` | `True` — **unchanged**, proves genuine targeting still works |
| `probed_count()` for this claim | 2 | 1 |
| `claim_score()` numeric output | X | **X — identical**, proved directly (`test_c`) |

---

## Confirmed exactly as requested

- (a) `score > 0` no longer marks a dimension probed — proved.
- (b) genuinely targeted dimensions remain probed — proved, both via
  `levels_used` and via `moves_used`.
- (c) `competence_score` remains unchanged — proved directly.
- (d) `claim_score` remains unchanged — proved directly.
- (e) `rank_candidates` ordering remains unchanged — proved directly from
  the same invariant chain.

No methodology, planner (under default settings), or scoring-weight
change. The one real, non-cosmetic impact found and not papered over:
`job_fit.py`'s COMPETENCY-matching score can now genuinely change for
dimensions that lose backdoor-crediting without `gate_open=True` — flagged
in §2, not fixed here (out of scope), and worth checking on real data
before this reaches production job-fit scoring.
