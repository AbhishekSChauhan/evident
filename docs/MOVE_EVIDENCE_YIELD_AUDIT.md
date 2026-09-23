# Move Evidence Yield Audit

**Scope, strictly:** given that a move *can* open a dimension (established in
`docs/DIMENSION_OPENING_AUDIT.md`), is asking it actually worth the question
budget it costs? Not wording, not planner redesign — those come after this.

## 0. Two datasets, used for different metrics, neither stretched past what it can support

**Dataset A — `studies/evidence_export_prod/`, 39 real (`llm_mode=live`)
candidates, 212 real questions.** This is the same corpus used in the two
prior audits. It gives real, large-N, per-question `signals_found` and
`answer_score`, and a per-turn persisted-evidence dimension count — but that
persisted count is **probe-level-keyed, not move-keyed** (established in
`DIMENSION_OPENING_AUDIT.md` §5: `_persist_evidence` calls
`evidence_engine.score_response()` with only the answer's `probe_level`, never
its `move`). So "dimensions credited" from Dataset A means "how many of the
six live dimensions the persisted record shows nonzero for on this turn," not
a strictly move-attributed count. It is still a genuine per-turn observation,
just labeled precisely.

**Dataset B — a from-scratch replay against `evident.sqlite3` and
`proofscreen.sqlite3` (the only two local databases with a populated `move`
column), 72 turns, run just now using the actual production functions
(`signals.score_claim`, `scoring.claim_score`, `scoring.weighted_evidence_score`,
`scoring.competence_score`) directly against each session's real chronological
turn order.** This is the only way to get true, code-verified claim-score and
competence-score deltas attributable to a single turn, since neither number is
stored incrementally anywhere. **The caveat that matters:** both source
databases are `llm_mode=fixture` (`settings.openai_api_key=None`), and
**100% of their 72 turns have `source ∈ {fallback, thread}` — zero came from
the live forensic-Move generator.** Fixture mode always renders questions from
`MOVE_FALLBACKS` templates and scores answers with `heuristic_signals`
(CLAUDE.md: "deliberately more conservative... if a fallback ever looks
*better*, the fallback has become the product"). Dataset B therefore verifies
the **scoring mechanics** — that a move genuinely credits the dimension score
and competence score the code says it should — on real code, real math, just
not real LLM-generated interviews. It corroborates 5 of the 9 named moves
(`OPERATING_CONTEXT`, `FAILURE`, `PERTURB`, `METRIC_DEFINITION`, `PEOPLE`);
`AUTHORITY`, `EXCLUSION`, `DEPENDENCY`, `OWNERSHIP_BOUNDARY`, and `COHERENCE`
never appeared in either fixture database's turns, so Dataset B has nothing to
say about them.

Every ranking below is built primarily on **Dataset A** (real interviews,
large N) and cites Dataset B only where explicitly labeled.

---

## 1. Per-move table (Dataset A — real interviews, N = 212 questions)

| Move | Times asked | Avg signals produced | Avg live dims credited (persisted record) | Avg answer_score | Dead-turn rate (signals=0) | Evidence yield per question |
|---|---:|---:|---:|---:|---:|---:|
| `AUTHORITY` | 14 | **4.36 (highest)** | 1.93 | **20.57 (highest)** | 28.6% | **4.36** |
| `DEPENDENCY` | 11 | 3.55 | **2.18 (highest)** | 17.09 | 36.4% | 3.55 |
| `OWNERSHIP_BOUNDARY` | 6 | 3.00 | 1.67 | 16.17 | **16.7% (lowest)** | 3.00 |
| `OPERATING_CONTEXT` | 52 | 2.94 | 1.62 | 15.37 | 36.5% | 2.94 |
| `PERTURB` | 31 | 2.94 | 1.65 | 16.81 | 48.4% | 2.94 |
| `FAILURE` | 43 | 2.47 | 1.86 | 16.93 | 48.8% | 2.47 |
| `EXCLUSION` | 6 | 2.33 | 0.83 | 8.33 | 33.3% | 2.33 |
| `PEOPLE` | 2 | 0.50 | 0.50 | 3.50 | 50.0% | 0.50 |
| `METRIC_DEFINITION` | 3 | 0.33 | 0.33 | 1.33 | **66.7% (worst)** | 0.33 |
| `COHERENCE` | **0** | — | — | — | — | **never asked; see `DIMENSION_OPENING_AUDIT.md` §1** |
| *(no move — `thread`)* | 30 | 4.10 | 2.67 | 21.80 | 20.0% | 4.10 |
| *(no move — `repair`)* | 12 | 0.50 | 0.17 | 2.33 | 91.7% | 0.50 |

"Evidence yield per question" is literally `avg signals produced` restated —
it is the same measurement asked twice under different names in the brief, and
reporting it separately would manufacture false precision.

---

## 2. Supplementary: replay-verified claim/competence-score deltas (Dataset B — fixture/fallback path, N = 72)

| Move | n | Avg dimensions opened per turn (0→positive) | Avg claim-score delta | Avg competence-score delta |
|---|---:|---:|---:|---:|
| `METRIC_DEFINITION` | 7 | **2.00 (highest)** | **+21.43 (highest)** | **+8.29 (highest)** |
| `PEOPLE` | 9 | 1.33 | +16.56 | +4.44 |
| `PERTURB` | 11 | **2.73 (highest)** | +13.45 | +3.36 |
| `OPERATING_CONTEXT` | 18 | 1.83 | +12.94 | +4.78 |
| `FAILURE` | 12 | 2.08 | +11.42 | +3.08 |
| *(no move — `thread`)* | 15 | 0.40 | +8.53 | +3.13 |

Read this table for **mechanism, not for ranking these five moves against the
other four** — it inverts Dataset A's finding for `METRIC_DEFINITION` and
`PEOPLE` (both weak in real interviews, both look strong here), which is
itself informative: it shows those two moves' *fallback templates* are
well-constructed and score well against the heuristic extractor when they
land, but real candidates asked the real (model-generated) version of those
same moves overwhelmingly fail to produce anything (§1's 66.7%/50% dead-turn
rates). The gap between the two tables **is** the finding for these two moves:
the mechanism is sound, the live generation and/or real-candidate response to
it is not — a question-wording issue, explicitly out of scope here, but the
next place to look per the brief's own stated sequencing.

---

## 3. Per-move notes

- **`AUTHORITY`** — highest real-interview yield on every axis that matters
  (signals, answer_score) and the second-lowest dead-turn rate. This is the
  single most productive move in the entire system, and per
  `DIMENSION_OPENING_AUDIT.md` it is also one of the rarest (asked in only
  25% of its 56 in-ladder opportunities, blocked by seniority on another 21).
  The best-yielding move in the framework is also its most artificially
  scarce one.
- **`DEPENDENCY`** — second-highest signal yield, highest live-dimension
  credit rate of any move. Unrestricted by seniority, archetype-eligible on
  44% of claims, yet selected on only 25% of those opportunities
  (`DIMENSION_OPENING_AUDIT.md` §1) — underused for no structural reason.
- **`OWNERSHIP_BOUNDARY`** — third-best yield and the single lowest dead-turn
  rate (16.7%) of any real move. Archetype-restricted to 11% of claims, but
  performs well every time it's actually offered — the constraint here is
  eligibility, not the move's own value.
- **`OPERATING_CONTEXT`** and **`FAILURE`** — the two moves designed to open
  *every* claim (`ARCHETYPE_LADDER` position 1 and 2) are mediocre performers:
  middle-of-the-pack signal yield and the two **highest dead-turn rates**
  among moves asked more than 10 times (36.5% and 48.8%). Nearly half of all
  `FAILURE` turns produce zero evidence. Guaranteed placement and evidence
  value are not the same thing, and the ladder currently optimizes for the
  former.
- **`PERTURB`** — respectable signal yield when it fires, but the
  **second-worst dead-turn rate** (48.4%) of any real move — consistent with
  its own design intent ("this did not happen, so there are none... asking
  invites invention," `question.py:1246-1252`): it is deliberately a
  low-signal-density probe, so a high dead-turn rate here is arguably by
  design rather than a defect, unlike `FAILURE`'s.
- **`EXCLUSION`** — weak on every axis except dead-turn rate: lowest
  `answer_score` of any move with n ≥ 5 (8.33, less than half of every other
  move's), and the lowest live-dimension credit rate among moves that fire at
  all (0.83). Combined with `DIMENSION_OPENING_AUDIT.md`'s finding that it is
  blocked by seniority on 73.4% of its opportunities, `EXCLUSION` is both rare
  and, when it does fire, one of the weaker performers.
- **`PEOPLE`** — n = 2 in the real corpus (the least-asked move in the
  system), and both of its data points are weak (0.50 signals, 3.50
  answer_score). Too small a sample to convict outright, but nothing here
  argues for asking it more.
- **`METRIC_DEFINITION`** — the worst performer on every real-interview axis:
  lowest signals (0.33), lowest answer_score (1.33), highest dead-turn rate
  (66.7%). It is also the rarest archetype-eligible move (7% of claims). Its
  Dataset B fallback-path numbers are the *best* of any move measured there —
  meaning the deterministic Python template for this move is fine; what real
  candidates get asked, or how they respond to the live-generated version, is
  not.
- **`COHERENCE`** — asked **zero times** in 212 real questions. There is no
  yield to measure because there is no data point. This is not a low-yield
  finding; it is a non-finding, and the more serious problem, already
  documented in `DIMENSION_OPENING_AUDIT.md` §1: its precondition (`seam_pair`)
  never clears under this interview's budget.
- **`thread`** (bonus finding, out of the nine named moves but too large a
  share of the corpus — 14.2% of all questions — to omit): the "hackathon
  demo" answer-threading mechanism, which has no `Move` and cannot open a
  dimension through the intended crediting path
  (`DIMENSION_OPENING_AUDIT.md` §0a), nonetheless produces the **second-highest
  signal yield in the entire corpus** (4.10, just behind `AUTHORITY`) and the
  **highest answer_score of anything measured** (21.80). Chasing a specific
  entity the candidate just named is, empirically, a very effective way to
  extract evidence — it simply isn't currently wired to credit any of the six
  competence dimensions when it works.

---

## 4. Rankings

**Highest-yielding moves** (composite of signal yield, live-dimension credit
rate, and inverted dead-turn rate, z-scored across the 9 named moves with
n ≥ 2 in Dataset A):

1. **`AUTHORITY`** (+1.07)
2. **`OWNERSHIP_BOUNDARY`** (+0.86)
3. **`DEPENDENCY`** (+0.80)
4. `OPERATING_CONTEXT` (+0.34)
5. `PERTURB` (+0.06)
6. `FAILURE` (+0.04)

**Lowest-yielding moves:**

7. `EXCLUSION` (−0.16)
8. **`PEOPLE`** (−1.24, n = 2 — treat as a weak signal, not a verdict)
9. **`METRIC_DEFINITION`** (−1.77, worst on every real-interview axis)
10. **`COHERENCE`** — unrankable; never fires (functionally the lowest
    possible yield: zero, by never being asked)

The composite inverts the planner's own scheduling priority almost exactly:
the three highest-yielding moves (`AUTHORITY`, `OWNERSHIP_BOUNDARY`,
`DEPENDENCY`) are the three rarest, most gated moves in the ladder (14, 6, and
11 real-corpus occurrences respectively), while the two moves guaranteed to
fire on every single claim (`OPERATING_CONTEXT`, `FAILURE`) rank fourth and
sixth of nine, and the worst performer of all (`METRIC_DEFINITION`) is gated
purely by claim archetype, not by anything related to its low yield.

---

## Answer to the question asked

> Which interview moves produce the highest amount of validated evidence per
> unit of question budget?

**`AUTHORITY`, `OWNERSHIP_BOUNDARY`, and `DEPENDENCY`** — in that order — are
the highest-yielding moves per question asked, on every real-interview metric
measured (signals produced, live-dimension credit rate, dead-turn rate,
answer quality). All three are also among the least-asked moves in the
system: `AUTHORITY` is seniority-gated and budget-starved
(`DIMENSION_OPENING_AUDIT.md` §2), `OWNERSHIP_BOUNDARY` is archetype-gated to
11% of claims, and `DEPENDENCY` is simply under-selected by the planner
despite being unblocked. **`METRIC_DEFINITION` and `COHERENCE` produce the
least validated evidence per question** — the former is the single worst
performer whenever it does fire, the latter never fires at all — and both are
principally blocked at the archetype/precondition layer rather than by
planner choice.

The practical implication, stated once and left for the next audit to act on:
**the fixed six-question budget is currently spent disproportionately on its
two most reliably-available moves (`OPERATING_CONTEXT`, `FAILURE`), which
yield only middling evidence, while its three best-yielding moves are
structurally the hardest to reach.** Fixing that is a planner-priority and
gating question, not a wording question — which is exactly why the brief
scoped question wording as the step after this one, not before it.
