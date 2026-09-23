# V2 Minimal Methodology Synthesis — Designing for a 4–6 Question Voice Screen

**Premise, taken as given, not re-litigated:** WhatsApp voice screening is
capped at 4–6 questions total, never more than 2 claims:

- 4Q = 1 claim, 4 questions
- 5Q = 2 claims, 2 questions each + 1 transfer question
- 6Q = 2 claims, 2 questions each + 1 transfer question + 1 gap-closer

This document synthesizes all fifteen prior audits
(`COVERAGE_REACHABILITY_AUDIT.md` through `CLAIM_TYPE_ROI_VALIDATION_AUDIT.md`)
as a single system against that constraint. Methodology only — no schemas,
APIs, prompts, or migrations below.

**One scale correction before anything else, because it changes how radical
this redesign actually is:** the current 39-candidate real corpus already
averages **5.44 questions/candidate** (212 questions / 39 candidates,
`COVERAGE_REACHABILITY_AUDIT.md` §0) and **2.12 questions/claim** (212/100,
same source). The new constraint is not asking for a system an order of
magnitude smaller than what's running today — it is asking for today's
*actual typical scale*, formalized into a fixed, small, auditable script
instead of an open-ended ladder that happens to land near this size. That
reframing matters for every answer below: this is not "shrink a large
system," it is "stop building a large system's machinery for a scale that
was already small."

---

## 1. Minimum viable evidence engine for a 4–6 question interview

Eight responsibilities, no more:

1. **Claim recall** — extract the real, complete, evidence-blind claim
   inventory (`EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md` Stage 1). Must not drop
   claims to a fixed per-type cap before selection runs
   (`CLAIM_EXTRACTION_AUDIT.md` Q3/Q4: the highest-ROI type, `system_ownership`,
   has two-thirds of its raw supply discarded by exactly this mechanism
   today). Must close the one narrow, cheap, already-identified defect first:
   the heuristic fallback promoting resume headers/contact lines/objective
   sentences to claims (`CLAIM_EXTRACTION_AUDIT.md` Q1/Q6) — a live-model
   problem this is not; a fallback-path problem it entirely is.
2. **Claim selection for exactly 2 slots** — see §5. Not by claim-type
   category.
3. **A declared evidence-gap taxonomy per selected claim** — see §2.
4. **One question generator**, used identically for every question in the
   script (opener, follow-up, transfer, gap-closer), applying the two
   wording principles validated identically across every move examined in
   `QUESTION_QUALITY_AUDIT.md`: name something specific and real from the
   claim, and ask explicitly for the thing that's hard to fake.
5. **A gap-first turn selector** — see §7 — that replaces "next rung of a
   fixed ladder" with "which still-open gap does the last answer make
   cheapest to close."
6. **Evidence extraction with declared-target crediting** — a dimension is
   credited only against what the question declared it was targeting at
   ask-time, never inferred afterward from an incidental nonzero score
   (deletes the `score > 0` backdoor and probe-level-keyed persistence,
   `COVERAGE_REACHABILITY_AUDIT.md` §5, `THREAD_MECHANISM_AUDIT.md` §6).
7. **Scoring over composite clusters, not six independent numbers** — see §6.
8. **Flat output assembly** — see §8. No graph object; the data volume at
   this scale (≤2 claims, ≤6 answers per candidate) makes a graph structure
   even less justified than at the current scale, where it was already found
   decorative (`EVIDENCE_GRAPH_AUDIT.md` — see the flagged disagreement in §10).

What is explicitly **not** part of the minimum viable engine, because the
audits measured it actively harmful or inert at any scale, and doubly so at
this one: archetype as a hard eligibility gate, ladder-depth scheduling
("ask a second scheduled move on the same claim" — proven the single worst
planner action available, `PLANNER_STRATEGY_AUDIT.md` §2), the 17-word
thread keyword list, `COHERENCE` and `METRIC_DEFINITION` as cold scheduled
moves, `claim_strength_bonus`, and seniority-gating of the transfer question
(forced out by the fixed-slot design — see §7).

---

## 2. Mandatory evidence categories

`EVIDENCE_GAP_FRAMEWORK.md`'s corrected minimal set is eight, not six — its
own addendum found the original six insufficient (`PROCESS_SEQUENCE` was
empirically confirmed missing at +3.62 lift, more frequent than two of the
"robust" six; `ADAPTABILITY`/transfer reasoning was structurally absent from
all six by construction). Ranked here by what a 4–6 question budget can
actually afford to chase, using the framework's own lift measurements:

**Tier 1 — proven lift (n≥25, "robust"), proven collectible today:**
`OPERATING_CONTEXT_DETAIL` (+4.10 lift), `CAUSAL_CHAIN`+`FAILURE_ANALYSIS`
(+2.97). These map to the two signal types (`process_steps`, `causal_links`)
that `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md` confirms actually populate in
real extractions (24/32 and 19/32 respectively) — every other category is
either directional-only or currently dead on extraction (next tier).

**Tier 2 — proven lift, currently broken on the extraction side:**
`CONSTRAINT` (+3.39 lift on the raw-text presence measure) and
`OWNERSHIP_BOUNDARY` (directional, +3.71). Both are must-ask targets under
the master context's own commitments (judgment, ownership), but
`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md` §2 found the *structured* signal
buckets these map to (`constraints`, `boundaries`) at **0/32 real usage** —
including on answers with textbook-clear content for exactly this category.
**This is a distinct problem from "ask for it more."** Asking a better
`AUTHORITY` or `OWNERSHIP_BOUNDARY` question, per
`EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md`'s own recommendation, does not fix this
by itself — the extraction layer is currently routing this content into
`process_steps` regardless of what was asked (`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`
§5, "the single most reproducible failure mode in the whole sample"). A 4–6Q
engine that spends one of its scarce questions on a constraint or ownership
target and still loses the content to misrouted extraction has wasted 17–25%
of its entire budget. **Fixing extraction for these two buckets is a
precondition for treating them as mandatory in practice, not an optional
follow-on.**

**Tier 3 — mandatory by product commitment, not by measured value:**
`ADAPTABILITY`/transfer reasoning. This is the one gap type that cannot be
discovered from an existing answer, only manufactured
(`PLANNER_STRATEGY_AUDIT.md` §1, `EVIDENCE_GAP_FRAMEWORK.md`'s addendum) —
which is exactly why the 5Q/6Q templates fix a dedicated transfer-question
slot rather than leaving it to compete for a ladder position, where it
currently loses to seniority gating for 46% of the corpus
(`DIMENSION_OPENING_AUDIT.md` §2).

**Tier 4 — named tension, not resolved here:** `OUTCOME`+`STAKEHOLDER_INTERACTION`.
This is `EVIDENT_MASTER_CONTEXT.md`'s own definition of verifiability — "what
actually resulted, and for whom" — and it is simultaneously the single
weakest-lift gap measured (+1.94, lowest of any category with a usable
sample) and the only gap with **no collection mechanism anywhere in the
system today, formal or accidental** (`EVIDENCE_GAP_FRAMEWORK.md` §5/§6).
At 4–6 questions there may not be budget to dedicate a slot to a
low-measured-lift target the product nonetheless considers foundational.
Named here as a real conflict between measured value and product
commitment, not silently resolved either direction.

**Not mandatory:** `TRADEOFF`/`DECISION_RATIONALE` as a *discovered* target —
`CLAIM_EXTRACTION_AUDIT.md` Q7 found **0.0% of 143 raw claims contain any
decision-framing language at all**, so no amount of better questioning
*discovers* this; it would have to be manufactured the same deliberate way
`ADAPTABILITY` is, which is a separate product decision this document does
not make. `METRIC_DEFINITION` as a standalone scheduled target — proven the
single worst-performing move on every real-interview axis when scheduled
cold (`MOVE_EVIDENCE_YIELD_AUDIT.md` §1), while the identical information
target triggered as a same-turn follow-up is among the corpus's best
(`THREAD_MECHANISM_AUDIT.md` §1/§3) — so it survives only inside the
gap-triggered follow-up mechanism (§7), never as its own budgeted slot.

---

## 3. Which existing concepts survive unchanged

Filtered from `EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md` Section 2 for what also
survives the *later* empirical findings (Dimension Validity, Extraction
Fidelity, Scoring Semantics, this session's Claim Type ROI audit) and the
4–6Q/2-claim constraint specifically:

1. **The model never scores; Python decides.** Untouched by budget size.
2. **Verbatim quote enforcement.** If anything more load-bearing at this
   scale — with 4–6 total answers instead of 20+, a single fabricated or
   miscredited signal is a much larger fraction of the candidate's entire
   evidence record.
3. **Declared move/target → dimension mapping, at ask-time.** Doubly
   necessary at small N: there is no room for the `score > 0` backdoor's
   noise to average out the way it partially does over a longer interview.
4. **Hard Python-side prohibitions on presentation-adjacent and
   quantity-fishing questions.** Unaffected by scale.
5. **The two winning wording patterns from `QUESTION_QUALITY_AUDIT.md`** —
   name something specific and real; ask for the hard-to-fake half. These
   were found identically across every move examined, so they are a
   property of question generation in general, not of any one scheduled
   move — and at 4–6 total questions, every single one must count; there is
   no budget to absorb a dead, generically-worded turn the way a
   20-question interview can.
6. **Thread's *principle*** (stay on the exact topic just, voluntarily,
   raised; ask for the one hard-to-fake detail implied but not yet stated) —
   generalized, not the 17-word implementation — as the *sole* depth
   mechanism, replacing ladder-depth entirely (§7).

What does **not** survive unchanged, despite being listed as "preserved" in
`EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md` before later audits ran: six
independently-scored dimensions (§6), seniority gating of transfer/decision-
boundary content in its current form (§7), and claim-type-based
prioritization (§5).

---

## 4. Which concepts should be removed entirely

- **The `score > 0` dimension-crediting backdoor** — inflates reported
  KNOWLEDGE coverage by up to 72.8 points over structural reality
  (`COVERAGE_REACHABILITY_AUDIT.md` §5).
- **Probe-level-keyed evidence persistence** — a `manager`-entity follow-up
  asking about decision authority gets credited to EXECUTION/KNOWLEDGE
  because its parent happened to carry an `OPERATIONAL` probe level
  (`THREAD_MECHANISM_AUDIT.md` §6).
- **Archetype as a hard eligibility gate.** 79% of claims can never offer
  `OWNERSHIP_BOUNDARY`/`PEOPLE` purely from a text-regex classification
  decided before any question is planned (`DIMENSION_OPENING_AUDIT.md` §4).
  At a 2-claim cap this is worse, not better: if both selected claims
  happen to classify `BUILD`/`PROCESS`/`METRIC_MOVE` (independently ~79%
  likely each, so roughly 3-in-5 for both), OWNERSHIP has **zero** chance
  the entire interview, with no third claim to fall back on the way today's
  multi-claim interviews partially self-heal (`DIMENSION_OPENING_AUDIT.md`
  §3's point about EXECUTION surviving via repetition across claims — a
  property that degrades sharply as claim count drops from ~2.56 to exactly
  2, and vanishes at exactly 1 for the 4Q shape).
- **The 17-word thread keyword vocabulary and its hand-written questions.**
  8 of 17 words never fired once in 212 real questions
  (`THREAD_MECHANISM_AUDIT.md` §1) — the mechanism's *behavior* is worth
  keeping, its specific implementation is not.
- **Ladder-depth scheduling** ("ask a second, different scheduled move on a
  claim already in progress"). Measured as the single **worst**-performing
  planner action available — 2.39 avg signals, 53.8% dead-turn rate, worse
  than abandoning the claim outright (`PLANNER_STRATEGY_AUDIT.md` §2). At
  2 questions per claim there is no room for this to ever be attempted; it
  must be structurally impossible in the new design, not merely
  deprioritized.
- **`COHERENCE` as a scheduled move.** Its precondition (two independently-
  established, cross-answer facts sharing a referent) never once cleared in
  212 real questions (`DIMENSION_OPENING_AUDIT.md` §1) even under the
  current, longer interview. It has categorically no chance of firing in a
  2-question-per-claim budget.
- **`METRIC_DEFINITION` as a cold scheduled move.** Worst performer on
  every real-interview axis (`MOVE_EVIDENCE_YIELD_AUDIT.md` §1); survives
  only as a possible gap-triggered follow-up target.
- **`claim_strength_bonus` and `default_claim_weights` as ranking
  mechanisms.** Correlation with actual evidence yield measured at
  −0.042 to −0.085 — statistically indistinguishable from zero, in places
  inverted (`CLAIM_PRIORITIZATION_AUDIT.md` §4).
- **The Evidence Graph as a graph.** See the flagged disagreement in §10 —
  no traversal capability exists or is used; every current output is
  reproducible from flat rows. At ≤2 claims and ≤6 answers per candidate,
  a graph object has even less to justify it than it already lacked at the
  current scale.
- **The legacy figure-leaking fallback template and the second, unmeasured
  question-generation architecture.** One generator, one measured path
  (§1.4).
- **Reported ("as-if-genuinely-probed") coverage as a concept.** Replaced
  by structural-only coverage (§8) — and, per §6, replaced further by a
  3-cluster report rather than a 6-dimension one.

---

## 5. Is claim prioritization still needed under a 2-claim maximum?

**Yes — needed *more*, not less, but not on the axis the current system or
even `CLAIM_PRIORITIZATION_AUDIT.md`'s own recommendation uses.** This is
the first place two audits in this corpus point in different directions
under direct pressure from the new constraint, and it needs to be named
rather than smoothed over.

**The disagreement.** `CLAIM_PRIORITIZATION_AUDIT.md` recommends re-weighting
claim *types* by measured ROI — `system_ownership` (3.67 signals/question)
over `delivery` (2.38) over `process_work` (1.25) — using real interview
outcomes from the current system. `CLAIM_TYPE_ROI_VALIDATION_AUDIT.md`,
run specifically at the 2-question-per-claim budget that the new 5Q/6Q
templates use exactly, found claim *type* explains only **9.6%** of yield
variance once the move sequence is held constant — because at 2 questions,
every archetype's ladder opens with the identical two universal moves
(`OPERATING_CONTEXT`, `FAILURE`), so category stops mattering to what
actually gets asked. The two audits are not measuring the same thing:
`CLAIM_PRIORITIZATION_AUDIT.md`'s type-level ROI numbers are confounded with
*how much ladder depth and move variety that type happened to receive* in
the current, variable-length interviews (a `system_ownership` claim is more
likely, by archetype, to eventually reach `AUTHORITY` or `OWNERSHIP_BOUNDARY`
— the system's best-yielding moves — if the interview runs long enough to
get there). `CLAIM_TYPE_ROI_VALIDATION_AUDIT.md` isolates that confound by
fixing the move sequence and finds the category signal nearly disappears.

**Which finding survives, at this specific budget:** the ROI audit's,
because it was run at the exact question-per-claim count (2) the 5Q/6Q
product templates actually use, via live simulation with the real question
generator and real scoring code, rather than inferred from outcomes at a
different, variable, generally-larger budget. **Claim-type category should
not be the selection axis in V2.**

**What should replace it, and why prioritization matters more here:** with
only 2 slots out of a real raw inventory averaging 3.67 claims per candidate
(`CLAIM_EXTRACTION_AUDIT.md` Q1), a wrong pick costs half the entire
interview, with no third or fourth claim to dilute the mistake — unlike
today's ~2.56-claim average interviews, where a weak claim is one of
several and its cost is partially absorbed. Three replacement signals, none
of them a category label:

1. **Complete, evidence-blind recall first** (§1.1) — you cannot select well
   from a pool that already lost real claims to a per-type cap or fallback
   junk.
2. **Archetype/gap-diversity across the exactly-2 slots**, specifically to
   hedge dimension reachability rather than to chase expected yield — e.g.,
   deliberately avoid selecting two claims that both foreclose OWNERSHIP,
   since there is no third claim to compensate the way there sometimes is
   today.
3. **Individual-claim phrasing signals**, not category weights — this
   session's ROI audit found first-person, responsibility/ownership-framed
   language outperforms achievement-shaped language under this exact budget
   (§9, the second flagged disagreement) — a *within-claim* property, not a
   between-type one.

---

## 6. Are six dimensions still justified?

**No — and this is the sharpest, most consequential disagreement in the
corpus.** `EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md` Section 2 lists "six fixed
competence dimensions... never challenged by any audit" as something to
preserve unchanged. `DIMENSION_VALIDITY_AUDIT.md`, run later, using data
(`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`, `SCORING_SEMANTICS_AUDIT.md`) that
did not exist when the V2 Design audit made that claim, tested it directly
at three independent grains — 39 candidates' final scores, 32 individual
re-extracted answers, and a causal ablation removing `causal_links` — and
all three agree: the six dimensions collapse to **three** statistical
clusters (Knowledge+Execution, r=0.85–0.97; Problem Solving+Judgment+
Adaptability, r=0.78–0.95; Ownership alone). The ablation is not a
correlation, it is a proof: with `causal_links` zeroed out, Judgment and
Adaptability's scores **stop varying entirely** — two of six "universal
competence dimensions" become mathematically constant. **Judgment and
Adaptability, as currently implemented, have no existence independent of
one shared signal type.**

**Which finding survives:** Dimension Validity's, for three reasons — it is
temporally later and built on evidence the earlier claim didn't have access
to; it is a direct empirical test at three independent grains rather than an
assertion of absence-of-challenge; and the causal ablation is proof of
mechanism, not just correlation.

**Why this gets worse, not better, at 4–6 questions.** Fewer answers means
less opportunity for any dimension to accumulate its own distinguishing
signal, and the two signal types actually driving the score
(`process_steps`, `causal_links`) are exactly the ones any answer to almost
any question naturally produces, regardless of intent. Reporting six
independently-labeled scores from 4–6 answers is a stronger, more visibly
implausible claim than reporting six from 15–20 — a recruiter can plausibly
doubt "6/6 competencies validly assessed in 4 questions" on its face, even
before knowing the underlying math forces it.

**What to do about it:** keep the master context's six as a *conceptual
and job-fit vocabulary* — the product still communicates in Knowledge/
Execution/Problem-Solving/Judgment/Ownership/Adaptability terms — but the
V2 *engine* at this budget should compute and report at most **three**
composite reads: an Execution/Knowledge composite, a Reasoning composite
(Problem Solving/Judgment/Adaptability, with the mandatory transfer question
feeding it rather than Adaptability standing alone), and Ownership kept
separate (the one dimension shown statistically distinct — not because it
is well-measured; `SCORING_SEMANTICS_AUDIT.md` already found its practical
gate reduces to "does the sentence contain the word I," a different,
weaker kind of noise — but because it measures something the other five
demonstrably don't). This is `DIMENSION_VALIDITY_AUDIT.md`'s own
recommended "Option C," adopted here as the only option consistent with
what a 4–6 question budget can actually support.

---

## 7. What should the planner optimize for at each question?

Mapped directly onto the fixed templates, using
`PLANNER_STRATEGY_AUDIT.md`'s central finding (evidence-gap-first beats
move-first on every measured axis) and `EVIDENCE_GAP_FRAMEWORK.md`'s lift
ranking (§2):

- **Opener (claim A's Q1, and claim B's Q1 in the 5Q/6Q shapes):**
  unconstrained, evidence-blind — the one place a scheduled, move-first
  question remains correct by necessity, because nothing exists yet to
  react to (`PLANNER_STRATEGY_AUDIT.md` §1). Should be `OPERATING_CONTEXT`-
  shaped: name the claim's own subject, ask what concrete artifact or
  signal the candidate worked from.
- **Follow-up (claim A's Q2, claim B's Q2):** never a second ladder rung.
  Selected by which evidence gap the opener's answer just made cheapest to
  close — thread's principle, generalized to run on every turn rather than
  a 17-word coincidence gated to fire once. This single fork is the
  difference between the corpus's best planner action (4.10 avg signals,
  20% dead-turn) and its worst (2.39 avg signals, 53.8% dead-turn) —
  `PLANNER_STRATEGY_AUDIT.md` §2. At 2 questions per claim, this is not an
  optimization, it is the entire value the second question can deliver.
- **Transfer question (5Q/6Q, one slot, cross-claim capable):** the one
  place a manufactured, not-discovered question is correct by design — no
  answer already given can substitute for it (`PLANNER_STRATEGY_AUDIT.md`
  §1, `EVIDENCE_GAP_FRAMEWORK.md`'s addendum). Given exactly 2 claims exist
  in this format, this is also the first place in the whole system where a
  genuine cross-claim comparison has a small, concrete, achievable use —
  unlike the abandoned, over-scoped `CROSS_CLAIM_LINK` feature
  (`EVIDENCE_GRAPH_AUDIT.md`), which died at graph scale but fits naturally
  at exactly-2-claims scale: perturb one claim's mechanism and ask the
  candidate to reason about it, optionally in light of the other claim.
- **Gap-closer (6Q only, one slot):** optimize for whichever mandatory gap
  (§2) has zero closure across **both** claims combined so far — coverage
  as a live input to the last question, not a side effect computed only at
  the end (`EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md` Section 6.2). This is
  trivial to check at this scale: at most 5 prior answers, at most 8 gap
  categories.
- **At every turn:** prefer a gap with proven (not merely directional) lift
  — `OPERATING_CONTEXT_DETAIL`, `CAUSAL_CHAIN`, `CONSTRAINT` — over an
  unproven one, and never repeat a move already asked on the same claim in
  a different guise.

**A forced consequence of the fixed-slot design, not a general
recommendation:** seniority gating of the transfer question must be
deleted outright, not merely "reconsidered" as `EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md`
Section 4.2 frames it for the general case. A 5Q/6Q template has one
transfer slot, always present. Silently skipping it for junior/unknown-
seniority candidates — 46% of the current corpus, `DIMENSION_OPENING_AUDIT.md`
§2 — would make the 5Q and 6Q *templates themselves* different interviews
for different candidates, a starker fairness problem than today's variable-
length ladder ever produced. The same argument applies to gating `AUTHORITY`-
type content out of the follow-up slot: it is independently the single
highest-yielding move in the entire system (`MOVE_EVIDENCE_YIELD_AUDIT.md`
§4), and `THREAD_MECHANISM_AUDIT.md` §6 already shows equivalent content
(`manager`/`approval` follow-ups) reaching junior candidates today with no
gate and no observed harm. Gating it out of a 2-question-per-claim budget
would remove the best available action from the candidates who can least
afford to lose a question to a mediocre one.

---

## 8. What should the final candidate output contain?

- The (at most 2) interviewed claims, each with its verbatim Q&A transcript,
  which gap(s) each answer closed or left open, and which dimension(s) each
  question **declared** as its target at ask-time — never a target inferred
  afterward from an incidental score.
- Three composite scores (§6), each carrying its own coverage state
  (genuinely targeted / candidate declined / not reached within budget) —
  never a bare number that reads identically whether the underlying reality
  was "asked and scored zero" or "never asked" (`SCORING_SEMANTICS_AUDIT.md`
  §3's "Unknown vs. zero" finding, which the master context's own fairness
  commitment — "a coverage gap is Unknown, never Bad" — already requires
  and the current arithmetic cannot currently deliver).
- An explicit, named statement of which of the master context's six
  competencies could not be independently assessed in this interview length
  — e.g., "Ownership: not independently measurable in this format" — rather
  than a fabricated low or zero score for something structurally unreachable
  at 4–6 questions. This is the sharpest place a short-format product needs
  to operationalize "Unknown, never Bad," because the temptation to report
  six numbers regardless of what was actually asked is strongest exactly
  where the format is shortest.
- No claim of "N of 6 dimensions covered." Already measured as
  substantially inflated at the current, longer scale (structural coverage
  reaches all six dimensions in only 2 of 39 real interviews,
  `COVERAGE_REACHABILITY_AUDIT.md` §5–6); at 4–6 questions the same claim
  would not merely be optimistic, it would be checkable-false on its face.
- A flat structure — claims, their gap-closures, their declared-dimension
  credits, the three composite scores — with no graph object
  (`EVIDENCE_GRAPH_AUDIT.md`: nothing is lost by skipping graph machinery
  even at the current, larger scale; it is even less justified at ≤2 claims
  and ≤6 answers).

---

## 9. Smallest set of measurable success metrics for V2

Five, each already validated as measurable by an existing audit's own
method, each targeting a different layer so no single number can be gamed
in isolation:

1. **Structural coverage of the three composite clusters** (§6), per
   candidate — genuinely-targeted only, never the `score > 0` backdoor.
   No a priori target number; track the distribution and watch it against
   the current structural baseline (median 3/6 dimensions,
   `COVERAGE_REACHABILITY_AUDIT.md` §7).
2. **Dead-turn rate per question slot** (opener / follow-up / transfer /
   gap-closer) — directly comparable to the existing benchmarks
   (`MOVE_EVIDENCE_YIELD_AUDIT.md`, `PLANNER_STRATEGY_AUDIT.md` §2): the
   follow-up slot should approach thread's ~20% dead-turn rate, not
   ladder-depth's ~54%.
3. **Gap-closure rate across the mandatory minimal set** (§2), per
   interview — directly computable from `EVIDENCE_GAP_FRAMEWORK.md`'s own
   taxonomy and regex method.
4. **Claim-selection yield correlation** — re-run
   `CLAIM_PRIORITIZATION_AUDIT.md` Section 4's test (selection score vs.
   actual signals/claim_score produced) on whatever replaces
   `claim_strength_bonus`, specifically at n=2-claim selection. Must clear
   a bar meaningfully above the current ~0/negative correlation — the top-
   ranked claim should not, on average, underperform the one that would
   have been picked last, as it currently does (`CLAIM_PRIORITIZATION_AUDIT.md`
   §4's inverted top-vs-bottom-decile finding).
5. **Extraction-bucket live rate for `decisions`/`constraints`/`boundaries`**
   specifically — currently 0/32 (`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`
   §2). V2 cannot be judged to have fixed Ownership- or Judgment-adjacent
   evidence collection until these move measurably off zero; per that
   audit's own conclusion, this may be the *primary* bottleneck for those
   two areas, ahead of anything the planner does.

---

## 10. Dependency-ordered methodology architecture

Each layer reads only what the layers above it produce.

**Layer 1 — Claim recall.** Complete, evidence-blind extraction. Fixes the
heuristic-fallback junk gap first (§1.1) — the cheapest, narrowest,
highest-leverage correction identified in the whole series
(`CLAIM_EXTRACTION_AUDIT.md`).

**Layer 2 — Claim selection (exactly 2 slots).** Archetype/gap-diversity
and individual-claim phrasing signals, not claim-type category weight (§5).

**Layer 3 — Evidence-gap taxonomy, declared per selected claim.** The
mandatory minimal set (§2), informed but never hard-gated by archetype.

**Layer 4 — Question generation.** One generator, one measured prompt
family, the two validated wording principles (§3.5), used identically for
opener, follow-up, transfer, and gap-closer. Depends only on Layer 3
handing it a target gap.

**Layer 5 — The gap-first turn selector.** Chooses, per the fixed template
position (§7), which gap Layer 4 should render next. Depends on Layer 3's
live gap state; does not need to know anything about Layer 6 or 7.

**Layer 6 — Evidence extraction with declared-target crediting.** Depends
on Layer 5 having declared, at ask-time, what each question targeted.
Also depends on fixing the extraction-bucket dead paths
(`decisions`/`constraints`/`boundaries`, and the schema-length-triggered
14.6% silent fallback rate, `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`) before
Layer 7 can be trusted.

**Layer 7 — Scoring.** Three composite clusters (§6), weight renormalized
over genuinely-targeted gaps only (fixing `total_weight`'s unconditional
six-way sum, `SCORING_SEMANTICS_AUDIT.md` §3), gates requiring a grounding
element beyond lexical "contains the word I" pattern matching
(`SCORING_SEMANTICS_AUDIT.md` §4).

**Layer 8 — Output assembly.** Flat structure (§8), no graph. Depends on
Layers 6–7 only; nothing below it.

**Flagged disagreement resolved at this layer, for the record:**
`EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md` Section 8/9 (written before the
dedicated graph audit) proposed keeping "evidence graph assembly" — role
weights applied, contradictions as traceable edges, fine-grained provenance
— as a first-class architectural stage. `EVIDENCE_GRAPH_AUDIT.md`, written
later and specifically to test that assumption, found **zero production
call sites requiring traversal**, every current recruiter-facing output
already reproducible from flat rows, and the one genuinely graph-shaped
feature (`CROSS_CLAIM_LINK`) dead on arrival (gated off, excluded from its
own priority order, dependent on a prompt file never loaded). The later,
directly-verified finding survives: Layer 8 is a flat assembly, not a graph,
and this is even more clearly correct at ≤2 claims / ≤6 answers than it was
at the current scale where the question was first settled.

---

## Summary of the three explicit corpus disagreements this synthesis resolved

1. **Six dimensions, keep as-is** (`EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md`) vs.
   **three empirically-forced clusters** (`DIMENSION_VALIDITY_AUDIT.md`) —
   the later, three-grain empirical test with a causal-ablation proof
   survives (§6).
2. **Achievement-shaped claims are the strongest, underrepresented evidence
   category** (`CLAIM_EXTRACTION_AUDIT.md` Q5's framing) vs. **achievement/
   outcome-shaped claims score lower than responsibility-framed claims under
   the actual production budget** (`CLAIM_TYPE_ROI_VALIDATION_AUDIT.md` §4)
   — the real-budget simulation survives, because it measures what the
   planner does with the claim, not just what the claim contains (§5).
3. **Claim-type ROI should drive prioritization**
   (`CLAIM_PRIORITIZATION_AUDIT.md`) vs. **claim type explains only 9.6% of
   yield variance at the actual 2-question-per-claim budget**
   (`CLAIM_TYPE_ROI_VALIDATION_AUDIT.md`) — the budget-matched simulation
   survives, because it isolates the confound between claim type and how
   much ladder depth that type happened to receive in the current,
   variable-length system (§5).
4. **Evidence graph assembly as a first-class V2 stage**
   (`EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md`) vs. **the graph is decorative,
   zero call sites require it** (`EVIDENCE_GRAPH_AUDIT.md`) — the later,
   directly-verified audit survives (§10).

In every case, the later, more directly empirical finding — not the earlier
or more architecturally ambitious one — is what this synthesis carries
forward.
