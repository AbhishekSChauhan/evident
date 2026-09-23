# Evidence Engine Remediation Plan

**What this is:** a sequenced plan for fixing what the fourteen audits in
`docs/` found, built directly on the phase structure and dependency
reasoning already provided — refined with exact baseline numbers from the
audits themselves (so each gate has a real number to clear, not just a
direction), explicit product-call flags where a decision belongs to a human
rather than an engineer, and a concrete re-audit methodology per phase.
**No code, no pseudocode, no schema below** — every phase states what must
become true and how to verify it, not how to build it. That is deliberate:
this plan is the handoff artifact for implementation work, not the
implementation itself.

**The dependency logic, stated once:** every audit after
`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md` measured *something downstream of
extraction* — coverage, planner behavior, scoring, dimension correlation —
using data that extraction already corrupted. `SCORING_SEMANTICS_AUDIT.md`'s
ablation and `DIMENSION_VALIDITY_AUDIT.md`'s correlation collapse are not
independent findings; both are consequences of the same five dead signal
buckets `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md` found first. Fixing planner
logic, claim selection, or the dimension count before fixing what gets
measured means re-optimizing against numbers that are still wrong. This is
why Phase 1 comes first regardless of which subsystem *feels* most broken.

---

## Phase 1 — Fix Measurement Reality

**Goal:** the system measures what actually happened in an answer, and a
missing measurement is recorded as missing, not as zero.

**Audits:** `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`,
`SCORING_SEMANTICS_AUDIT.md`, `DIMENSION_VALIDITY_AUDIT.md`.

**Baseline, exact:**
- `decisions`, `constraints`, `boundaries`, `concept_explanations`, `facts`
  populated in **0 of 32** genuine live extractions — including at least
  six real answers with unambiguous content for one of these categories
  (Jyoti's `manager`/`report` threads, SK's `AUTHORITY` answer, Renuka's
  `AUTHORITY` answer, Tushar's `OWNERSHIP_BOUNDARY` answer, Ayush's `report`
  thread — all named with quotes in
  `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md` §2).
- A real ablation against production code found `process_steps` and
  `causal_links` are the **only** two signal types with measurable effect on
  `claim_score` (avg swings of 16.38 and 11.06 points across 32 real
  answers); the other ten are near-inert, and the same five listed above
  measured **exactly zero** effect — because they never populate.
- JUDGMENT's gate has exactly one live route in the real data:
  `causal_links` (`decisions`/`constraints` are dead, so the two other
  designed routes don't exist in practice). OWNERSHIP's gate reduces to
  "does the sentence contain the word I" for the same reason.
- Five of six competence dimensions correlate at r=0.78–0.97 across three
  independent measurement grains, and two of the highest-correlated pairs
  (Problem Solving↔Judgment, Judgment↔Adaptability) become **mathematically
  undefined** the instant `causal_links` is ablated — because those
  dimensions stop varying at all without it.
- `total_weight` in `claim_score()` sums all six declared dimension weights
  unconditionally (`scoring.py:135`); an unprobed dimension's weight is
  forfeited to zero, not excluded or redistributed. `score_claim()` marks a
  dimension `probed=True` whenever its score is simply nonzero
  (`signals.py:746`), independent of whether a targeting question was ever
  asked.

**Outcome required:**
1. `decisions`, `boundaries`, `constraints`, and `facts` extract as
   themselves on answers that state them — not as `process_steps` or
   `causal_links` wearing the wrong label. (`concept_explanations` is
   included in this outcome too, even though the user's list above didn't
   name it separately — it measured zero in the same audit for the same
   reason and belongs in the same fix.)
2. "Unknown" becomes a distinct value the arithmetic can carry, not a zero
   that looks identical to a proven weakness. This has to resolve the named
   conflict from `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md` C1 — see the
   product-call flag below.
3. The `score > 0` backdoor in `score_claim()` stops being sufficient on its
   own to mark a dimension "probed" — probing has to mean a targeting
   question was actually asked.

**Product call, flagged not resolved:** whether "unprobed" becomes a
tri-state (probed-and-scored / probed-and-zero / never-probed) that
propagates as something other than `0` through `claim_score`, or whether the
product keeps "unprobed = 0" as an intentional confidence discount and only
fixes the *reporting* layer to show it clearly — both were named as live
options in `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`'s roadmap and
`SCORING_SEMANTICS_AUDIT.md`'s conclusion. This plan does not pick one.
Whoever implements Phase 1 needs that decision made explicitly first,
because it changes what "fixed" means for outcome #2 above.

**Re-audit gate — re-run, don't eyeball:**
- `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`'s exact stratified-sample
  methodology (48 real answers across yield bands), checking specifically
  whether the six named real answers above now populate their correct
  bucket. Bucket-usage counts for `decisions`/`boundaries`/`constraints`
  must move off zero.
- `SCORING_SEMANTICS_AUDIT.md`'s exact ablation. The five dead buckets must
  show nonzero average point-swing when removed.
- `DIMENSION_VALIDITY_AUDIT.md`'s exact three-grain correlation methodology.
  Do not expect r=0 between everything — some conceptual overlap between,
  say, Knowledge and Problem Solving is defensible. The gate is narrower:
  Problem Solving↔Judgment and Judgment↔Adaptability must **no longer
  become undefined when `causal_links` is removed**, because `decisions`
  and `constraints` now carry real, independent variance for those
  dimensions.

**Do not proceed to Phase 2 until all three re-audits are re-run and show
movement on the specific numbers above** — not "improved," a re-measured
number.

---

## Phase 2 — Fix Coverage Reachability

**Goal:** every dimension has a path to being genuinely asked about that
isn't blocked by a fact having nothing to do with the candidate's actual
competence.

**Audits:** `COVERAGE_REACHABILITY_AUDIT.md`, `DIMENSION_OPENING_AUDIT.md`.

**Baseline, exact:**
- OWNERSHIP is the worst-covered dimension (51.3% reported / 20.5%
  structural), because its two openers (`OWNERSHIP_BOUNDARY`, `PEOPLE`)
  only exist in the `OWNERSHIP`/`VOLUME` archetypes — **21% of claims,
  combined** — and archetype is decided by a text regex on the claim at
  extraction time, before any question is planned.
- JUDGMENT and ADAPTABILITY are jointly gated by seniority: `AUTHORITY`
  needs mid/senior (blocked on 37.5% of its in-ladder claims), `EXCLUSION`
  needs senior (blocked on 73.4% — the single most-blocked move in the
  system), `PERTURB` needs senior (blocked on 47%). `seniority=None` blocks
  all three simultaneously rather than defaulting open.
- `COHERENCE` fired **0 of 212** real questions. `PEOPLE` fired on only
  **9.5%** of its 21 eligible, fully-unblocked opportunities — the least-used
  move in the whole system, blocked by nothing structural.
- `OPERATING_CONTEXT` — documented as guaranteed on every claim — actually
  opens only **46%** of real claims; the gap is planner choice, not a gate.
- The coverage metric itself lies: the `score > 0` backdoor (Phase 1's
  finding, restated here at its consequence) inflates KNOWLEDGE's reported
  coverage over its structural (genuinely-targeted) coverage by **72.8
  percentage points**, and JUDGMENT/OWNERSHIP by 30.8 points each.

**Outcome required (as specified):** every dimension needs at least one
reachable path that does not depend on seniority, and at least one
reachable path that does not depend on archetype. Concretely, per the
baseline above: OWNERSHIP needs an opener outside the
`OWNERSHIP`/`VOLUME`-archetype restriction; JUDGMENT and ADAPTABILITY each
need an opener that doesn't require mid/senior status. "Coverage" must mean
"the candidate was explicitly asked," full stop — not "the score happened
to end up above zero."

**Note on ownership of this fix:** the coverage-metric-lies problem's root
mechanism (the `score > 0` backdoor) lives in the same `signals.py` code
Phase 1 already has to change. This phase's gate on that specific point is
a *re-verification that Phase 1's fix actually propagates into the coverage
numbers* — once the backdoor is gone, reported and structural coverage
should become the same number by construction, which is a cheap thing to
confirm and a strong signal if it doesn't hold.

**Re-audit gate:**
- `COVERAGE_REACHABILITY_AUDIT.md`'s exact methodology. Structural coverage
  for OWNERSHIP, JUDGMENT, and ADAPTABILITY must rise measurably above the
  20.5% / 38.5% / 79.5%-with-inflation baselines, and the "all six
  dimensions genuinely reached" candidate count must rise above the
  baseline **2 of 39**.
- `DIMENSION_OPENING_AUDIT.md`'s exact methodology. `COHERENCE` and
  `PEOPLE` selection rates must move off their near-zero baselines (0/212
  and 9.5% of eligible respectively). Reported-vs-structural coverage gap
  should collapse toward zero for every dimension, per the note above.

---

## Phase 3 — Replace the Move-First Planner

**Goal:** the planner decides what to ask next by what evidence is missing,
not by which rung of a fixed ladder comes next.

**Audits:** `PLANNER_STRATEGY_AUDIT.md`, `THREAD_MECHANISM_AUDIT.md`,
`QUESTION_QUALITY_AUDIT.md`, `MOVE_EVIDENCE_YIELD_AUDIT.md`. (The user's
phase list also names `EVIDENCE_GAP_FRAMEWORK.md` as involved here but
doesn't include it in the re-audit list below — noted, not silently
corrected; see the recommended addition at the end of this phase's gate.)

**Baseline, exact:**
- Real turn-by-turn trace of all 39 interviews: asking a second, different
  scheduled move on a claim already in progress is the **worst-performing
  planner action available** — 2.39 avg signals, 53.8% dead-turn rate —
  worse than abandoning the claim (2.79) or a contingent `thread` follow-up
  (4.10, the best of the three).
- The continue-vs-abandon decision is **uncorrelated with the evidence the
  last answer just produced**: the planner abandons a genuinely hot trail
  (≥5 signals) in 28.6% of switches, and persists on a dead trail (0
  signals) in 42.7% of continuations.
- `AUTHORITY`, `OWNERSHIP_BOUNDARY`, `DEPENDENCY` are the highest-yield
  moves in the corpus and also the rarest/most gated; `OPERATING_CONTEXT`
  and `FAILURE` are guaranteed on every claim and only mediocre.
- Two wording patterns work identically across every move examined (name a
  concrete entity from the claim; ask explicitly for the hard-to-fake
  thing) — this means question *wording* is not the bottleneck once the
  planner asks the right thing; `METRIC_DEFINITION`'s best-worded real
  instance still failed because the underlying claim had nothing to give
  it, which is a planning/claim problem, not a wording one.
- `thread` — an unrelated, hard-coded, seniority-blind, 17-word keyword
  lookup given planner-priority-1 as a hackathon shortcut — is the
  second-highest-yield mechanism in the entire corpus, and its credited
  dimension is often wrong because it inherits `probe_level` from its
  parent question rather than deriving one from its own content
  (`THREAD_MECHANISM_AUDIT.md` §6).

**Outcome required:** the planner's central operation becomes "what gap,
if closed right now, converts the most already-latent information into
evidence" — generalizing `thread`'s actual working principle (stay on
topic, ask for the specific missing hard-to-fake detail, zero
context-switch cost) into an always-on mechanism, rather than a 17-word
coincidence that fires once per claim. "Ask a second scheduled move on the
same claim by fixed ladder position" stops being a planner action, per the
measured result above. Full design contract for this is already written in
`EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md` §5 — this phase implements that
section specifically, not a new design.

**Product call, flagged not resolved:** `EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md`
§4.2 challenges the safety premise behind seniority-gating
`AUTHORITY`/`EXCLUSION`/`PERTURB` at all, using `thread`'s seniority-blind
equivalent (which asks nearly the same content and reads as appropriate in
every real transcript examined) as counter-evidence. Whether the redesigned
planner keeps, loosens, or removes seniority gating is a fairness/product
decision, not something this plan or an engineer should decide unilaterally
— it needs the same explicit sign-off `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`
asked for on C1/C2.

**Re-audit gate:**
- `PLANNER_STRATEGY_AUDIT.md`'s exact turn-by-turn trace. The
  correlation between continue-vs-switch and evidence-just-produced must
  flip from ~uncorrelated to a real positive relationship. Same-claim
  continuation yield (via whatever replaces `thread`) must match or beat
  the 4.10 baseline `thread` already set — not regress to the old ladder's
  2.39.
- `THREAD_MECHANISM_AUDIT.md`'s findings, re-checked conceptually: the new
  mechanism should preserve `thread`'s real advantages (recency, concrete
  entity, no forced context switch) while fixing its dimension-crediting
  mismatch.
- `QUESTION_QUALITY_AUDIT.md` and `MOVE_EVIDENCE_YIELD_AUDIT.md`, re-run to
  confirm `AUTHORITY`/`OWNERSHIP_BOUNDARY`/`DEPENDENCY`-shaped evidence is
  now reached more often — their scarcity was a scheduling problem, and
  this phase is exactly what should fix scheduling.
- **Recommended addition, not in the user's original list:** spot-check
  `EVIDENCE_GAP_FRAMEWORK.md`'s gap-closure regex taxonomy against fresh
  data, since that audit is named as involved here. Not made a hard gate
  because the user's own re-audit list didn't include it — flagged so it
  isn't silently dropped either.

---

## Phase 4 — Fix Claim Selection

**Goal:** claim priority predicts evidence yield instead of resume-writing
register.

**Audits:** `CLAIM_PRIORITIZATION_AUDIT.md`,
`METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md` (conflict C2).

**Baseline, exact:** re-running the real `claim_strength_bonus()` and
`default_claim_weights()` functions against all 100 real interviewed claims
found correlation with actual yield **indistinguishable from zero, and
negative on two measures**: −0.042 against total signals, −0.085 against
claim_score. The top decile of claims by priority score averaged a
claim_score of **17.90**; the bottom decile averaged **36.40** — inverted.
Both components of the formula (the taxonomy-declared type weight and the
resume-prose regex bonus) are independently uncorrelated, not just diluted
by each other. `system_ownership`-type claims measured 3x the ROI of
`process_work`-type claims, and neither the current formula nor the current
selection mechanism notices.

**Outcome required (as specified):** claim priority predicts evidence
yield, claim score, and signal density — not resume vocabulary.
`CLAIM_PRIORITIZATION_AUDIT.md` §7 already specifies this precisely: stop
using any unverified resume-prose scan as a ranking signal; re-weight claim
types by measured ROI rather than a hand-set constant; treat selection as
portfolio allocation across a budget, not a one-time top-3 cut decided
before any evidence exists.

**Re-audit gate:** re-run `CLAIM_PRIORITIZATION_AUDIT.md`'s exact
correlation methodology on fresh claims. The new priority score's
correlation with actual yield must be positive and material — the specific
bar to clear is not a number this plan invents, but the qualitative result
must reverse: the top-decile/bottom-decile comparison must no longer
invert, and ideally should show the top decile outperforming the bottom by
a clear margin. Separately, confirm the low-ROI types identified in the
audit (`process_work`, `tooling`, `measurable_outcome` — 15.6% of the
measured question budget) are no longer competing for early interview
slots against `system_ownership`/reporting/ownership-shaped claims.

---

## Phase 5 — Decide the Competence Model

**Goal:** determine, on real post-fix data, whether six independent
dimensions are supportable — and this is explicitly a product decision, not
an engineering one, exactly as specified.

**Audits:** `DIMENSION_VALIDITY_AUDIT.md` (re-run), informed by
`EVIDENCE_GAP_FRAMEWORK.md`'s dimension-to-gap mapping.

**Baseline, exact (pre-fix, for reference — this phase runs on post-Phase-1
data, not this number):** Knowledge↔Execution r=0.973 (candidates) / 0.853
(answers); Problem Solving↔Judgment r=0.949/0.945; Problem
Solving↔Adaptability 0.874/0.778; Judgment↔Adaptability 0.841/0.840; only
Ownership was statistically distinct from the rest (r=0.05–0.68 depending
on grain). `DIMENSION_VALIDITY_AUDIT.md`'s own recommendation, on this
pre-fix data, was Option C (composite scores + evidence categories), not a
clean six or a collapse to three.

**Outcome required:** this phase does not happen until Phase 1's re-audit
gate has already re-run `DIMENSION_VALIDITY_AUDIT.md` once (Phase 1's own
gate requires this). Phase 5 is the point where whoever owns the product
decision looks at that *post-fix* correlation structure and picks:

- **Option A** — six dimensions, if the correlations genuinely dropped and
  Problem Solving/Judgment/Adaptability no longer collapse to a constant
  without `causal_links`.
- **Option B** — fewer dimensions (e.g., the two clusters found), if the
  correlations persist even after `decisions`/`constraints`/`concept_explanations`
  are genuinely populating.
- **Option C** — `DIMENSION_VALIDITY_AUDIT.md`'s own recommendation:
  composite cluster scores alongside the evidence categories from
  `EVIDENCE_GAP_FRAMEWORK.md`, which doesn't require the six-way
  independence claim to hold at all.

**This plan does not make this choice.** It only asserts the choice should
be made with fresh data, after Phase 1, not on the pre-fix numbers above.

**Re-audit gate:** `DIMENSION_VALIDITY_AUDIT.md`'s exact three-grain
methodology, re-run on data collected after Phases 1–4 are live. This is
the same re-run Phase 1 already requires — Phase 5 is where its result gets
acted on rather than just checked.

---

## Phase 6 — Evidence Graph V2

**Goal:** build actual graph relationships — only after the evidence
flowing into them is trustworthy.

**Audit:** `EVIDENCE_GRAPH_AUDIT.md`.

**Baseline, exact:** the current "Evidence Graph" is a strict three-level
tree (Candidate → Claim → QA-turn/DimensionScore) with foreign-key-only
edges, no traversal API, and zero inferred relationships. The one attempted
cross-node feature (`CROSS_CLAIM_LINK`) is dead three ways — gated off by
default, excluded even when the gate is on, and dependent on a prompt file
that's never loaded anywhere. The highest-traffic recruiter output (the
ranked candidate list) already bypasses the graph entirely, reading a flat
cache table instead.

**Why this phase is last, exactly as reasoned:** every relationship this
phase would build — `Claim ↔ Claim`, `Evidence ↔ Evidence`, `Evidence ↔
Requirement`, `Candidate ↔ Candidate`, contradiction edges, support edges,
similarity edges — is a relationship *between pieces of evidence*. Building
that structure on top of evidence that Phase 1 hasn't yet fixed (five dead
signal buckets, non-deterministic extraction, unknown/zero conflation)
means encoding relationships between things that are frequently wrong or
missing. `EVIDENCE_GRAPH_AUDIT.md`'s own finding reinforces this from a
different angle: the *only* future capability it identified as genuinely
requiring real graph structure (rather than a well-indexed relational
table) is exactly this class of cross-claim/cross-candidate relationship —
which means this phase is not "build a graph because the architecture
diagram says so," it's "build the one thing that was correctly identified
as actually needing graph semantics, now that there's trustworthy evidence
to put in it."

**Outcome required:** not specified further here — this is genuinely a V2
design task, not a fix, and belongs in its own design pass once Phases 1–5
are live, the same way `EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md` was a design
pass rather than a fix-audit.

**Re-audit gate:** none yet — there is nothing to re-audit until this phase
has a design to measure against. When it does, it should be checked the
same way every other phase was: real data, a re-run of
`EVIDENCE_GRAPH_AUDIT.md`'s methodology, and a specific number showing the
new relationships are used by production consumers rather than decorative.

---

## Recommended order, as a checklist

| # | Step | Phase | Blocked on |
|---|---|---|---|
| 1 | Extraction fidelity | 1 | — |
| 2 | Scoring semantics | 1 | 1 (same phase, same re-audit) |
| 3 | Dimension validity (first re-run, diagnostic only) | 1 | 1–2 |
| 4 | Coverage reachability | 2 | Phase 1 gate cleared |
| 5 | Dimension opening | 2 | Phase 1 gate cleared |
| 6 | Planner strategy replacement | 3 | Phase 2 gate cleared |
| 7 | Thread generalization / evidence-gap planner | 3 | same as 6 |
| 8 | Claim prioritization | 4 | Phase 3 gate cleared (a gap-first planner and a fixed claim-selection mechanism are independent, but measuring #8's fix cleanly is easier once #6–7 aren't also moving) |
| 9 | Competence model decision | 5 | Phases 1–4 gates cleared; product decision, not an engineering one |
| 10 | Evidence Graph V2 | 6 | Phases 1–5 |

**Everything after step 3 depends on trustworthy evidence. Everything after
step 9 depends on trustworthy dimensions. Everything after step 10 depends
on trustworthy relationships.** Each phase's re-audit gate above is the
literal test for whether that dependency has actually been discharged —
not a checkbox, a re-run of the same methodology the original audit used,
against the same or fresher real data.
