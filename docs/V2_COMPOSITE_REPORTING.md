# Phase 2B — Composite Reporting Layer

**Implemented, additive only.** The six dimensions are unchanged in how
they are computed, scored, or stored. This adds one new, derived view over
them.

## What was added

- `CompositeCluster` enum (`EXECUTION_KNOWLEDGE`, `REASONING`,
  `OWNERSHIP`) and `CoverageState` enum (`UNKNOWN`, `NOT_DEMONSTRATED`,
  `DEMONSTRATED`) — `api/schemas.py`.
- `CompositeScore` model — `api/schemas.py`.
- `CandidateGraph.composite_profile: list[CompositeScore]` — a new field
  alongside the existing, untouched `dimension_profile`.
- `scoring.composite_profile()` — the aggregation function:
  renormalizes over **probed members only**, so an unprobed dimension
  contributes to neither the numerator nor the denominator (the exact
  defect `claim_score()`'s `total_weight` still has, left untouched here
  since fixing it was out of scope for this pass). A cluster with zero
  probed members reports `UNKNOWN` with `score=None` — never a numeric
  zero standing in for "never asked."
- One wiring call in `build_candidate_graph()` (`graph.py`) populating the
  new field from the same `dimension_profile` input the existing call
  already produces.

## `DECLINED` was not implemented — named, not silently dropped

A genuine `DECLINED` state (the candidate explicitly passed, vs. probed
and nothing resulted) needs a per-answer non-answer flag
(`evidence.is_memory_exhausted_or_skip()`) that is not currently carried
into the claim-level `DimensionScore` this layer is built from. Adding it
honestly would require either touching extraction/evidence code (out of
scope for this task) or adding new stored data (the task said keep
existing storage). Rather than approximate it with a proxy that can't
actually tell "declined" apart from "demonstrated nothing," it is left out
of `CoverageState` entirely, with the reasoning recorded directly in the
enum's own docstring. Three honest states shipped; a fourth needs a
separate, explicit decision.

## Blast radius

Zero changes to `claim_score()`, `candidate_dimension_profile()`,
`weighted_evidence_score()`, `competence_score()`, or `rank_candidates()`'s
sort key. `job_fit.py` is untouched — it reads `dimension_profile`, which
is computed exactly as before. The new field defaults to `[]` wherever
`CandidateGraph` is constructed without it (e.g. existing test fixtures
that mock the graph), so nothing needed updating.

## Test results

8 new tests (`tests/test_composite_reporting.py`), all passing: cluster
membership, the `UNKNOWN`-vs-`NOT_DEMONSTRATED` distinction, correct
renormalization over probed-only members, the Ownership single-dimension
passthrough, stable output ordering, and graceful handling of a partial
input. Full suite: **560/560 passed** (552 + 8 new), zero regressions.
