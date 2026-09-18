# Full Corpus Coverage & Dimension Reachability Audit

**Scope, strictly:** whether the six-dimension competence framework is actually
being measured, corpus-wide, or is structurally unreachable in places. This
document does not evaluate scoring quality, claim extraction, question
wording, evidence-extraction fidelity, or job fit — those are covered
elsewhere (`docs/METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`) and are out of scope
here by request.

## 0. Dataset note — correcting the brief

The brief asked for "all 57 evaluations." No accessible database or export
contains 57. What exists, checked directly:

| Source | Finalized evaluations | Mode |
|---|---:|---|
| `evident.sqlite3` / `proofscreen.sqlite3` / `demo_audit.sqlite3` / `rehearsal.sqlite3` (local dev) | 4 / 8 / 4 / 11 = 27 | mostly `fixture` |
| `studies/phase3/study.sqlite3`, `studies/phase4/study.sqlite3` | 0 (68 and 44 *sessions*, no `Evaluation` rows — that harness never finalizes one) | `live`, but not this entity |
| `studies/evidence_export/` (dry-run export) | 8 | `fixture` (this is the "8-evaluation sample" the brief said not to use) |
| **`studies/evidence_export_prod/`** (production export, generated 2026-09-18 00:47 via `scripts/export_evidence_dataset.py`) | **39** | **all `live`** |

Per the user's direction to use the files present in `studies/evidence_export/`
and `studies/evidence_export_prod/`, this audit runs on **`evidence_export_prod`,
N = 39 finalized, real-LLM (`llm_mode=live`) evaluations** — the largest and
only fully-real dataset available. It is not 57; it is the actual number, and
it is reported here rather than fabricated. 100 claims were interviewed across
these 39 candidates (avg 2.56/candidate), 212 questions asked (avg 5.44/candidate).

**Method.** Every number below is computed directly from
`studies/evidence_export_prod/00_full_dataset.json` (stored `dimension_profile`,
`claims[].turns[].move`, `seniority`) cross-referenced against the live
planner code — `api/engine/anatomy.py` (`analyse`, `Archetype`) and
`api/engine/question.py` (`ARCHETYPE_LADDER`, `LEVEL_RESTRICTED`,
`level_appropriate`, `move_available`, `MOVE_DIMENSIONS`) — imported and run
directly, not paraphrased from memory or docs. Scripts are inline below each
finding's derivation; nothing here is estimated.

---

## 1. Per-dimension probe rate, score distribution, unprobed rate

(As **reported** by the stored `DimensionScore.probed` flag — see §5 for why
this number is not the same as "a targeted question was asked.")

| Dimension | Probed | Unprobed | Probe rate | Mean score (probed) | Median | Zero-score among probed |
|---|---:|---:|---:|---:|---:|---:|
| KNOWLEDGE | 31/39 | 8 | 79.5% | 44.2 | 32.0 | 3/31 |
| EXECUTION | 39/39 | 0 | **100.0%** | 43.6 | 35.0 | 11/39 |
| PROBLEM_SOLVING | 39/39 | 0 | **100.0%** | 15.8 | 0.0 | 20/39 |
| JUDGMENT | 27/39 | 12 | 69.2% | 7.8 | 5.0 | 8/27 |
| **OWNERSHIP** | 20/39 | 19 | **51.3% (lowest)** | 8.3 | 4.5 | 7/20 |
| ADAPTABILITY | 33/39 | 6 | 84.6% | 34.5 | 36.0 | 10/33 |

Two things jump out before any causal analysis: (1) **OWNERSHIP, not
JUDGMENT, is the worst-covered dimension** in the full corpus — the opposite
of what the 8-evaluation sample suggested; (2) PROBLEM_SOLVING is "100%
probed" with a median score of **0** — probed and scored-zero are different
facts (a dimension can be legitimately asked about and still earn nothing),
and 20 of 39 candidates did.

---

## 2. For every unprobed dimension: why, which rule, which move

Each dimension's live openers, read directly from `MOVE_DIMENSIONS`
(`question.py:1151-1173`), filtered to the six scored dimensions:

| Dimension | Opening move(s) | Guaranteed-early? | Seniority-gated? |
|---|---|---|---|
| EXECUTION | `OPERATING_CONTEXT` | **Yes — ladder position 1, every archetype** | No |
| PROBLEM_SOLVING | `FAILURE`, `DEPENDENCY` | `FAILURE` is **position 2, every archetype** | No |
| ADAPTABILITY | `PERTURB` (sole opener) | Position 3, every archetype | **Yes — senior only** |
| KNOWLEDGE | `METRIC_DEFINITION`, `COHERENCE` | No | No, but both are precondition-gated (see below) |
| JUDGMENT | `EXCLUSION`, `AUTHORITY` | No — position 4/5 | **Yes** — `AUTHORITY` needs mid/senior, `EXCLUSION` needs senior |
| OWNERSHIP | `OWNERSHIP_BOUNDARY`, `PEOPLE` | No — position 4/5 | No, but archetype-gated (see below) |

This single table already explains the ranking in §1: **the two 100%-probed
dimensions are the two whose sole/primary opener is a guaranteed opening
move in every archetype's ladder** (`ARCHETYPE_LADDER`, `question.py:1266-1287`).
Everything else depends on either surviving to a later ladder position, a
seniority gate, an archetype-eligibility gate, or a runtime precondition.

For every (candidate, dimension) pair where the stored flag is `probed=False`
(45 pairs across 39 candidates), the proximate cause, computed by walking
that candidate's actual claims through `ARCHETYPE_LADDER` /
`LEVEL_RESTRICTED` / `move_available()`:

| Primary reason | Count | Mechanism |
|---|---:|---|
| **Budget exhausted despite eligibility** | 13 | The opener was in the claim's ladder, seniority allowed it, its precondition was met — and the planner still never reached it in the 6-question ceiling |
| **Archetype excludes the opener on every claim** | 11 | All 11 are OWNERSHIP — none of this candidate's claims classified as `Archetype.OWNERSHIP` or `Archetype.VOLUME`, the only two archetypes whose ladder contains `OWNERSHIP_BOUNDARY`/`PEOPLE` at all |
| **Mixed seniority-gate + archetype-exclusion** | 14 | Mostly JUDGMENT and KNOWLEDGE — no claim both offered the opener in its ladder *and* cleared the seniority bar |
| **Pure seniority gate, on every claim** | 7 | Mostly ADAPTABILITY and JUDGMENT — the opener was in every relevant ladder, but the candidate's seniority (`junior`, or `None`) blocked it everywhere |

By dimension:
- **JUDGMENT** unprobed instances: 7 mixed seniority+archetype, 3 pure seniority gate, 2 budget-exhausted-despite-eligible.
- **ADAPTABILITY** unprobed instances: 4 pure seniority gate, 2 budget-exhausted.
- **OWNERSHIP** unprobed instances: 11 archetype-exclusion, 8 budget-exhausted.
- **KNOWLEDGE** unprobed instances: 7 mixed precondition+archetype (see §4), 1 budget-exhausted.

---

## 3. JUDGMENT — the four specific questions

**3a. Is the 8-evaluation sample's 25% probe rate representative of the
39-candidate corpus?**

**No, but not in the direction that first looks obvious.** The full corpus's
*reported* JUDGMENT probe rate is 69.2% (27/39) — much higher than 25%. But
§5 below shows the reported flag is inflated by a scoring-side backdoor
unrelated to whether a JUDGMENT-targeting question was ever asked. The
**structurally-targeted** JUDGMENT rate — did the candidate's interview ever
actually ask `AUTHORITY` or `EXCLUSION` — is **38.5% (15/39)**. So: the
8-sample's 25% is closer to the truth than the corpus's headline 69.2%
number is, but both are different from the honest structural figure, and the
8-sample (n=8, all-fixture, single-digit sample) is too small to have been a
reliable estimate of anything — it happened to land in the right
neighborhood by chance, not by representativeness.

**3b. How many candidates had seniority = null?**

**1 of 39** (`Abhishek Singh`, `seniority=None`). For that one candidate,
JUDGMENT and ADAPTABILITY were both **0% probed** — an exact, deterministic
match to the code: `level_appropriate()` (`question.py:1101-1116`) returns
`False` for any `LEVEL_RESTRICTED` move whenever `seniority is None`, by
explicit design ("unknown seniority stays disabled rather than defaulting
open"). This is not a statistical finding (n=1) — it is a direct
confirmation that the code behaves exactly as documented.

**3c. How many times was AUTHORITY eligible but not selected?**

Across the 100 interviewed claims, `AUTHORITY` appears in the ladder for
**56** of them (every `OWNERSHIP`, `PROCESS`, and `VOLUME`-archetype claim).
Of those 56:

| Disposition | Count | % of in-ladder claims |
|---|---:|---:|
| Asked | 14 | 25.0% |
| **Blocked by seniority** (`LEVEL_RESTRICTED`, junior or null) | 21 | 37.5% |
| **Eligible, seniority cleared, not selected** | 21 | 37.5% |

(The other 44 of 100 claims are `METRIC_MOVE` or `BUILD` archetype, whose
ladder never contains `AUTHORITY` at all — see §4.)

**3d. How many times was AUTHORITY blocked?**

**21 of 56 in-ladder claims (37.5%)**, purely by `LEVEL_RESTRICTED = {"mid",
"senior"}` — every one of those 21 belonged to a `junior`- or `None`-seniority
candidate. Notably, "blocked" (21) and "eligible-but-not-selected" (21) are
**exactly tied** — meaning seniority gating and plain budget exhaustion are
equally large contributors to `AUTHORITY` never firing, and neither alone
explains most of the gap.

---

## 4. Structural coverage gaps (claim-archetype level, independent of budget)

Claim archetype is decided by a keyword regex over the claim's own text
(`anatomy._archetype()`, `api/engine/anatomy.py:294-305`) at extraction time
— **before any question is planned**. Archetype distribution across the 100
interviewed claims:

| Archetype | Count | % | Contains `OWNERSHIP_BOUNDARY`/`PEOPLE`? | Contains `AUTHORITY`? | Contains `EXCLUSION`? |
|---|---:|---:|:---:|:---:|:---:|
| BUILD | 37 | 37% | No | No | Yes |
| PROCESS | 35 | 35% | No | Yes | Yes |
| OWNERSHIP | 11 | 11% | Yes | Yes | No |
| VOLUME | 10 | 10% | Yes | Yes | No |
| METRIC_MOVE | 7 | 7% | No | No | Yes |

**79 of 100 claims (79%) — every `BUILD`, `PROCESS`, and `METRIC_MOVE` claim
— can never have `OWNERSHIP_BOUNDARY` or `PEOPLE` asked, at any budget,
because those moves are absent from their archetype's ladder entirely.**
This is not a planner failure or a seniority gate; it is decided the moment
a claim's verb ("built," "deployed," "implemented" → BUILD; a bare metric →
METRIC_MOVE) is regexed at extraction time. This single fact is the primary
cause of OWNERSHIP being the worst-covered dimension in §1 — it is not
mainly a question-budget problem, it is a claim-classification problem
upstream of any question ever being planned. (This is the same
archetype-classification mechanism, applied at a different layer, as the
claim-*selection* vocabulary-sensitivity already flagged in
`METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md` §0/C2 — a candidate's wording choice,
not their competence, decides which dimensions can even be reached.)

Similarly for `KNOWLEDGE`'s openers: `METRIC_DEFINITION` requires
`anatomy.has_metric` (`move_available()`, `question.py:1468-1469`), true for
only the 7 `METRIC_MOVE` claims by definition, and `COHERENCE` requires
`seam_pair(ledger) is not None` — a runtime condition needing two `MID`/`DEAR`-
cost facts from *different* answers sharing a referent
(`question.py:1364-1412`), which most 1-2-question claims never generate
enough material to produce. `KNOWLEDGE`'s 79.5%-reported / 7.7%-structural
gap (§5) is a direct measurement of how rarely this precondition is actually
met versus how often the dimension gets credited anyway.

---

## 5. Planner-level coverage gaps — the `probed` flag overstates targeting

This is the most consequential finding in this audit and needs to be stated
precisely, because it changes what "83% coverage" printed on a candidate
record actually means.

`score_claim()` (`api/engine/signals.py:697-749`) sets:

```python
entry.probed = dimension in probed or entry.score > 0
```

`probed` here is the set of dimensions credited from moves *actually asked*
(via `MOVE_DIMENSIONS`). But the `or entry.score > 0` clause means **any
incidental nonzero score — a candidate volunteering decision-like or
causal-like language in an answer to a completely different question — also
marks the dimension `probed=True`**, with no requirement that a targeting
move was ever asked. Measured directly across all 234 (candidate × dimension)
pairs in the corpus:

| | Count | % of all pairs |
|---|---:|---:|
| Reported probed, and a targeting move was actually asked (genuine) | 135 | 57.7% |
| **Reported probed, but NO targeting move was ever asked — credited purely by `score > 0`** | **54** | **23.1%** |
| Reported unprobed (neither route credited it) | 45 | 19.2% |

Per dimension, reported-probed rate vs. **structurally-targeted** rate (a
targeting move was actually asked, at least once):

| Dimension | Reported probed | Structurally targeted | Gap |
|---|---:|---:|---:|
| KNOWLEDGE | 79.5% | **7.7%** | **72.8 pp** |
| JUDGMENT | 69.2% | 38.5% | 30.8 pp |
| OWNERSHIP | 51.3% | 20.5% | 30.8 pp |
| ADAPTABILITY | 84.6% | 79.5% | 5.1 pp |
| EXECUTION | 100.0% | 100.0% | 0.0 pp |
| PROBLEM_SOLVING | 100.0% | 100.0% | 0.0 pp |

EXECUTION and PROBLEM_SOLVING show zero gap for the reason already given in
§2 — their openers are guaranteed early moves, so "targeted" and "reported"
coincide by construction. Everywhere else, a meaningful share of "coverage"
is the scoring rubric picking up incidental language, not the planner
deliberately probing that competency. **KNOWLEDGE is the extreme case: four
out of every five candidates the system reports as "KNOWLEDGE probed" never
actually received a KNOWLEDGE-targeting question at all.**

This directly changes the corpus-level coverage picture:

| | Mean | Median | All 6 dimensions genuinely reached |
|---|---:|---:|---:|
| **Reported** coverage (stored `probed` flag) | 80.8% | 83.3% | 14/39 (35.9%) |
| **Structural** coverage (a targeting move was actually asked) | **57.7%** | **50.0%** | **2/39 (5.1%)** |

A recruiter reading "5 of 6 dimensions probed" on a candidate record is, on
the median real interview in this corpus, seeing a number that is roughly
33 percentage points more generous than what was actually, deliberately
asked about.

---

## 6. Per-evaluation coverage %

Reported vs. structural coverage, all 39 candidates (grouped; full per-candidate
detail is in the analysis scripts this document was generated from — every
number here is reproducible from `00_full_dataset.json`):

| Reported coverage | Candidates | Structural coverage | Candidates |
|---|---:|---|---:|
| 100% (6/6) | 14 | 100% (6/6) | 2 |
| 83% (5/6) | 13 | 66% (4/6) | 15 |
| 66% (4/6) | 7 | 50% (3/6) | 19 |
| 50% (3/6) | 2 | 33% (2/6) | 3 |
| 33% (2/6) | 3 | — | — |

The lowest-coverage real interviews (structural ≤ 50%) include both junior
candidates with a single interviewed claim (Deepali, Jitender — 2 questions
total, 33% either way) and candidates who *look* fully covered on the
reported number but are not structurally: Srishti, Ayush, and Manya are each
reported at 100% coverage while their structural coverage is 50% — three of
six competencies were never actually asked about despite the record reading
"complete."

---

## 7. Top 10 reasons dimensions remain unprobed

Ranked by how many (candidate, dimension) instances each mechanism accounts
for, across both the "reported unprobed" set (§2) and the deeper
structural-targeting gap (§5):

1. **The `score > 0` scoring backdoor** (`signals.py:746`) credits `probed=True` for 54 (candidate, dimension) pairs with no targeting move ever asked — the single largest contributor to the gap between what's reported and what's real.
2. **Claim archetype (a resume-text regex) never offers `OWNERSHIP_BOUNDARY`/`PEOPLE`** for 79% of claims (`BUILD`/`PROCESS`/`METRIC_MOVE`) — the dominant, budget-independent cause of OWNERSHIP's low coverage.
3. **`AUTHORITY` is seniority-gated to mid/senior**, blocking it outright on 21 of 56 in-ladder claims (37.5%), all belonging to junior/null-seniority candidates.
4. **`EXCLUSION` is seniority-gated to senior only** — blocked on 58 of 79 in-ladder claims (73.4%), the single most-blocked move in the entire ladder.
5. **`PERTURB` (the sole ADAPTABILITY opener) is seniority-gated to senior only** — blocked on 47 of 100 claims (47%), despite appearing in every archetype's ladder.
6. **Budget exhaustion on eligible, unblocked moves** — 21/56 `AUTHORITY`-eligible, 15/79 `EXCLUSION`-eligible, and 22/100 `PERTURB`-eligible claims simply never got there before the 6-question ceiling, with everything else equal.
7. **`METRIC_DEFINITION` requires a metric already present on the claim** — only 7% of claims qualify by construction, regardless of interview quality.
8. **`COHERENCE` requires two `MID`/`DEAR`-cost facts from different answers sharing a referent** — a compounding runtime precondition that a 2-question-per-claim budget rarely accumulates enough material to satisfy.
9. **Breadth-first-then-depth planning** (`plan_next_forensic`, `orchestrator.py:2217-2317`) guarantees every claim's opening move (`OPERATING_CONTEXT`, `FAILURE`, `PERTURB`) before any claim's fourth-plus-position move — so anything beyond ladder position 3 competes for a shrinking remainder of a fixed 6-question budget split across up to 3 claims.
10. **`seniority = None`** disables every `LEVEL_RESTRICTED` move simultaneously (`AUTHORITY`, `EXCLUSION`, `PERTURB` all at once) rather than defaulting open — a single missing metadata field removes JUDGMENT and ADAPTABILITY reachability entirely for that candidate, confirmed exactly in the one such case in this corpus.

## Structural coverage gaps (summary)

- OWNERSHIP is unreachable via its intended openers on 79% of claims purely from archetype classification, independent of seniority or budget.
- JUDGMENT and ADAPTABILITY are jointly gated by the same three-move seniority list (`AUTHORITY`, `EXCLUSION`, `PERTURB`); a junior or unknown-seniority candidate (18 of 39 candidates, 46%) faces a materially harder path to both dimensions regardless of how the interview goes.
- KNOWLEDGE's two openers both carry claim-specific runtime preconditions (a stated metric; an emergent cross-answer seam) that most claims never satisfy — its high *reported* rate is almost entirely the scoring backdoor, not the intended mechanism working.

## Planner-level coverage gaps (summary)

- Breadth-first-then-depth ordering means a 6-question/≈2.56-claim interview spends roughly half its budget on guaranteed opening moves before any claim reaches ladder position 4+, where JUDGMENT's and OWNERSHIP's openers live.
- `AUTHORITY`, `EXCLUSION`, and `PERTURB` eligible-but-unselected rates (37.5%, 19%, 22%) show the planner is not fully using the budget it does have on unblocked, eligible moves — this is a scheduling gap, separate from the seniority and archetype gates.

## Metadata dependencies causing coverage failures

- **`seniority`** is the single highest-leverage metadata field in this entire audit: it gates 3 of 9 moves, covering 2 of 6 dimensions (JUDGMENT, ADAPTABILITY) either fully or partially, and a `null` value disables all three simultaneously rather than defaulting to any permissive behavior.
- **Claim `text` wording** (via the archetype regex) is a de facto second metadata dependency: a claim's own resume phrasing, not the candidate's actual role scope, determines whether OWNERSHIP's openers are ever eligible.
- **`metric` presence on a claim** gates `METRIC_DEFINITION` outright; a claim extracted without a numeric metric field (see the companion methodology audit's extraction findings) can never open KNOWLEDGE via its primary intended route.

---

## Answer to the success criterion

> **Can the current interview methodology reliably reach all six competence
> dimensions within the existing question budget?**

**No.** Across 39 real interviews, only 2 (5.1%) genuinely, deliberately
targeted all six competence dimensions; the median real interview
structurally reached 3 of 6. The two dimensions the system reports as
reliably covered — EXECUTION and PROBLEM_SOLVING, both effectively 100% —
owe that entirely to being the guaranteed first two moves in every claim's
ladder, not to the budget being sufficient in general. The other four
dimensions each fail for a distinct, structural reason independent of any
single candidate's answers: OWNERSHIP is excluded by claim-archetype
classification on 79% of claims before a question is ever planned; JUDGMENT
and ADAPTABILITY are jointly blocked by seniority gating for any junior or
seniority-unknown candidate (46% of this corpus); and KNOWLEDGE's apparent
79.5% coverage is real only 7.7% of the time — the rest is a scoring-side
side effect, not a targeted question. The reported per-candidate "coverage"
number that a recruiter would see materially overstates how much of the
framework was actually, deliberately probed.
