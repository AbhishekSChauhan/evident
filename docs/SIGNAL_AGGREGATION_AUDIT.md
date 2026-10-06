# Signal Aggregation Audit

**No implementation, no refactors, no methodology or planner changes.**
Establishes exactly where the four recovered buckets (`decisions`,
`constraints`, `concept_explanations`, `boundaries`) stop reaching stored
claim scores, and measures the gap with real data — reusing the same
40-claim, 240-turn, fully-corrected-pipeline dataset from
`POST_FIX_ROI_REMEASUREMENT_AUDIT.md`, plus one new, real
candidate-level/job-fit measurement built for this audit specifically.

---

## Part 1 — The exact path, traced stage by stage

All four buckets travel an **identical** path and fail at the **identical**
stage, so this is one shared trace, not four — the difference between
buckets is only in how often they're present, not in where they're lost.

| Stage | Present? | Merged? | Scored? | Persisted? | Displayed? | Used for matching? |
|---|---|---|---|---|---|---|
| **`extract_signals()`** (the LLM call) | **Yes** — confirmed live, 22.5–70% of real answers | n/a (per-answer, nothing to merge yet) | n/a | n/a | n/a | n/a |
| **`AnswerSignals`** (the parsed per-answer object) | **Yes** — all four are declared fields (`schemas.py:309-312`), correctly populated | n/a | n/a | **Yes** — `Response.signals_json` stores the full per-answer object, buckets included | n/a | n/a |
| **`score_answer()`** (per-answer rubric, `signals.py`) | **Yes** — reads `sig.decisions`/`.constraints`/`.concept_explanations`/`.boundaries` directly, confirmed by reference count (4/3/3/2 call sites respectively) | n/a (operates on one already-parsed `AnswerSignals`) | **Yes** — real, large per-answer score movement confirmed in `POST_FIX_ROI_REMEASUREMENT_AUDIT.md` §5 (JUDGMENT +35.4, OWNERSHIP +34.1, etc.) | **Yes**, as `Response.answer_score` | **Yes** — `QATurn.answer_score` on the recruiter detail page shows this per-answer number | No |
| **`merge_signals()`** (`signals.py:648-694`) | Present in the input it receives | **No** — confirmed directly: the function enumerates exactly eight bucket names and none of the four appear in its body | — | — | — | — |
| **`score_claim()`** (`signals.py:697-749`, calls `score_answer(merge_signals(answers), ...)`) | **No** — the merged object it scores never had the four buckets to begin with | — | **No** for these four — confirmed by real ablation: stripping any of them from the *current* merged object changes nothing, because they were never there | **Yes**, but the stored `ClaimScore.dimensions_json`/`.score` reflect **zero contribution** from any of the four | **Yes** — `ClaimGraph.claim_score`, every claim-level dimension score | No |
| **`candidate_dimension_profile()`** (`scoring.py:261-300`) | Inherits whatever `score_claim()` produced — zero contribution | — | Aggregates claim-level scores that already carry zero contribution from these buckets | **Yes**, cached in `Profile.dimension_profile_json` | **Yes** — the candidate-level radar/profile | No |
| **`build_candidate_graph()`** (`graph.py:265-482`) | Same — assembles `ClaimGraph`/`CandidateGraph` from already-zero-contribution stored rows | — | — | — | **Yes** — the entire recruiter detail page and Phase 2B's `composite_profile` both read this | — |
| **`job_fit.py`** | Reads `graph.dimension_profile` and `graph.competence_score`, both already zero-contribution for these buckets | — | — | — | — | **Yes, but matching against a number with zero contribution from any of the four buckets** |
| **Recruiter outputs** (ranked list, detail page) | — | — | — | — | **Yes, displayed, but the number displayed never reflects these buckets** | — |
| **Candidate outputs** (WhatsApp close-out message) | — | — | — | — | **Yes, same gap** — `graph.competence_score` carries the same zero contribution | — |

**One stage is genuinely correct and worth naming precisely: `score_answer()`
itself, called directly on a single answer, is not broken.** The break is
singular and localized — `merge_signals()` — and every stage after it is
"broken" only in the sense of faithfully propagating an already-empty
input forward.

---

## Part 2 — Quantified loss, real data, exact percentages

40 real claims, 240 real turns, the actual production pipeline exactly as
merged today (no monkeypatching).

| Bucket | Answers containing bucket | Merged claim contains (current, real) | Merged claim contains (if fixed) | Claim score uses bucket (current) | Claim score uses bucket (if fixed) |
|---|---:|---:|---:|---:|---:|
| `decisions` | 27/40 (67.5%) | **0/40 (0.0%)** | 27/40 (67.5%) | **0/40 (0.0%)** | 21/40 (52.5%) |
| `constraints` | 19/40 (47.5%) | **0/40 (0.0%)** | 19/40 (47.5%) | **0/40 (0.0%)** | 10/40 (25.0%) |
| `concept_explanations` | 9/40 (22.5%) | **0/40 (0.0%)** | 9/40 (22.5%) | **0/40 (0.0%)** | **0/40 (0.0%)** |
| `boundaries` | 28/40 (70.0%) | **0/40 (0.0%)** | 28/40 (70.0%) | **0/40 (0.0%)** | 28/40 (70.0%) |

**Every bucket collapses to exactly 0.0% at the merge stage, every time,
with no exceptions** — this is a complete, categorical loss, not a partial
one.

**One genuinely surprising result, reported as measured, not expected:**
even in the hypothetical "fixed" merge, `concept_explanations` moves **zero
of the nine claims'** scores, despite being present in all nine. The most
likely mechanism, consistent with already-confirmed scoring code: KNOWLEDGE
and ADAPTABILITY (the two dimensions `concept_explanations` feeds) are
already pushed to their `TARGETS`-defined ceiling by the much more abundant
`process_steps`/`causal_links` signals accumulated across six real turns
per claim — `score_knowledge()`'s `100 × min(1, weighted/TARGET)` formula
cannot move past 100 regardless of what else is added once the target is
already met. This is a real, measured saturation effect specific to the
claim level (six turns' worth of accumulated signal), not visible in the
single-answer ablation in `POST_FIX_ROI_REMEASUREMENT_AUDIT.md` §5, where
the same bucket moved KNOWLEDGE by +30.8 on average precisely because a
single answer is far less likely to already be saturated.

---

## Part 3 — `merge_signals()` audited directly

**1. Why were the four buckets omitted?**
`git log -S"concept_explanations: list" -- api/schemas.py` identifies
commit `ba03d47` ("wire 12 competence dimensions...") as the one that added
all four fields to `AnswerSignals` and all six `score_<dimension>()`
functions that read them. **That same commit touched `api/engine/signals.py`
extensively (137 lines) but never touched `merge_signals()`** — confirmed
directly by diffing the commit against the file; no hunk appears within 50
lines of `merge_signals()`'s definition. The scoring rubrics were written to
expect this content; the aggregation step that feeds them was never told
the new fields existed.

**2. Is the omission intentional?**
**No.** No comment, docstring, test, or commit message anywhere references
a deliberate decision to exclude these four buckets from merging. The
function's own docstring says "Union of every signal across a claim's
answers" — unqualified, naming no exceptions.

**3. Is it legacy technical debt?**
**Yes, confirmed by the commit history above, not inferred.** The function
predates the four fields in spirit even though it lives in the same file —
it was simply never revisited when the schema grew, and remained
unaddressed through the ownership-ladder fix, the extraction-prompt fix,
and the `score>0` backdoor fix, none of which touched this function either.

**4. Are there other buckets missing from `merge_signals()`?**
**No — exhaustively checked.** `AnswerSignals` has exactly twelve list
fields plus `summary`. `merge_signals()` explicitly handles eight:
`quantities, process_steps, causal_links, tools, metric_definitions,
incident_markers, entities, facts`. Twelve minus eight is four, and those
four are exactly `decisions, constraints, concept_explanations, boundaries`
— no fifth gap exists.

**5. Are there buckets merged but never scored?**
**Yes — `facts`.** Grepped across every `score_<dimension>()` function:
`facts` is referenced exactly once anywhere in `signals.py`, and that one
reference is inside `merge_signals()` itself (line 679) — no scoring rubric
reads it. **This is not a bug, unlike the four-bucket gap** — `facts` is
documented elsewhere in this codebase as existing solely for
`consistency.py`'s cross-answer contradiction detection, a different,
legitimate purpose than dimension scoring. Flagged here for completeness
per the question asked, not as a defect requiring the same fix.

**6. Are there buckets scored but impossible to populate?**
Not independently of the main finding. The current `extract_signals.txt`
asks for all twelve buckets (confirmed by re-reading the live prompt file),
so nothing is structurally unextractable. The only sense in which a bucket
is "scored but impossible to populate" today is exactly the four-bucket
case already documented: scored by the rubrics, genuinely populated at
the answer level, structurally discarded before scoring ever sees the
merged claim.

### Full table

| Bucket | In `merge_signals()`? | Scored by any rubric? | Status |
|---|:---:|:---:|---|
| `quantities` | Yes | Yes | Healthy |
| `process_steps` | Yes | Yes | Healthy |
| `causal_links` | Yes | Yes | Healthy |
| `tools` | Yes | Yes | Healthy |
| `metric_definitions` | Yes | Yes | Healthy |
| `incident_markers` | Yes | Yes | Healthy |
| `entities` | Yes | Yes | Healthy |
| `facts` | Yes | **No** | Merged but never scored — by design, feeds consistency checking instead |
| `decisions` | **No** | Yes | **Scored but discarded before scoring — the bug** |
| `constraints` | **No** | Yes | **Scored but discarded before scoring — the bug** |
| `concept_explanations` | **No** | Yes | **Scored but discarded before scoring — the bug** |
| `boundaries` | **No** | Yes | **Scored but discarded before scoring — the bug** |

---

## Part 4 — Blast radius if the four buckets are added to `merge_signals()`

**Measured, not estimated**, on 27 real candidates (grouped from the same
40-claim sample by their real `candidate_id`), using the real
`scoring.claim_score()`, `candidate_dimension_profile()`,
`composite_profile()`, `weighted_evidence_score()`, `competence_score()`,
and `job_fit.calculate_job_fit()` — called directly, current vs. a
corrected merge, nothing else changed. Job-fit used a representative
COMPETENCY-weighted requirement set (Ownership 35%, Judgment 35%,
Leadership 30%) specifically because those are the requirements these
buckets would plausibly move.

| Metric | Avg current | Avg if fixed | Avg delta |
|---|---:|---:|---:|
| Claim score | 92.17 | 94.52 | +2.35 |
| Competence score | 92.15 | 94.52 | +2.37 |
| **Ownership (composite cluster)** | 43.30 | **75.70** | **+32.41** |
| **Reasoning (composite cluster)** | 77.96 | **88.15** | **+10.19** |
| **Job-fit score** | 82.78 | **94.41** | **+11.63** |

**Claim score and competence score barely move** — both are six-dimension
weighted averages where EXECUTION and KNOWLEDGE (already near-saturated
from `process_steps`/`causal_links`, per Part 2's note) dominate the
denominator, diluting the four buckets' real contribution to a small
average effect. **The composite clusters show the true size of the gap**:
Ownership nearly doubles, Reasoning rises substantially — because those
clusters, per `V2_SCORING_METHODOLOGY.md`'s design, renormalize over
probed dimensions only and are not diluted by EXECUTION/KNOWLEDGE's
saturation.

**Badge thresholds:** 0 of 27 candidates crossed a badge boundary in this
sample — the claim/competence-score movement (+2.35/+2.37 avg) is real but
too small, on this particular sample, to cross the 40/70 thresholds.
(Contrast with `V2_CLAIM_SCORE_RENORMALIZATION_PLAN.md`'s separate finding
of a confirmed badge flip under a *different* change — this fix's effect
on the headline score is smaller because it is diluted across six
dimensions rather than concentrated in a denominator correction.)

**Recruiter ranking: the largest confirmed effect in this entire audit.**
Sorting the same 27 real candidates by competence score, current vs.
fixed: **23 of 27 candidates (85%) changed rank position.** The largest
single mover improved by 21 positions; the largest drop was 17 positions.
This is measured directly on real candidate data, not inferred from the
score deltas above.

---

## Summary

The defect is singular, precisely located, and legacy in origin — one
function, never updated across three separate dependent fixes. Its effect
is categorical (100% loss, every bucket, every claim) rather than partial,
and its downstream consequence is uneven: small on the headline
claim/competence score, large on the composite clusters this product is
moving toward reporting, and largest of all — a near-total reshuffling —
on recruiter ranking, the one output every other number in this product
ultimately exists to produce.

See `docs/SIGNAL_AGGREGATION_FIX_PLAN.md` for the plan to close it.
