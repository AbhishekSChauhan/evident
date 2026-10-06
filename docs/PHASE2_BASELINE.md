# Phase 2 Baseline

Reference snapshot taken at commit `e95e5cc` on branch `phase2-evidence-fixes`
(2026-10-07). Anything measured **before** these commits is pre-fix; anything
after is post-fix. Every number below cites its source; none was re-derived here
except the test count and version constants, which were read from the tree.

## 1. Commits in this baseline

Each commit passes the full suite on its own (checked in a clean worktree per commit).

| # | Commit | Tests at that commit |
|---|---|---:|
| 1 | `c16fe48` ownership availability fix | 545 |
| 2 | `d272263` extraction recovery (prompt) | 545 |
| 3 | `9048358` merge fix + `rub_3` | 554 |
| 4 | `4bb7491` probed-flag (backdoor) fix | 561 |
| 5 | `36deac0` composite reporting | 569 |
| 6 | `e95e5cc` job-fit crash fix | **576** |

The pre-fix reference is `09ed76f` (**532** tests). Commit 1 adds 13 tests; the first commit's count of 545 is the sum, not the pre-fix figure.

## 2. Versions

| Item | Value | Where |
|---|---|---|
| Tests | **576 passing** | `pytest -q` |
| Rubric | `rub_3` (was `rub_2`) | `signals.py:57` |
| Scoring | `score_1` (**unchanged**) | `scoring.py:45` |
| Question policy | `qpol_3` | `question.py:319` |
| Taxonomy | `tax_1@ff71094e8670` | `/api/health` |
| Composite | **no version constant.** `composite_profile()` is derived, never stored, not hashed into `evaluation_version` | `scoring.py` |

`score_1` was not bumped although merged `constraints` now reach `claim_score()`'s
+5% operational bonus. `rub_3` carries the change into `evaluation_version`, so
finalized evaluations are not silently replayed, but a reader should know the
scoring formula text itself did not change.

## 3. What each fix changed, and the measured status

| Fix | Status | Evidence |
|---|---|---|
| **Ownership availability** | `OWNERSHIP_BOUNDARY` at ladder position 4 for BUILD, PROCESS, METRIC_MOVE. Reached on **29 of 40** claims in the 6-turn live set (BUILD 6/6, PROCESS 6/6, METRIC_MOVE 7/7, OWNERSHIP 10/11, **VOLUME 0/10**). At the 2-question budget it is **never reached** (position 4). | `POST_FIX_ROI_REMEASUREMENT_RERUN.md` §Q5 |
| **Extraction recovery** | Prompt asks for all four buckets. Per-claim presence on the 40-claim live set: decisions 67.5%, constraints 47.5%, concepts 22.5%, boundaries 70.0%. On the 68-candidate Phase 3 corpus: **51.1 / 19.6 / 19.6 / 8.7%**. Density depends on whether the interview asked ownership questions. Heuristic fallback ran on 14.2% of turns; `facts` populated 0 of 240 times. | `SIGNAL_AGGREGATION_AUDIT.md`; `SIGNAL_AGGREGATION_PREDICTION_VALIDATION.md` §2 |
| **Aggregation (merge)** | `merge_signals()` handles **12 of 12** buckets (was 8). Claim-level presence now equals per-answer presence. | commit `9048358`; rerun verdict 1 |
| **Backdoor** | `probed` = targeted only. At the 2Q budget `OWNERSHIP` probed is 0/40 (was 51.7% of 143 in the original ROI audit). | `V2_SCORING_BACKDOOR_FIX.md`; `CLAIM_TYPE_ROI_VALIDATION_RERUN.md` §2 |
| **Composite** | Three clusters (Execution & Knowledge, Reasoning, Ownership) over probed members; unprobed cluster is `UNKNOWN`/`None`. Reporting only; feeds no score or sort key. | `V2_COMPOSITE_REPORTING.md` |
| **Job-fit crash** | Unprobed requested dimension contributes 0. 31/80 candidates raised before, 0 after; 0 previously computable scores changed. | `JOB_FIT_GATE_OPEN_DEFECT.md` |

### Measured effect of the merge fix (the one with a before/after)

| Metric | Audit predicted | Measured (68 candidates) |
|---|---:|---:|
| Claim score | +2.35 | +5.04 |
| Competence score | +2.37 | +4.68 |
| Ownership composite | +32.41 | +3.36 overall; +29.17 where `boundaries` present (n=8) |
| Reasoning composite | +10.19 | +11.63 |
| Job fit | +11.63 | +10.04 (49 computable) |
| Rank position changed | ~85% | 88.2% (86.8% tie-aware) |

Source: `SIGNAL_AGGREGATION_PREDICTION_VALIDATION.md`. A different corpus from the
audit's; read its §0 before comparing.

## 4. How to read older audit numbers

| Audit generation | Meaning |
|---|---|
| Written before `d272263` | Pre-extraction-fix: the four buckets were rarely populated. |
| Written before `9048358` | Pre-merge-fix: buckets extracted but absent from claim scores. Per-answer numbers are valid; claim/candidate numbers are not. |
| Written before `4bb7491` | `probed` inflated by incidental score. Coverage and "dimensions opened" figures are suspect. |
| `CLAIM_TYPE_ROI_VALIDATION_AUDIT.md` | Headline (category explains little) **still holds**; its §3 ownership figures are stale and §4 achievement-vs-responsibility is not re-established. See `CLAIM_TYPE_ROI_VALIDATION_RERUN.md`. |

## 5. Known open defects and gaps

1. **`signals.total_signals()` sums 7 of 12 buckets** (`signals.py:608`). Omits
   decisions, constraints, concept_explanations, boundaries and facts. Feeds yield
   reporting and `signals_found`, not claim scores. Unfixed.
2. **Job fit counts an unprobed requested dimension as 0**, so it appears as MISSING
   and lowers `competence_fit`. `EVIDENT_MASTER_CONTEXT` says a coverage gap is
   Unknown, never Bad; job-fit arithmetic does not yet honour that.
3. **`VOLUME` claims are never offered `OWNERSHIP_BOUNDARY`** (0/10). Deliberate in
   the ladder fix; its consequence is that ownership evidence there arrives only by
   volunteering.
4. **Claim score still divides by all six dimension weights** regardless of probing
   (`V2_CLAIM_SCORE_RENORMALIZATION_PLAN.md`, not implemented).
5. **Extraction is non-deterministic (~23%)** and 14.2% of turns hit the heuristic
   fallback in the live set; absolute bucket density is one draw.
6. **Validation corpora are simulated candidates.** No real-candidate run has
   exercised the recovered buckets.
7. **The audits' original datasets are gone** (`claim_roi_simulation_results.json`,
   the 27-candidate set). Reproducing them requires regeneration.
8. **`/job-fit/rank` has no per-candidate error isolation.** The crash is fixed, but
   any other per-candidate exception still fails the batch.
9. **Pre-existing, outside this baseline:** auth is one shared key per tenant;
   `REQUIRE_API_KEY` defaults false; `profiles` is a mutable score cache; the DPDP
   workstream is untouched (`CLAUDE.md`).

## 6. Not committed

Several documents cited above as sources (for example `SIGNAL_AGGREGATION_PREDICTION_VALIDATION.md`, `POST_FIX_ROI_REMEASUREMENT_RERUN.md`, `CLAIM_TYPE_ROI_VALIDATION_RERUN.md`) are still **untracked**, so this baseline's citations do not yet resolve in git. `docs/` still holds untracked audit and plan documents not cited by any commit
(the remaining validation, re-measurement and methodology reports, plus
`EVIDENT_PRD_1PAGER.md`). `docs/V2_OWNERSHIP_IMPLEMENTATION_PLAN_2.md` is **0 bytes**.
Validation harness scripts live in the session scratchpad, not in the repo.
