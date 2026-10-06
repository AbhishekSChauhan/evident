# Signal Aggregation Fix Plan

**Plan only. No code changes made by this document.**

---

## Exact file and function

**`api/engine/signals.py`**, function `merge_signals()` (currently
lines 648-694). One function, one file. Nothing else needs to change —
confirmed in `SIGNAL_AGGREGATION_AUDIT.md` Part 1 that every stage after
`merge_signals()` already correctly reads whatever the merged object
contains; they have never needed to change, only to be fed real data.

## Exact code location and change

Inside the existing `for sig in answers:` loop (currently lines 664-680),
add four more `add(...)` calls, immediately after the existing
`entities`/`facts` calls, following the identical pattern already used for
every other bucket:

```python
for de in sig.decisions:
    add("decisions", de, _key(de.choice, de.reason))
for co in sig.constraints:
    add("constraints", co, _key(co.limitation, co.effect))
for ce in sig.concept_explanations:
    add("concept_explanations", ce, _key(ce.concept))
for bo in sig.boundaries:
    add("boundaries", bo, _key(bo.scope_held, bo.scope_handed_off))
```

No change to the `add()` helper, the existing eight bucket handlers, the
`tools`/`metric_definitions` "best description wins" post-pass (lines
682-691), or `merged.summary`'s assignment (line 693). No new field, no
schema change — `decisions`, `constraints`, `concept_explanations`, and
`boundaries` already exist on `AnswerSignals` (`schemas.py:309-312`) with
`Field(default_factory=list)`, so `merged = AnswerSignals()` at the top of
the function already initializes them correctly; they simply need to be
populated by the loop like everything else.

**Dedup key rationale, matching the existing convention exactly:**
`causal_links` dedupes on `(cause, action, outcome)` — the full semantic
content, not just one field. The four new keys follow the same principle:
`(choice, reason)` for a decision (two near-identical choices with
different reasons are different signals), `(limitation, effect)` for a
constraint, `concept` alone for a concept explanation (its `reasoning` is
explanatory prose, not an identity component — mirrors how
`metric_definitions` dedupes on `metric` alone, not
`(metric, how_measured)`), and `(scope_held, scope_handed_off)` for a
boundary.

## Exact tests required

New test file, `tests/test_merge_signals_recovers_four_buckets.py`
(mirroring the naming and structure of `tests/test_probed_backdoor_fix.py`
and `tests/test_composite_reporting.py`, both already in the suite):

1. **Presence**: construct two `AnswerSignals` objects, one with a
   `DecisionSignal`, the other with a different one; call
   `merge_signals()`; assert both appear in `merged.decisions`. Repeat for
   `constraints`, `concept_explanations`, `boundaries`.
2. **Deduplication**: two answers both containing the identical decision
   (same `choice` and `reason`); assert `merge_signals()` keeps exactly
   one, not two — proving the dedup key works, not just that the bucket
   is no longer silently dropped. Repeat for the other three buckets with
   their respective keys.
3. **Non-interference**: construct an `AnswerSignals` sequence exercising
   every one of the twelve buckets at once; call `merge_signals()`; assert
   the eight previously-working buckets are byte-identical to their output
   before this change (same items, same order, same dedup behavior) —
   proving this is additive, not a rewrite.
4. **End-to-end, real functions, no mocking**: call
   `signal_rubrics.score_claim()` on two real answers where a
   `DecisionSignal` appears only in the second answer, with
   `moves_used=["AUTHORITY"]` on that turn; assert `JUDGMENT.score > 0` and
   `JUDGMENT.probed is True` — proving the fix reaches all the way to
   claim-level scoring, not just the merged object in isolation.
5. **Regression — the full existing suite.** 560/560 as of the last merged
   Phase 2B change must still pass unmodified; this change touches no
   existing bucket's logic.

## Expected metric movement

Directly from `SIGNAL_AGGREGATION_AUDIT.md` Part 4's real measurement on
27 real candidates — stated here as the expectation this fix should
reproduce when re-measured post-merge, not a new estimate:

| Metric | Expected movement |
|---|---|
| Claim score / competence score | Small, real increase (~+2 to +3 average) — diluted by six-dimension averaging |
| Ownership composite cluster | Large increase (~+30 average) — the single biggest beneficiary, since `boundaries` is Ownership's only unshared, exclusive signal |
| Reasoning composite cluster | Moderate increase (~+10 average) — `decisions`/`constraints` feed Judgment and Problem Solving directly |
| Job-fit score (Ownership/Judgment-weighted requirements) | Large increase (~+12 average) |
| Recruiter ranking | **Expect most candidates' rank position to move** — measured at 85% (23/27) on the audit's sample; re-measure on the full candidate base before treating this as a stable rate |
| Badge thresholds | Expect few or no flips on average, but check individually — the audit's sample showed zero, which should not be assumed to generalize without re-checking |

## Rollback plan

Revert the one function to its current state (delete the four added
`add(...)` calls). No data migration in either direction:
`ClaimScore.dimensions_json`/`.score`/`.probed_dimensions` are recomputed
from stored `responses.signals_json` on every `recompute_claim()` call,
never derived irreversibly — reverting the code and re-running
`recompute_claim()` for affected claims restores the pre-fix numbers
exactly, the same guarantee already established for the Phase 2A backdoor
fix's rollback plan. Per `scoring.py`'s own versioning convention
(`SCORING_VERSION`, wired into `provenance.py`'s `evaluation_version`
hash), this change should bump that constant, consistent with the same
requirement already noted for the claim-score renormalization plan, so
any already-finalized `Evaluation` is not silently replayed under a
formula it was never scored against.
