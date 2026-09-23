# Claim Type ROI Validation Audit

**Question asked:** among all 143 raw claims found by `CLAIM_EXTRACTION_AUDIT.md`,
if we actually simulated interviewing them, which claim *categories* would
maximize evidence yield per question budget? Not extraction quality, not
planner quality, not scoring quality in the abstract — just: which claims
deserve interview budget?

**Answer, in one line:** almost none of the yield variance is explained by
claim category. Category explains **9.6%** of the spread in simulated claim
score; the other **90.4%** is within-category. The reason is structural, not
a property of any category: under the real 2-question-per-claim budget,
**every claim in this dataset — regardless of type or archetype — is asked
the same first two moves**, and those two moves systematically starve the
same dimension (`OWNERSHIP`) for every category alike. Re-ranking which
*categories* get interview budget will not fix evidence yield, because the
planner does not differentiate by category in the window that budget
actually covers.

## 0. Method — real simulated interviews, not estimates

Consistent with this audit series' standing practice
([[proofscreen-audit-verification-practice]]), this was run as real code
against real (if simulated) data, not inferred from the claim text alone.

For each of the 143 raw claims from `CLAIM_EXTRACTION_AUDIT.md`'s live
re-extraction (`inventory_extraction` in `claim_extraction_rerun.json`, one
entry per claim, each carrying its candidate's real `resume_excerpt` and
`job_family`):

1. **Real anatomy + archetype.** `api.engine.anatomy.analyse(claim_text,
   metric)` — the same function the orchestrator calls in production
   (`orchestrator.py:293`).
2. **Real ladder, real budget.** `question_engine.ARCHETYPE_LADDER[archetype]`
   (`api/engine/question.py:1266`), first **2** moves — `settings.
   demo_max_questions_per_claim = 2` (`api/config.py:51`), matched to the real
   corpus's own observed average of 2.12 questions/claim (212 questions / 100
   claims, `studies/evidence_export_prod/00_full_dataset.json`).
3. **Real question generation.** `question_engine.generate_forensic_question()`
   (`api/engine/question.py:1700`) — the actual LLM #2 call, with the actual
   `validate()` gate, the actual two-attempt retarget logic, and the actual
   Python fallback if both attempts fail.
4. **Simulated candidate answer.** One live LLM call per question, role-playing
   the candidate from their own `resume_excerpt`, mirroring the prompt shape
   of the repository's own established simulator
   (`scripts/interview_study.py:373`, `_simulate_answer`) rather than
   inventing an unrelated methodology.
5. **Real evidence extraction.** `evidence_engine.score_response()`
   (`api/engine/evidence.py:430`) — the actual LLM #3 call, with the actual
   verbatim-quote enforcement (dropped 1-2 non-verbatim signals live during
   the run — that is `enforce_verbatim()` working, not a script defect).
6. **Real scoring.** `signals.score_claim()` (`api/engine/signals.py:697`) and
   `scoring.claim_score()` (`api/engine/scoring.py:119`) — the exact functions
   production uses, over the accumulated two-answer signal set.

143/143 claims completed with zero unhandled exceptions. Full per-claim
transcripts, per-question signal counts, and per-dimension scores are at
`claim_roi_simulation_results.json` (scratchpad).

**What this method cannot claim:** these are LLM-simulated candidates, not
real ones — the same limitation the repository's own Phase 3 validation study
carries and states explicitly. It measures what the *planner and scoring
pipeline do with a plausible answer*, not what a real candidate would say.
Given the finding turns out to be about which move gets asked rather than
about answer content, this limitation does not weaken the headline finding —
the move that never gets asked would not get asked regardless of who answers.

## 1. The category label barely moves the outcome

| claim_type | n | avg score | median | avg signals | signals/question |
|---|---:|---:|---:|---:|---:|
| system_ownership | 41 | 73.6 | 75.0 | 13.17 | 6.59 |
| delivery | 43 | 71.7 | 73.0 | 12.35 | 6.17 |
| performance_work | 8 | 73.2 | 77.0 | 14.38 | 7.19 |
| hiring_delivery | 7 | 74.3 | 73.0 | 14.00 | 7.00 |
| outcome_ownership | 7 | 68.6 | 72.0 | 13.29 | 6.64 |
| business_impact | 13 | 66.0 | 70.0 | 11.54 | 5.77 |
| tech_depth | 6 | 62.3 | 57.5 | 13.83 | 6.92 |
| team_handling | 3 | 85.3 | 92.0 | 16.67 | 8.33 |
| modelling | 3 | 63.3 | 73.0 | 13.00 | 6.50 |
| process_work | 2 | 72.5 | 72.5 | 12.00 | 6.00 |
| (7 more types at n≤2) | — | — | — | — | — |
| **overall** | **143** | **72.0** | — | **13.03** | **6.52** |

Every category with n≥3 falls between 62.3 and 85.3 average score — a 23-point
band around a 72.0 overall mean. `CLAIM_PRIORITIZATION_AUDIT.md` documented
`system_ownership` scoring highest and `process_work` lowest **among claims
that survived the current one-per-type selection cut** (i.e., in the
production data actually collected). Simulated head-to-head, on the raw,
unselected inventory, that ordering does not reproduce cleanly:
`system_ownership` and `delivery` — the two largest, most heavily-selected
categories today — sit in the *middle* of the simulated range, not the top.
`team_handling` (n=3) tops it; the categories with the fewest surviving
production examples are not the categories the simulation ranks worst.

**Variance decomposition** (one-way ANOVA-style split of total claim-score
variance): sum of squares between claim_type groups = 2,808 of 29,286 total =
**9.6%**. The remaining 90.4% is variance *within* a category — two claims of
the identical `claim_type` are, on average, far more different from each
other in simulated yield than two claims of *different* types are on average.
**Claim category is a weak predictor of simulated evidence yield.**

## 2. Why: the planner asks the same two questions to (almost) every claim

`ARCHETYPE_LADDER` (`api/engine/question.py:1266`) has five entries — one per
`Archetype` (`METRIC_MOVE`, `OWNERSHIP`, `BUILD`, `PROCESS`, `VOLUME`) — and
every single one of them **opens on `Move.OPERATING_CONTEXT`, then
`Move.FAILURE`, then `Move.PERTURB`**, in that order, before the archetype-
specific moves begin at position 4. `move_available()`
(`api/engine/question.py:1459`) returns `True` unconditionally for both
`OPERATING_CONTEXT` and `FAILURE` — no precondition, no seniority gate
(`LEVEL_RESTRICTED`, `api/engine/question.py:1094`, only restricts `AUTHORITY`,
`EXCLUSION`, `PERTURB`).

The practical consequence, confirmed directly in this run: **at
`demo_max_questions_per_claim = 2`, every one of the 143 claims — of every
archetype, of every claim_type — was asked `OPERATING_CONTEXT` then
`FAILURE`, and nothing else.** The claim's category, its archetype, and its
seniority all become irrelevant to question selection the moment the budget
is 2. They only start to matter at question 3+ (`PERTURB`, then the
archetype-specific branch) — budget the real system spends on barely more
than 1 in 10 claims: the corpus average is 2.12 Q/claim, meaning most claims
never reach move 3 in practice either.

This also means the five-archetype classification carries less signal than
its cardinality suggests here: **92 of 143 raw claims (64%) classified as
`PROCESS`** regardless of `claim_type` (33/43 `delivery`, 23/41
`system_ownership`, 10/13 `business_impact`, 7/8 `performance_work` — see
full crosstab in the scratchpad analysis). Archetype and claim_type are two
labels sitting on top of a planner that, within the actual budget most claims
receive, does not consult either.

## 3. What the two universal moves systematically starve — for every category alike

Per-dimension outcome across all 143 simulated claims:

| dimension | avg score | probed rate | zero rate |
|---|---:|---:|---:|
| EXECUTION | 97.3 | 100.0% | 0.0% |
| KNOWLEDGE | 92.3 | 100.0% | 0.0% |
| ADAPTABILITY | 85.6 | 99.3% | 0.7% |
| PROBLEM_SOLVING | 63.4 | 100.0% | 7.0% |
| JUDGMENT | 18.2 | 85.3% | 14.7% |
| **OWNERSHIP** | **12.7** | **51.7%** | **48.3%** |

`OPERATING_CONTEXT` and `FAILURE` reliably saturate `EXECUTION`, `KNOWLEDGE`
and `ADAPTABILITY` (all ≥85 average, effectively a ceiling — there is no more
ROI headroom left on these three for *any* category under this budget).
`OWNERSHIP` is left unprobed on **48.3% of all 143 claims**, and scores near
zero (12.7/100 average) even where it is nominally probed. `JUDGMENT` fares
only slightly better. This is not a `claim_type` effect — it reproduces
inside every category with n≥3 (`OWNERSHIP` probed rate: `tech_depth` 0.0%,
`performance_work` 12.5%, `modelling` 33.3%, `business_impact` 38.5%,
`outcome_ownership` 42.9%, `delivery` 53.5%, `system_ownership` 56.1%,
`hiring_delivery` 71.4%, `team_handling` 100.0% — a range that tracks
individual claims' phrasing, not their type label).

`OWNERSHIP` reaches an eliciting move (`OWNERSHIP_BOUNDARY`, `AUTHORITY`,
`PEOPLE`) only at ladder position 4+ in every archetype except `OWNERSHIP`
itself — outside the 2-question budget. Where `OWNERSHIP` *does* register a
nonzero score without an ownership-targeted move having been asked, it is the
`score > 0` backdoor in `signals.py:746` (`entry.probed = dimension in probed
or entry.score > 0`) firing on incidental first-person language inside the
`OPERATING_CONTEXT`/`FAILURE` answers — not the planner deliberately probing
it. Because `scoring.claim_score()`'s `total_weight`
(`api/engine/scoring.py:135`) sums all six dimension weights unconditionally,
an unprobed `OWNERSHIP` does not get excluded from the denominator — it is
simply forfeited to zero, dragging every claim's score down by a fixed amount
that has nothing to do with what the claim was about.

## 4. The extraction audit's "achievement-shaped" claims underperform in simulation — the opposite of what their framing implied

`CLAIM_EXTRACTION_AUDIT.md` (Q4) flagged achievement-shaped claims (8.4% of
the raw inventory) as the strongest, most underrepresented evidence category.
Simulated head-to-head, on this dataset, they perform **worse**, not better:

| tag (from `CLAIM_EXTRACTION_AUDIT.md`'s tagging) | n | avg score | delta vs. rest |
|---|---:|---:|---:|
| `achievement` / `outcome` (identical 10-claim set) | 12 rows | 65.1 | −7.6 |
| `dependency` | 4 | 62.2 | −10.0 |
| `constraint` | 1 | 77.0 | +5.0 |
| `ownership` (resume-language tag) | 21 | 73.4 | +1.7 |
| `responsibility_only` | 6 | 81.3 | +9.7 |

Reading the transcripts explains why (three lowest achievement-shaped
examples, e.g. *"Reduced resume extraction time by 66.67% for Lagoon"*, score
39–42): the simulated answers are genuinely rich — concrete causal chains,
named tools, a believable incident for `FAILURE` — and this is exactly what
drives `KNOWLEDGE`/`EXECUTION`/`ADAPTABILITY` to 60–100. But an achievement
statement gives `OPERATING_CONTEXT` and `FAILURE` nothing ownership-shaped to
land on, so `OWNERSHIP` stays at 0 in most of these (confirmed on the three
lowest-scoring examples directly). `responsibility_only` claims — plain duty
statements like *"Managed daily sales operations..."* or *"Oversaw the
prototyping phase..."* — score 81.3 on average precisely because 4 of 6 of
them get `OWNERSHIP` probed with a nonzero score (17–50) via the same
first-person-language route, dragging their total up rather than down.

This is a direct, evidence-based conflict with the earlier audit's framing,
named per this series' standing practice rather than silently reconciled: an
achievement-shaped claim is stronger *evidence of the achievement itself*,
but it is not a stronger candidate for *interview yield under the current
planner*, because the planner's first two moves are not built to extract
ownership from an achievement statement — they are built to extract process
and context, which achievement statements already supply on the page.

## 5. Direct answer to the question asked

**"Which claim categories would maximize evidence yield per question
budget?"** — under the current planner (`ARCHETYPE_LADDER`,
`demo_max_questions_per_claim = 2`), this is close to the wrong axis to
optimize. Claim category explains 9.6% of yield variance; it cannot be used
to reliably route interview budget, because the two questions every category
actually receives are identical regardless of category. Ranking `delivery`
above `process_work` (or any other category-vs-category ordering) inside a
claim-selection or claim-weighting mechanism will not change what gets
extracted, because selection happens on a label the planner does not consult
within the budget that label would be used to justify.

What the 90.4% within-category variance does correlate with, on this data:
whether the claim's own phrasing gives `OPERATING_CONTEXT`/`FAILURE` a
first-person, ownership-shaped answer to land on (`responsibility_only`,
`+9.7` vs. the rest) versus a bare achievement/outcome statement that these
two moves cannot convert into an `OWNERSHIP` reading (`achievement`/`outcome`,
`−7.6`). That is a property of individual claim phrasing, not of the
`claim_type` taxonomy `default_claim_weights()` and `claim_strength_bonus()`
currently select on.

## 6. Scope discipline — what this audit does not claim

Per the brief's own scope: this is not a verdict on extraction quality
(`CLAIM_EXTRACTION_AUDIT.md`), planner design (`PLANNER_STRATEGY_AUDIT.md`,
`COVERAGE_REACHABILITY_AUDIT.md`), or scoring formula correctness
(`SCORING_SEMANTICS_AUDIT.md`, `DIMENSION_VALIDITY_AUDIT.md`) — those are
covered elsewhere and are cited, not re-litigated, here. This audit answers
exactly one question: does the claim_type label predict simulated interview
yield well enough to be used as a selection criterion? On this dataset, under
the real budget the production system actually uses, it does not.

**Limitations to weigh before acting on this:** (1) simulated candidates, not
real ones (§0); (2) budget fixed at 2 questions/claim to match the corpus
average — a larger budget would eventually reach the archetype-specific moves
and might restore some category separation, untested here; (3) several
categories have n≤3 (`team_handling`, `modelling`, `tooling`,
`stakeholder_management`, `stakeholder_alignment`, `process_work`, and six
categories at n=1) — their rankings are directional, not statistically
reliable, and are reported for completeness, not as a ranked list to act on;
(4) `resume_excerpt` is the same fixed 600-character truncation used
throughout this audit series (`CLAIM_EXTRACTION_AUDIT.md` §0), so the
simulated answers are grounded in less resume content than a real interview
would have available.
