# Phase 2 — Scoring & Reporting Implementation Plan

**Plan only. No code in this document.** Traced fresh against the current
`api/engine/scoring.py`, `api/engine/graph.py`, `api/engine/signals.py`,
`api/engine/orchestrator.py`, `api/models.py`, and every router that
reaches a `DimensionScore`. No planner, claim-selection, or dimension
redesign proposed anywhere below — every recommendation is additive or a
single-expression correctness fix, named as such where it applies.

---

## 1. Unknown vs. Not Demonstrated collapse

**Exact code path, traced line by line:**

```
signals.py:746   score_claim()
                 entry.probed = dimension in probed or entry.score > 0
                 ─────────────────────────────────────────────────────
                 THE BACKDOOR. A dimension is marked probed either because
                 a targeting move/gap was genuinely asked, OR because the
                 score is incidentally nonzero for any reason. This is the
                 one place "Unknown" and "genuinely weak" become the same
                 bit.
                        │
                        ▼
orchestrator.py:1635   recompute_claim()
                 dimensions = signal_rubrics.score_claim(...)
                 stored.dimensions_json = _dump_dimensions(dimensions)     [:1665]
                 stored.probed_dimensions = scoring.probed_count(dimensions) [:1666]
                 ─────────────────────────────────────────────────────
                 Both the per-dimension `.probed` flags AND the integer
                 count are persisted here, already carrying whatever
                 signals.py:746 decided.
                        │
                        ▼
scoring.py:135   claim_score()
                 total_weight = sum(active.get(d.value, 0.0) for d in
                                     DIMENSION_ORDER) or 1.0
                 ─────────────────────────────────────────────────────
                 THE SECOND COLLAPSE. This line never reads `.probed` at
                 all — confirmed by reading the full function body. It
                 sums all six dimensions' weights unconditionally, then
                 divides. A dimension that was never probed (`entry is
                 None` → `value = 0`) and a dimension that was probed and
                 scored a genuine 0 are both `weight × 0` in the
                 numerator, with the full weight still in the
                 denominator. `.probed` is computed, persisted, and
                 reported alongside the score — never consulted by the
                 score's own arithmetic.
                        │
                        ▼
scoring.py:258   candidate_dimension_profile()
                 probed_any = probed_any or entry.probed    [:287]
                 ─────────────────────────────────────────────────────
                 Tracks `.probed` as metadata (feeds the dashboard's
                 `probed` flag per dimension) but the weighted average at
                 line 289 (`accumulated / weight_total`) has the identical
                 defect as claim_score() — unprobed claims' entries are
                 skipped via `continue` (line 282) only when `entry is
                 None`, but graph.py always constructs a placeholder
                 entry (next arrow) so `entry` is never actually `None`
                 by the time it reaches here.
                        │
                        ▼
graph.py:378-384  build_candidate_graph()
                 dimensions_map.get(d.value, DimensionScore(dimension=d,
                     score=0, basis="not probed", probed=False))
                 ─────────────────────────────────────────────────────
                 This default placeholder has the EXACT SAME shape
                 (score=0, probed=False) as a dimension signals.py
                 genuinely scored at 0 with probed=False — the one case
                 the backdoor doesn't inflate. These two situations are
                 structurally identical past this point; nothing
                 downstream can tell "never reached" from "reached and
                 proven weak" unless it additionally reads the `basis`
                 string, which no consumer in this codebase does.
                        │
                        ▼
whatsapp.py:371-377   the CANDIDATE-facing message
                 probed = sum(1 for d in graph.dimension_profile if d.probed)
                 f"Evidence covered {probed} of {len(graph.dimension_profile)}..."
```

**Reporting consequence, concrete and already measured:** the candidate's
own WhatsApp close-out message, the recruiter's single-candidate detail
page (`ClaimGraph.dimensions`, `CandidateGraph.dimension_profile`), and
`_why_ranked()`'s "N of 6 dimensions probed" sentence on the ranked list
all read from the same backdoor-inflated `.probed` flag. `COVERAGE_REACHABILITY_AUDIT.md`
already measured the gap this produces: reported coverage averaging 33
percentage points above structural (genuinely-targeted) coverage.

---

## 2. Coverage metric

**Two different "coverage" numbers exist in this codebase, and they must
not be conflated — tracing both precisely:**

1. **`role_coverage`** (`scoring.py:205-242`, `weighted_evidence_score()`)
   — claim-TYPE coverage: how much of a role's claim-weight schema the
   candidate's resume even speaks to, independent of interview quality.
   Computed correctly already — `total_role_weight` (claim types present)
   over `denominator` (all claim types the role weights). **Not affected
   by the score>0 backdoor at all** — it never touches dimension scores.
2. **"N of 6 dimensions probed"** (`scoring.probed_count()`, line
   192-193, and `graph._dimension_totals()`'s `probed` set, line
   604-619) — dimension-level coverage. **This is the number the
   backdoor inflates**, because both functions simply count `.probed is
   True` entries, and that flag's truth value was already decided (or
   miscalculated) at `signals.py:746`.

**Downstream consumers of the dimension-level coverage number,
enumerated exhaustively by direct grep, not assumed:**

| Consumer | File:line | What it shows |
|---|---|---|
| Candidate WhatsApp close-out | `whatsapp.py:371-377` | "Evidence covered N of 6 competency areas" |
| Recruiter single-candidate detail page | `recruiter.py:84` → `graph.dimension_profile`, each `ClaimGraph.probed_dimensions` | Per-dimension and per-claim probed state |
| Ranked list's `why_ranked` sentence | `graph.py:657`, inside `_why_ranked()` | "N of 6 dimensions probed" embedded in prose |
| Job-fit scoring (single + ranked) | `job_fit.py:86,110` → `graph.dimension_profile` | Consumed as an *input* to job-fit matching, not just displayed — flagged here for awareness; job-fit's own logic is out of scope for this plan |
| Dev inspection endpoint | `dev.py:166` | Same `CandidateGraph`, non-production use |

**Verification of the backdoor finding against current code:** confirmed
unchanged from `COVERAGE_REACHABILITY_AUDIT.md` and `SCORING_SEMANTICS_AUDIT.md`
— `signals.py:746` reads identically today.

---

## 3. Reporting layer — every output, traced

**Recruiter-facing:**
- `GET` via `recruiter.py:73` (`rank_candidates()`) → `CandidateSummary` —
  **no raw per-dimension fields at all**, confirmed by reading the full
  object construction (lines 831-858): `competence_score`, `role_coverage`,
  `badge`, `consistency_score`, and the `why_ranked` prose string only.
  The highest-traffic recruiter output does not expose six-dimension
  detail directly — it already only shows a composite-shaped surface
  (one score, one badge, one sentence).
- `GET` via `recruiter.py:84` (`build_candidate_graph()`) → full
  `CandidateGraph` — **this is the one place all six raw dimensions are
  exposed**, both at `dimension_profile` (candidate level) and at each
  `ClaimGraph.dimensions` (claim level).

**Candidate-facing:**
- `whatsapp.py:363-377` — exactly two scalars read from the graph:
  `graph.competence_score` and the probed-count sentence above. The
  candidate never sees per-dimension scores, only the coverage count.

**Every API returning dimension scores**, enumerated:
`routers/recruiter.py` (detail page), `routers/job_fit.py` (both the
single and ranked endpoints, as a scoring input), `routers/dev.py`
(non-production), `routers/whatsapp.py` (coverage count only, no scores).
No other router touches `DimensionScore` or `dimension_profile`.

---

## 4. Composite reporting — smallest-change path

**Recommended path: purely additive. Zero changes to `claim_score()`,
`candidate_dimension_profile()`, or any existing stored field shape.**
The six dimensions are already computed, stored, and consumed
successfully by `rank_candidates()` (via `Profile`/`ClaimScore`) and
`job_fit.py` — reworking that arithmetic in place would touch every one
of those consumers at once, which is the opposite of minimal blast
radius. Instead:

1. **A new, pure aggregation function**, parallel to
   `candidate_dimension_profile()` but operating on its *output* rather
   than replacing it: given the existing six `DimensionScore` entries
   (already computed, already correct as inputs), group them into the
   three clusters (`Execution/Knowledge`, `Reasoning` = Problem Solving +
   Judgment + Adaptability, `Ownership`) and produce one aggregate value
   per cluster — **renormalized only over genuinely-probed members**,
   which this new function can do correctly from the start, since it is
   new code with no existing callers to preserve.
2. **A new field on `CandidateGraph`** (and, if claim-level composite
   detail is wanted, on `ClaimGraph`) holding this three-entry list,
   populated by one additional call inside `build_candidate_graph()`
   immediately after the existing `scoring.candidate_dimension_profile(...)`
   call — the existing call and its result are untouched; the new call
   reads the same input and produces a second, separate output alongside
   it.
3. **The existing six-dimension `dimension_profile` field stays exactly
   as it is today** — "kept internally," per the task's own framing —
   available for `job_fit.py` and any other existing consumer that
   already depends on its current shape, while new recruiter/candidate
   surfaces can switch to reading the new three-cluster field instead.

This is the smallest change that satisfies "keep existing dimensions
internally if possible": nothing existing is removed, renamed, or
recomputed differently; one new function and one new field are added.

---

## 5. Confidence reporting — where it attaches

**Entirely at the same new, additive layer — no planner involvement,
confirmed by the same call-path check already done for the extraction
and ownership fixes.** Every field this plan touches
(`dimensions_json`, `.probed`, `.basis`, `.score`) was already confirmed,
in the two prior Phase 2 implementations, to be read by zero planner
code (`orchestrator.py`'s question-selection functions, `question.py`'s
move/ladder logic). The new composite-aggregation function (§4) is the
natural place to also compute a confidence/coverage tag per cluster —
**Unknown** (no member dimension has any stored entry at all),
**Not Demonstrated** (probed, scored at or near zero), **Declined**
(the claim's answers were flagged as memory-exhausted/non-answers — this
state already exists structurally via `is_memory_exhausted_or_skip()` in
`evidence.py`, just not currently surfaced at the cluster level), or
**Closed-with-confidence** (genuinely probed with real content) — derived
purely from data this layer already reads, attached as a new field
alongside each cluster's numeric value.

**One honest caveat that must be stated, not glossed over:** this new
confidence tag, built with zero changes elsewhere, can only be as honest
as the `.probed` flag it reads — and that flag is still computed by the
backdoor at `signals.py:746` unless §1's one-line fix is also applied.
Without that fix, the new "Not Demonstrated" state will still include
some claims that were never actually targeted, just incidentally scored
nonzero. This is named explicitly in the sequencing below as a decision
point, not decided silently here.

---

## Deliverables

### Call graph (consolidated)

```
signals.py:746  score_claim()  →  entry.probed  (BACKDOOR HERE)
      │
      ▼
orchestrator.py:1635-1667  recompute_claim()  →  ClaimScore.{score, dimensions_json, probed_dimensions}
      │
      ├──▶ scoring.py:119  claim_score()            [total_weight never reads .probed]
      │
      ▼
graph.py:375-408  build_candidate_graph()  →  ClaimGraph{dimensions, probed_dimensions}
      │
      ├──▶ scoring.py:258  candidate_dimension_profile()  →  CandidateGraph.dimension_profile
      │         [NEW, additive: composite cluster aggregation reads this same input]
      │
      ├──▶ graph.py:490  recompute_profile()  →  Profile.dimension_profile_json  (cache)
      │
      └──▶ graph.py:700  rank_candidates()  →  CandidateSummary  (no raw dims; why_ranked prose only)
                │
                ▼
      routers: recruiter.py (detail + list), job_fit.py (scoring input),
               whatsapp.py (coverage-count sentence only), dev.py (non-prod)
```

### Impacted files

| File | Change type |
|---|---|
| `api/engine/signals.py` | **Decision point, §1** — one boolean expression, only if the backdoor fix is approved |
| `api/engine/scoring.py` | **Additive only** — one new aggregation function |
| `api/engine/graph.py` | **Additive only** — one new field population call in `build_candidate_graph()` |
| `api/schemas.py` | **Additive only** — one new field/type for the composite cluster list |
| `api/routers/recruiter.py` | **Additive only** — expose the new field where the detail page already returns `CandidateGraph` |
| `api/routers/whatsapp.py` | **Optional, additive** — candidate message could use the new confidence-aware coverage sentence instead of the raw probed-count one |
| Nothing in `api/engine/orchestrator.py`, `api/engine/question.py`, `api/engine/extract.py` | **Unchanged** — confirmed no planner or claim-selection code reads any field this plan touches |

### Implementation sequence

1. **Decide the backdoor question explicitly** (§1, §5's caveat) — fix
   `signals.py:746` now, or ship the composite/confidence layer first and
   fix it in a follow-up once its blast radius (every existing
   `ClaimScore.probed_dimensions` value changes on next recompute) is
   separately reviewed. This is a product/timing call, not a technical
   one — named here for a decision, not made here.
2. **Add the composite-cluster aggregation function** (§4) — purely
   additive, zero existing callers affected, can be built and tested
   independently of step 1.
3. **Add the confidence/coverage-state tag** (§5) to the same function's
   output.
4. **Wire the new field through `build_candidate_graph()`** — one call,
   one new field on the return object.
5. **Expose it in `recruiter.py`'s detail-page response** — the schema
   already carries it once step 4 lands; this is routing, not logic.
6. **Only after the above is stable**, consider whether `whatsapp.py`'s
   candidate-facing sentence should move to the new, confidence-aware
   coverage language — lower priority, candidate-facing changes warrant
   more caution than an internal recruiter page.

### Blast radius

- **If step 1 (backdoor fix) is taken:** every existing candidate's
  `ClaimScore.probed_dimensions` and `.probed` flags change value on next
  recompute — real, visible, retroactive number movement across the
  entire candidate base, not confined to new interviews. `claim_score()`'s
  numeric output does **not** change from this alone (it never read
  `.probed`), only the reported coverage count does.
- **If steps 2-5 only are taken (no backdoor fix):** zero existing
  numbers change anywhere. Purely additive — new fields appear, nothing
  existing is recomputed or removed. This is the lowest-risk subset and
  can ship entirely independently of the backdoor decision.
- **`job_fit.py`** is a downstream consumer of `dimension_profile` as a
  scoring input — unaffected by steps 2-5 (that field is untouched), and
  if step 1 is taken, it would see the same `.probed`-driven changes
  `COVERAGE_REACHABILITY_AUDIT.md` already analyzed — worth a dedicated
  check before step 1 ships, not assumed safe.
- **`rank_candidates()`'s sort key** (`-competence_score, -weighted_evidence_score`)
  is untouched regardless of which steps are taken — neither depends on
  `.probed` or the new composite field.

### Test plan

1. New unit tests for the composite-aggregation function: each of the
   three clusters correctly groups its member dimensions; renormalization
   excludes unprobed members from both numerator and denominator (direct,
   isolated proof the new function does not inherit `claim_score()`'s
   defect); a cluster with zero probed members reports `Unknown`, not a
   numeric zero.
2. New unit tests for the confidence/coverage-state tag: all four states
   (`Unknown`, `Not Demonstrated`, `Declined`, `Closed-with-confidence`)
   produced from constructed fixtures matching each real condition.
3. Regression: full existing suite (545 tests as of the last two Phase 2
   merges) passes unmodified — proves `claim_score()`,
   `candidate_dimension_profile()`, `weighted_evidence_score()`,
   `rank_candidates()`'s sort order, and `job_fit.py`'s existing behavior
   are byte-identical.
4. **If step 1 is taken:** a dedicated before/after test on real or
   fixture data showing `probed_dimensions` drops for claims whose only
   "probed" dimensions were backdoor-credited — this is the one test that
   directly proves the fix, not just the absence of regression.
5. Integration test: `build_candidate_graph()` returns both the legacy
   `dimension_profile` and the new composite field populated, for the
   same candidate, in one call — proves the additive field doesn't
   displace or corrupt the existing one.

### Rollback plan

- **Steps 2-5 (additive path):** remove the new field from the schema and
  the one new call site in `build_candidate_graph()`; delete the new
  aggregation function. No stored data migration needed — nothing
  persisted changes shape, since the new field is computed fresh on each
  graph build, not stored (unless a later decision adds it to the
  `Profile` cache, which is not part of this plan).
- **Step 1 (backdoor fix), if taken:** revert the one-line expression in
  `signals.py:746`; existing `ClaimScore` rows will read the old
  (inflated) `.probed` values again on their next recompute. No destructive
  migration occurs either direction — `probed_dimensions` and `.probed`
  are recomputed from stored `AnswerSignals`/`responses.signals_json` on
  every `recompute_claim()` call, not derived irreversibly, so reverting
  the flag's logic and re-running recompute restores the prior numbers
  exactly.
