# job_fit.py `gate_open` Defect — Verification

Verification only. No fix applied, none proposed here.

## Verdict

**Confirmed. A real, reachable defect that returns HTTP 500, and the Phase 2A
backdoor fix raised its frequency roughly tenfold.**

`api/engine/job_fit.py:107`:

```python
dim_scores.append(dp.score if dp.probed or dp.gate_open else 0)
```

## 1. Is the earlier report correct?

Yes, with one correction: the introducing commit is **`e70f52d`** (2026-09-09,
"implement explainable Job Fit Ranking layer"), confirmed by `git blame` and
`git log -S"dp.gate_open"`. My earlier note naming `c682102` was wrong; it is
corrected in `SIGNAL_AGGREGATION_PREDICTION_VALIDATION.md`. The line has never been
edited since it was written.

## 2. Does `DimensionScore` lack `gate_open`?

Yes. `schemas.py:322-331` defines `dimension, score, signal_count, basis, quotes,
probed` and nothing else. The only other `gate_open` in `api/` is a **parameter** of
`signals._score()` (`signals.py:135`) that decides whether a ceiling applies; it is
never stored on the returned `DimensionScore`. Pydantic v2 raises
`AttributeError: 'DimensionScore' object has no attribute 'gate_open'`, observed
directly.

## 3. Why do only some candidates fail?

`dp.probed or dp.gate_open` short-circuits when `probed` is True, so the missing
attribute is evaluated **only when a requested dimension is unprobed** on the
candidate's `dimension_profile`. It is also evaluated only for `COMPETENCY`
requirements, which map to dimensions (`COMPETENCY_MAP`).

Measured on the recomputed 68-candidate set, same JD requirements
(Ownership + Judgment):

| Candidate | HTTP | Why |
|---|---:|---|
| `c_b05b4b` | **500** | OWNERSHIP `probed=False` (its OWNERSHIP score is 18, so evidence exists, but no ownership-targeting move was asked) |
| `c_7e712c` | 200 | ADAPTABILITY is unprobed, but it was not requested |

So failure depends on **which dimensions the JD asks for × which the interview
happened to probe**.

## 4. Is it reachable in production?

Yes.

- `routers/job_fit.py` is mounted (`main.py:107`, prefix `/api`).
- `POST /api/job-fit` and `POST /api/job-fit/rank` both call `calculate_job_fit`.
- Reproduced through the real app with FastAPI's `TestClient`: **500 Internal
  Server Error** for the failing candidate.
- **One bad candidate poisons a batch.** `/job-fit/rank` with `[bad, good]` returned
  500; with `[good]` alone, 200. There is no per-candidate handling.
- The requirement source does not protect it. Even the offline heuristic JD
  extractor emits `COMPETENCY` items (e.g. "Ownership", "Problem Solving",
  "Execution", "General Competence"), and LLM extraction can too.
- `tests/test_job_fit.py` builds every dimension with `probed=True`, so no test
  reaches the branch.

## 5. Does the backdoor fix increase frequency?

**Yes, measured.** Same signals, same code, same JD requirements, only the one
`probed` line differs (shipped vs. restored `or entry.score > 0`):

| Sample | Candidates | job-fit raises, **without** backdoor fix | **with** (shipped) |
|---|---:|---:|---:|
| Phase 3 study | 68 | 0 | **19** |
| proofscreen | 8 | 2 | **8** |
| evident | 4 | 1 | **4** |
| **Total** | **80** | **3 (3.8%)** | **31 (38.8%)** |

The `or entry.score > 0` clause had been masking the bug: any dimension with a
nonzero score counted as probed. Removing it (correctly, per
`V2_SCORING_BACKDOOR_FIX.md`) exposed the dormant defect. The backdoor fix itself is
not at fault; its consumer trace missed this read of `probed`.

The job-fit requirement set here is a stand-in (Ownership 35 / Judgment 35 /
Leadership 30 in the batch run; Ownership 50 / Judgment 50 in the HTTP repro), so
the 38.8% depends on which dimensions a JD requests. A JD asking only for Execution
would almost never fail.

## Caveats

- Samples are simulated-persona interviews with re-extraction; rates describe those,
  not live traffic.
- I did not verify what the original author intended by `gate_open` and make no
  claim about the right behavior.
- `V2_SCORING_BACKDOOR_FIX.md`'s consumer trace did not list `job_fit.py`. I did not
  re-audit that trace for other missed readers of `probed`.

## Resolution (applied)

`job_fit.py:107` is now `dp.score if dp.probed else 0`: an unprobed dimension
contributes 0, as `claim_score()` and the absent-dimension branch already do.
`gate_open` never existed on `DimensionScore` (absent at `e70f52d`), and the test
helper's `gate_open=True` was silently dropped by Pydantic, which is why the
author's tests could not see it. Crediting unprobed scores instead would reopen the
`or entry.score > 0` backdoor Phase 2A closed. 7 regression tests added to
`tests/test_job_fit.py`: 6 failed before the fix (including the HTTP 500), all pass
after. Full suite 569 -> 576 passing. On the 80-candidate corpus: job-fit raises
31 -> 0, and 0 previously computable job-fit values changed.
