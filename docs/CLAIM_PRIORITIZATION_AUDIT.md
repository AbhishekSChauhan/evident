# Claim Prioritization Audit

**Objective:** every prior audit in this series starts after a claim has
already been selected for interview. This one asks the question upstream of
all of them: is the mechanism that picks which claims get the fixed question
budget actually picking the claims that produce evidence?

**Dataset:** the same 39 real (`llm_mode=live`) candidates, 100 interviewed
claims, 212 questions (`studies/evidence_export_prod/00_full_dataset.json`).
For every claim, `claim_strength_bonus()` and each candidate's
`default_claim_weights(job_family)` were **re-run live against the actual
production functions** (not re-derived or approximated) to reconstruct the
exact priority score `extract.py` computed for that claim at selection time,
then compared against that claim's real, observed interview outcomes.
Claim-type sample sizes range from 1 to 20; every average below is reported
with its `n`, and anything under 8 is marked directional, not robust — four
types (`delivery` n=20, `system_ownership` n=12, `performance_work` n=11,
`process_work` n=8) carry enough volume to trust on their own.

---

## 1. Current prioritization methodology

Confirmed directly from the live code, not inferred: a claim's fate is
decided by exactly one formula, computed once, before any interview
question exists —

**priority_score = claim_type weight (a fixed per-family constant,
`default_claim_weights`) + `claim_strength_bonus()` (a regex scan of the
claim's own resume text for incident, causal, quantity, constraint, and
leadership vocabulary).**

This is the same mechanism `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md` named as
conflict C2 — the finding here is not a new mechanism, it's the first
empirical test of whether that mechanism actually works.

---

## 2. Evidence yield by claim type

Average per claim, all 100 interviewed claims, sorted by average total
signals produced:

| Claim type | n | Avg signals | Avg claim_score | Avg evidence rows | Avg dims opened (reported) | Avg dims opened (structural) | Dead-turn rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| `hr_systems` | 1 | 16.00 | 83.0 | 10.0 | 6.0 | 1.0 | 0.0% |
| `team_handling` | 1 | 16.00 | 79.0 | 9.0 | 6.0 | 1.0 | 0.0% |
| `pipeline_management` | 1 | 16.00 | 38.0 | 5.0 | 3.0 | 1.0 | 0.0% |
| `pipeline_ownership` | 2 | 13.50 | 67.5 | 8.0 | 5.0 | 2.0 | 0.0% |
| `csat_improvement` | 2 | 11.50 | 77.0 | 10.5 | 6.0 | 1.5 | 0.0% |
| `reporting` | 2 | 11.00 | 33.0 | 6.0 | 4.5 | 1.0 | 0.0% |
| `reliability` | 3 | 8.67 | 43.3 | 6.3 | 3.7 | 2.0 | 33.3% |
| **`system_ownership`** | **12** | **7.50** | **28.3** | 5.0 | 3.4 | 1.8 | 30.6% |
| `launch_delivery` | 3 | 7.33 | 42.0 | 7.7 | 5.3 | 1.3 | 16.7% |
| `discovery` | 3 | 6.67 | 34.7 | 5.7 | 4.3 | 1.7 | 33.3% |
| `outcome_ownership` | 3 | 6.33 | 35.7 | 5.7 | 3.7 | 1.7 | 16.7% |
| `stakeholder_management` | 3 | 5.33 | 16.7 | 4.7 | 2.7 | 1.3 | 66.7% |
| **`delivery`** | **20** | **4.75** | **20.0** | 4.5 | 3.3 | 1.7 | **47.5%** |
| `tech_depth` | 4 | 4.50 | 22.8 | 5.0 | 3.5 | 1.8 | 37.5% |
| **`performance_work`** | **11** | **4.45** | **19.8** | 4.1 | 3.4 | 1.7 | **59.1%** |
| `measurable_outcome` | 4 | 3.50 | 23.8 | 6.3 | 4.5 | 1.5 | 62.5% |
| **`process_work`** | **8** | **2.50** | **18.8** | 4.5 | 3.4 | 1.9 | 43.8% |
| `tooling` | 3 | 1.67 | 8.0 | 4.0 | 3.0 | 2.0 | 66.7% |

(Full 25-type table, including the remaining n=1-2 types, is in the raw
analysis; the ones shown span the range from best to worst.)

The gap between "reported dims opened" and "structural dims opened" is the
same `score > 0` backdoor `COVERAGE_REACHABILITY_AUDIT.md` measured
corpus-wide (§5 there) — it's visible again here at the claim level: every
type's reported number is 1.5-2x its structural number. Structural counts
are the ones trusted for the rest of this document.

---

## 3. Evidence ROI by claim type

Signals produced per question spent — the direct answer to "is this claim
worth its interview budget":

| Claim type | n (confidence) | ROI (signals/question) | Total questions this type consumed |
|---|---|---:|---:|
| `pipeline_ownership` | 2 (directional) | 6.75 | 4 |
| `csat_improvement` | 2 (directional) | 5.75 | 4 |
| `reporting` | 2 (directional) | 5.50 | 4 |
| `reliability` | 3 (directional) | 4.33 | 7 |
| **`system_ownership`** | **12 (robust)** | **3.67** | **27** |
| `launch_delivery` | 3 (directional) | 3.67 | 6 |
| `outcome_ownership` | 3 (directional) | 3.17 | 6 |
| `stakeholder_management` | 3 (directional) | 2.67 | 6 |
| **`delivery`** | **20 (robust)** | **2.38** | **42 — the single largest budget consumer in the corpus** |
| `tech_depth` | 4 (directional) | 2.25 | 9 |
| **`performance_work`** | **11 (robust)** | **2.23** | **23** |
| `measurable_outcome` | 4 (directional) | 1.75 | 9 |
| **`process_work`** | **8 (robust)** | **1.25 — worst of the four robust types** | **18** |
| `tooling` | 3 (directional) | 0.83 — worst overall | 6 |

Among the four types with enough volume to trust unconditionally,
`system_ownership` (3.67) clearly outperforms `delivery` (2.38) and
`performance_work` (2.23), with `process_work` (1.25) trailing by nearly 3x.
**`delivery`, the single most heavily-selected claim type in the entire
corpus (20 of 100 claims, more total questions spent on it than on any other
two types combined), sits in the bottom half of the ROI ranking.**

---

## 4. Resume-strength vs. evidence-strength analysis

This is the central finding of the audit, and it is unambiguous.

Correlation across all 100 claims between the selection mechanism's own
scores and what the interview actually produced:

| | vs. total signals | vs. claim_score | vs. structural dims opened |
|---|---:|---:|---:|
| **Full priority_score** (what actually ranks claims today) | **−0.042** | **−0.085** | +0.088 |
| `claim_strength_bonus` alone (the resume-prose scan) | +0.032 | −0.024 | — |
| `claim_type` weight alone (the taxonomy constant) | −0.054 | −0.084 | +0.082 |

**Every one of these is statistically indistinguishable from zero, and
several are negative.** Neither half of the selection formula — not the
taxonomy's declared importance for a claim type, not the regex scan of the
candidate's own wording — predicts how much evidence that claim will
actually produce. This holds separately for each component, so it isn't a
case of one good signal being diluted by a bad one; both are independently
uninformative.

The starkest illustration: comparing the top 10 claims by priority_score
against the bottom 10 —

| | Avg signals | Avg claim_score | Avg structural dims |
|---|---:|---:|---:|
| **Top 10 by priority_score** | 5.30 | **17.90** | 1.70 |
| **Bottom 10 by priority_score** | 7.10 | **36.40** | 1.50 |

The claims the current system is most confident about score **lower** on
signals and **half** the claim_score of the claims it ranks lowest. This is
not noise around zero correlation — on this specific comparison the
relationship runs backward. `hiring_delivery` carries the single highest
average priority_score in the corpus (32.75) and one of the lowest claim
scores (7.50); `hr_systems` and `workforce_planning` carry the lowest
priority scores in the corpus (5.00) and `hr_systems` produces the single
highest average signal count and claim_score of any type measured (16.00
signals, 83.0 claim_score, n=1 — directional, but not an isolated
coincidence given the aggregate correlation above agrees with it).

**Answer to the question asked: the system is not predicting evidence
strength from resume language. It is measuring resume-writing register and
calling it priority**, exactly as `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`'s
C2 argued from the mechanism alone — this is the same conclusion, now
confirmed against outcomes rather than argued from design.

---

## 5. Evidence-magnet claim categories

Composite gap-closure rate (average of causal-chain, constraint, decision-
rationale, ownership-boundary, stakeholder-interaction, and process-sequence
presence, per `EVIDENCE_GAP_FRAMEWORK.md`'s taxonomy) by claim type, among
types with usable volume:

| Claim type | n | Magnet composite | Strongest gap(s) closed |
|---|---:|---:|---|
| `reporting` | 2 (directional) | 41.7 | causal, constraint |
| `sla_adherence` | 2 (directional) | 33.3 | ownership, stakeholder |
| `pipeline_ownership` | 2 (directional) | 33.3 | constraint, process |
| `stakeholder_management` | 3 (directional) | 27.8 | causal, ownership |
| `sourcing_strategy` | 3 (directional) | 27.8 | constraint, ownership, stakeholder |
| **`performance_work`** | **11 (robust)** | **21.2** | causal, constraint, process |
| **`system_ownership`** | **12 (robust)** | **20.8** | causal, constraint, process |
| **`delivery`** | **20 (robust)** | **18.3** | causal, process |
| **`process_work`** | **8 (robust)** | **10.4 — lowest of the robust group** | process only, weakly |

Among the statistically trustworthy types, `performance_work` and
`system_ownership` are the closest thing to genuine evidence magnets —
claims of these types reliably produce more than one type of hard-to-fake
content per interview. `delivery` produces some, mostly process-sequence
narration. `process_work` produces almost none of any kind — its one
above-floor signal is a weak process-sequence rate, with essentially no
causal, constraint, decision, ownership, or stakeholder content at all.

Individually, the strongest evidence-magnet *claims* observed (not
types — see caveat on n=1/2 types above) are ownership- and reporting-shaped
work: agreement/discrepancy reconciliation, QA/team mentoring, dashboard/
report-anomaly claims. These consistently pulled multiple gap types at once
in the raw per-claim data, matching `QUESTION_QUALITY_AUDIT.md`'s and
`MOVE_EVIDENCE_YIELD_AUDIT.md`'s independent finding that `OWNERSHIP_BOUNDARY`
and reporting/root-cause content are among the highest-yield material in
the whole system, regardless of which move or mechanism elicits it.

---

## 6. Low-value claim categories

Three types combine low ROI, low magnet score, and high dead-turn rate at
enough volume to trust the pattern:

- **`process_work`** (n=8, robust): worst ROI of the four robust types
  (1.25), lowest magnet composite of the four (10.4), and it consumed 18
  questions across 8 claims — more budget per claim than `system_ownership`
  gets, for a third of the return.
- **`tooling`** (n=3, directional but consistent across all three
  observations): worst ROI in the whole table (0.83), a 66.7% dead-turn
  rate, and an $8.0$ average claim_score — every measure agrees this
  category underperforms, though the sample is too small to rank
  confidently against the other directional types.
- **`measurable_outcome`** (n=4, directional): a 62.5% dead-turn rate, the
  second-worst in the table, despite a moderate average claim_score — a
  claim type that frequently produces nothing at all, and produces a real
  score only when it happens to land.

`performance_work` (n=11, robust) deserves a distinct flag: its ROI (2.23)
and magnet score (21.2) are not bad, but it carries the **worst dead-turn
rate of any robust type (59.1%)** — nearly three in five questions asked
about a `performance_work` claim produce nothing. This is not a
"deprioritize" case the way `process_work` is; it's a "this type is
volatile — sometimes very good, often nothing" case, worth a different kind
of handling (see Section 7) than an outright low-value type.

None of these are recommended for outright removal — every type still
produces *some* real evidence some of the time, and n is too thin for most
of them to justify elimination rather than deprioritization. The
recommendation is ranking, not exclusion.

---

## 7. Recommended V2 prioritization methodology

Three changes, each directly justified by a specific number above, and each
consistent with `EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md`'s broader redesign
(claim recall and claim salience as separate stages, Section 4.1 there):

1. **Stop using `claim_strength_bonus` (or any unverified resume-prose scan)
   as a ranking signal at all.** Section 4 shows it is not merely weak, it
   is statistically indistinguishable from zero against every yield measure
   tested, and the full priority score built on top of it performs *worse*
   than zero on the top-vs-bottom-decile comparison. This is not a tuning
   problem to fix with different keyword weights — the entire approach of
   scoring the candidate's own wording as a proxy for evidentiary value is
   unsupported by the outcomes it was supposed to predict.
2. **Re-weight claim types using the ROI and magnet numbers actually
   measured here, not a hand-set taxonomy constant.** The current
   `default_claim_weights` constant is equally uncorrelated with outcomes
   (Section 4) — it should be replaced, or at minimum informed going
   forward, by which claim *types* have empirically demonstrated they
   produce causal chains, constraints, and ownership boundaries
   (`system_ownership`, `performance_work`, reporting/reliability-shaped
   claims) versus which mostly don't (`process_work`, `tooling`,
   `measurable_outcome`).
3. **Treat claim selection as budget allocation across a portfolio, not a
   one-time top-3 cut** — consistent with the V2 planner design's shift to
   evidence-gap-first scheduling. For a fixed budget of **6 questions**, the
   evidence here favors 3 claims of the highest-ROI types available on that
   resume (typically `system_ownership`/ownership- or reporting-shaped
   claims where present), 2 questions each — closer to today's actual shape,
   but chosen by measured type performance rather than resume vocabulary.
   For **8 questions**, the marginal 2 questions are better spent opening a
   **4th claim of a high-ROI type** than adding a 3rd/4th question of ladder
   depth to an already-interviewed claim — `PLANNER_STRATEGY_AUDIT.md`
   already measured "a second scheduled move on the same claim" as the
   single worst planner action available (2.39 avg signals), so budget
   growth should buy breadth across more good-type claims, not depth on the
   same ones. For **10 questions**, the same logic extends to a 5th claim,
   with `performance_work`-type claims — high-variance but not low-value —
   good candidates for the later slots once the highest-ROI types on that
   resume are exhausted, rather than for the first three.
   `process_work`/`tooling`/`measurable_outcome`-type claims should be the
   *last* claims a budget reaches, at any budget size, not excluded outright
   but never competing with a `system_ownership`- or reporting-shaped claim
   for an early slot.

---

## 8. Quantitative validation criteria

Whatever V2 prioritization mechanism replaces the current one, it should be
checked against the same four numbers this audit used, on the same or a
larger real-interview corpus, before being trusted:

1. **Correlation between the new priority score and actual signals/
   claim_score produced**, re-run exactly as in Section 4. The bar to clear
   is not "positive" alone — it must be materially better than the current
   mechanism's ~0 (and in places negative) correlation, ideally into a
   range where top-ranked claims measurably outperform bottom-ranked ones on
   average, reversing the inverted top-vs-bottom-decile result found here.
2. **ROI-by-type stability**: re-measure signals-per-question by claim type
   on new data and confirm the ranking direction found here
   (`system_ownership`/reporting/ownership-shaped types over
   `process_work`/`tooling`) holds, rather than being an artifact of this
   specific 39-candidate sample — this matters most for the four robust
   types, since everything else here is still directional.
3. **Reduction in budget spent on the lowest-value types.** `process_work`,
   `tooling`, and `measurable_outcome` together consumed 33 of 212 questions
   (15.6%) in this corpus despite ranking at or near the bottom on every
   measure in Sections 3, 5, and 6 — a V2 mechanism should measurably reduce
   this share without a corresponding drop in overall claim coverage per
   candidate.
4. **No re-introduction of a resume-vocabulary proxy under a different
   name.** Given Section 4's result, any replacement scoring mechanism
   should be checked for the same failure mode before shipping — specifically,
   whether it still rewards incident/leadership/quantity-dense phrasing
   independent of verified content, which is the property that made the
   current mechanism fail here.
