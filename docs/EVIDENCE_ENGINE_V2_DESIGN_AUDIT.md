# Evidence Engine V2 Design Audit

**Question:** if Evident's planning and evidence-collection engine were
designed today, from scratch, using everything the eight prior audits found,
what should the methodology be? This is a redesign of the *methodology*, not
a code proposal — no algorithms, schemas, or implementation steps below,
only what each stage must do, why, and what evidence justifies the call.
Deployment, auth, ATS, the recruiter dashboard, infrastructure, scaling,
Postgres, and vector search are all out of scope by instruction; this is the
evidence engine only.

**Sources, all already-verified findings, cited by short name below:**
`METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md` (METHOD), `COVERAGE_REACHABILITY_AUDIT.md`
(COVERAGE), `DIMENSION_OPENING_AUDIT.md` (OPENING), `MOVE_EVIDENCE_YIELD_AUDIT.md`
(YIELD), `QUESTION_QUALITY_AUDIT.md` (QUALITY), `THREAD_MECHANISM_AUDIT.md`
(THREAD), `PLANNER_STRATEGY_AUDIT.md` (STRATEGY), `EVIDENCE_GAP_FRAMEWORK.md`
(GAPS), `EVIDENT_MASTER_CONTEXT.md` (MASTER).

---

## Section 1 — Current architecture map

For orientation only; every claim here is established in the audits above,
not re-derived.

```
Resume
  → extract.py: claim extraction AND prioritization fused in one pass
      (claim_type keyword weight + claim_strength_bonus, a resume-prose
      regex scan) → top 3 claims kept, ~12-17 discarded (METHOD C2, GAPS)
  → anatomy.py: archetype classified from claim text at extraction time
      (BUILD / PROCESS / OWNERSHIP / VOLUME / METRIC_MOVE) — this alone
      decides which of the ten moves' ladders even contain
      OWNERSHIP_BOUNDARY/PEOPLE/AUTHORITY/EXCLUSION/METRIC_DEFINITION,
      before a single question is asked (OPENING, COVERAGE §4)
  → orchestrator.plan_next_forensic: breadth-first-then-depth scheduling
      over a fixed ARCHETYPE_LADDER per claim, gated by LEVEL_RESTRICTED
      seniority checks (STRATEGY, OPENING §0-2)
  → orchestrator._thread_plan: a 17-word keyword lookup against the
      candidate's last answer, given planning priority ABOVE the forensic
      system, gated behind demo_mode (THREAD §1)
  → question.py generator: renders a Move-specific prompt, validates with
      seven Python rules, retargets to a new Move on rejection, falls back
      to an anatomy-built template if both attempts fail (METHOD Stage 4)
  → evidence.py / signals.py: extracts AnswerSignals, persists per-response
      Evidence rows keyed by probe_level (not move or content) (OPENING §5,
      THREAD §6), and separately recomputes claim-level dimension scores
      from the raw signal history, crediting a dimension "probed" either
      from a targeting move OR from any nonzero score at all (OPENING §5b)
  → scoring.py: claim_score → weighted_evidence_score → competence_score,
      with role dimension weights fetched and never applied (METHOD S1)
  → graph.py: assembles the candidate-level dimension profile and ranking
```

Two things about this map matter more than any single box in it: **claim
fate and dimension reachability are decided in the first two boxes, before
any interview evidence exists** (METHOD, OPENING, COVERAGE), and **the one
part of the running system that behaves like it's reacting to what the
candidate just said sits outside this pipeline entirely**, bolted on ahead
of it as a demo shortcut (THREAD).

---

## Section 2 — What should be preserved

Preserved because the audits measured it working, not because it's already
built.

1. **Six fixed competence dimensions, defined domain-independently.**
   MASTER's own framing (Knowledge/Execution/Problem Solving/Judgment/
   Ownership/Adaptability) is never challenged by any audit — every finding
   is about *reaching* these six reliably, not about whether they're the
   right six. Keep as-is.
2. **The model never scores; Python decides.** Every audit that touches
   scoring treats this as the correct architecture (METHOD explicitly
   credits it as "Strong" wherever it's actually enforced). The problems
   found are all about *which* Python logic decides, not about moving
   judgment back into the model.
3. **Verbatim quote enforcement.** `enforce_verbatim()`-style checking
   ("these words were said") is real, cheap, and — per METHOD — does exactly
   what it claims to do. It is not sufficient on its own (see Section 4), but
   nothing in any audit argues for removing it.
4. **An explicit, auditable move/target → dimension mapping.** The fact that
   `MOVE_DIMENSIONS`-style bookkeeping exists at all is what made every one
   of these eight audits possible — without a declared mapping from "what was
   asked" to "what it's supposed to prove," none of the gaps found here would
   have been visible or fixable. Keep the *principle* of an explicit mapping;
   Section 6 modifies how it's populated.
5. **Python-enforced hard prohibitions on presentation-adjacent questions**
   (no direct "how many/how much/how long" asks). METHOD rates this
   correctly as defense-in-depth for the "never score presentation"
   commitment (MASTER). Keep.
6. **The two winning question-wording patterns identified in QUALITY**: name
   a specific, concrete entity from the claim, and ask explicitly for the
   thing that's hard to fake (a cause, both halves of a decision boundary, a
   comparison). These are not move-specific tricks — QUALITY found them
   identically across every move examined — so they should be a property of
   *all* question generation in V2, not of individual prompt templates.
7. **`DEPENDENCY` and `AUTHORITY` as scheduled moves, in principle.** Both
   are, on the evidence, genuinely strong: highest causal density and
   highest overall yield respectively (YIELD §1), with no meaningful
   low-yield wording cluster (QUALITY). The problem with both is scarcity,
   not design — see Section 4.
8. **A required grounding step before a fabrication-resistant probe's
   content is trusted** — this doesn't exist today as a *requirement*
   (TRANSFER/PERTURB is optional, per METHOD EC1), but the *idea* that some
   mechanism must verify a claim beyond lexical pattern matching is the
   single most important preserved *intent* in the whole system, even though
   its current execution is what Section 4 replaces.

---

## Section 3 — What should be deleted entirely

1. **The `score > 0` backdoor in dimension crediting** (`entry.probed =
   dimension in probed or entry.score > 0`). Measured to inflate reported
   coverage by up to 72.8 percentage points for KNOWLEDGE alone, and by
   30.8 points each for JUDGMENT and OWNERSHIP (COVERAGE §5). This is not a
   tuning problem — it makes the single most recruiter-visible number in the
   system (coverage/probed dimensions) mean something other than what it
   claims to mean. Delete; a dimension is "opened" only through a genuine
   targeting mechanism (Section 6 defines what that must be in V2).
2. **Persisting per-response evidence keyed by `probe_level` alone.**
   Demonstrated to produce visibly wrong dimension attribution — a `manager`
   follow-up asking about decision authority (JUDGMENT/OWNERSHIP content)
   gets persisted-credited toward EXECUTION/KNOWLEDGE because its parent
   question happened to carry an `OPERATIONAL` probe level (THREAD §6). This
   coarse, many-to-one key should not exist in V2 at all; every persisted
   evidence record must carry what it actually targeted.
3. **Archetype as a hard eligibility gate on which moves' ladders even
   contain a dimension's opener.** 79% of claims can never offer
   `OWNERSHIP_BOUNDARY`/`PEOPLE` because a text regex classified them as
   `BUILD`/`PROCESS`/`METRIC_MOVE` at extraction time — a decision made from
   the candidate's *wording*, not their actual role scope (OPENING §4,
   COVERAGE §4). This is architecturally the same failure mode as claim
   selection's resume-vocabulary sensitivity (METHOD C2) at a different
   layer. Delete archetype as a hard gate; it may survive as descriptive
   metadata that *informs* question generation, but it must not
   categorically remove a dimension from reach.
4. **The `demo_mode` framing around the thread mechanism, and its position
   "ahead of everything the forensic planner does."** The mechanism's
   *behavior* is the best-performing thing in the corpus (Section 4 keeps
   the principle) — but its status as an unrelated, hard-coded, priority-one
   bolt-on gated behind a demo flag has no place in a from-scratch design.
5. **The fixed 17-word keyword vocabulary and its one hand-written question
   per word.** 8 of 17 never fired once in 212 real questions (THREAD §1);
   the mechanism works despite this vocabulary, not because it is well
   chosen. Delete the specific word list and its static questions; Section 5
   replaces the *principle* with something that doesn't depend on a curated
   noun list.
6. **The legacy probe-level-based fallback templates that render `On
   "<claim>" — <base>` and leak the claim's own figures into the fallback
   question by construction** (METHOD Stage 4, weakness list #6). The
   anatomy-based forensic fallback (which deliberately excludes figures) is
   the correct design and should be the *only* fallback path in V2.
7. **The unmeasured, currently-dormant second question-generation
   architecture and prompt variant** (the retired probe-level generator, and
   the `v2` prompt gated off by default). METHOD's Top-10 lists this as an
   architecture weakness in its own right: two systems exist, only the
   retired one has ever been measured. A from-scratch design has one
   generator, measured.
8. **`COHERENCE` and `METRIC_DEFINITION` as independently-scheduled, cold
   moves competing for ladder position.** Not because their information
   targets are wrong — METRIC_DEFINITION asks exactly the right thing per
   its own brief (QUALITY), and COHERENCE's fact-reconciliation goal is
   sound — but because scheduling them cold, on a fixed ladder position, is
   empirically the wrong delivery mechanism: `COHERENCE` never fires at all
   (0/100, OPENING §1) and `METRIC_DEFINITION` is the worst performer in the
   corpus on every real axis (0.33 avg signals, 66.7% dead-turn rate, YIELD
   §1) while its own fallback template — and thread's near-identical
   `metric` follow-up — both work fine (YIELD §2, THREAD §1/§3). The
   information targets survive into Section 5 as gap types, not as
   scheduled moves.

---

## Section 4 — What should be redesigned

These are mechanisms whose *goal* is right and whose *current form* is not —
neither pure keeps nor pure deletions.

1. **Claim extraction and prioritization must become two stages, not one.**
   Recall (what's genuinely on the resume) must be evidence-blind and
   complete; ranking (what's worth interviewing first) must not run on an
   unverified keyword scan of the candidate's own prose (`claim_strength_bonus`
   rewards incident/causal/leadership vocabulary with no check against
   anything, METHOD C2 — precisely the register an AI resume-writer
   optimizes for, per MASTER's own diagnosis of the problem it exists to
   solve). This was already the team's own stated intended architecture
   (cited from `CLAIM_INVENTORY.md` inside METHOD) and never shipped.
2. **Seniority gating on `AUTHORITY`/`EXCLUSION`/`PERTURB` needs to be
   reconsidered, not just tuned.** The current design assumes decision-
   authority and hypothetical-reasoning questions require seniority context
   to be appropriate — but THREAD directly falsifies the premise that this
   content is unsafe to ask without it: the `manager`/`approval` follow-ups
   ask nearly identical content to `AUTHORITY`, carry no seniority check at
   all, and nothing in the 30 real transcripts examined reads as
   inappropriate for the candidate it was asked of (THREAD §1, §6). Combined
   with `seniority=None` blocking all three gated moves simultaneously
   rather than defaulting to anything permissive (OPENING §2, COVERAGE §7),
   the current gate trades a large, measured coverage cost (46% of the
   corpus structurally denied ADAPTABILITY and materially reduced JUDGMENT
   access, COVERAGE §7) for a safety property the data don't show is actually
   at risk. This is exactly the kind of assumption the brief asked to be
   challenged: redesign the gate around the *content* of what's being asked
   (is this question itself presentation-adjacent or bias-risking, per
   MASTER's own "never score presentation" line?) rather than around a
   demographic-adjacent proxy field that empirically removes a whole
   dimension for half the candidate pool.
3. **The archetype-ladder scheduling logic itself.** STRATEGY's turn-by-turn
   trace found that "ask a second, different scheduled move on the same
   claim" is the single **worst**-performing planner action available —
   worse than abandoning the claim outright (2.39 avg signals vs. 2.79 for
   switching vs. 4.10 for a contingent follow-up, STRATEGY §2). A fixed
   ladder that assumes depth-via-next-move is the natural continuation of a
   claim is measurably wrong; Section 5 replaces the scheduling principle.
4. **Gate-opening evidence needs a grounding requirement, not lexical
   pattern presence.** `gate_open` for OWNERSHIP/PROBLEM_SOLVING/JUDGMENT
   today is satisfiable by generic first-person verb matching with zero
   check that the underlying event happened or connects to the specific
   claim (METHOD EC1 — "the review's top finding"). METHOD's own proposed
   direction — require gate-opening evidence to also include something
   specific and unique to *this* claim, or require survival of a transfer/
   perturbation-style probe as an input to the gate rather than an
   independent, budget-competing dimension — is adopted here as a
   requirement for V2's dimension-opening methodology (Section 6).
5. **Memory-exhaustion handling.** Currently indistinguishable from "never
   asked" (METHOD EC2) and a documented zero-cost evasion. V2's evidence-gap
   tracking (Section 5) must record "candidate declined" as a distinct state
   from "not yet probed," because a gap-first planner needs to know the
   difference to decide whether to try a different angle or move on.
6. **The thread mechanism's targeting.** Keep the *behavior* (immediate,
   same-topic, ask-for-the-hard-to-fake-detail, zero context-switch cost —
   THREAD's Final Answer), replace the *delivery*: detection of what's worth
   following up on should be driven by the evidence-gap taxonomy (Section 5,
   from GAPS) rather than a fixed noun list, and its dimension crediting must
   come from what the follow-up actually asked for (Section 6), not from
   whatever probe level its parent happened to carry.
7. **Question generation's validator rule set.** Keep Python-side
   enforcement as the mechanism (Section 2), but four of the seven current
   rules have never had their precision established against independent
   human judgment (`duplicate_content`, `no_claim_anchor`,
   `multiple_fact_targets`, `scope_drift` — METHOD Q5), and the largest
   measured recall gap (`unsupported_premise`) has a validated
   *non*-solution rather than a fix (METHOD Q4). V2 needs the discriminative-
   power check METHOD's Q2 identifies as entirely missing (a question
   answerable purely from the resume, ~10.6% of the measured corpus) and a
   dedicated elicitor for causal/generalizable reasoning, which GAPS'
   addendum confirms has no reliable current source.
8. **Coverage reporting.** Must be rebuilt on the structural (genuinely
   targeted) definition only — the reported-vs-structural gap is not a
   rounding error, it changes "all 6 dimensions reached" from 14/39
   candidates to 2/39 (COVERAGE §5-6). Whatever V2 reports as coverage must
   be the number that would not change if the incidental-scoring backdoor
   (Section 3) is removed, because by construction it will be the *only*
   number once that backdoor is gone.

---

## Section 5 — Evidence-gap-first planner design

This is the central redesign, and STRATEGY's finding is the mandate for it:
every quantitative result across all eight audits shows evidence yield
tracks *what the candidate just revealed and what is still missing*, not
*which move is scheduled next*. Two of the clearest individual proofs:
`METRIC_DEFINITION` scheduled cold is the worst performer in the system;
the same information target, triggered by a gap the candidate's own words
just exposed (thread's `metric` entity), is among the best (STRATEGY, final
determination). A move-first planner cannot distinguish those two
situations because it isn't looking at the answer to decide what to do
next — it's looking at a ladder position.

**What the planner must track, per claim, continuously:** which of the
minimal evidence gaps (GAPS §7 + addendum — operating context, a causal
chain, decision rationale, a constraint/boundary, ownership, outcome, and
transfer/adaptability reasoning) are still open, and which the candidate's
own last answer just made newly reachable by naming something concrete. This
replaces "which move is next in the ladder" as the planning question with
"which gap, if closed right now, converts the most already-latent
information into evidence."

**What this means concretely, without prescribing implementation:**

- **Opening a claim** still needs an unconstrained first question — there is
  nothing to react to yet (STRATEGY §1's `OPERATING_CONTEXT` row: "not
  applicable to itself"). This is the one place a move-first opener remains
  correct by necessity.
- **Every turn after the first** should be chosen by asking: did the last
  answer just name something (an artifact, a person, a number, a decision,
  an unfinished cause) that closes a gap more cheaply than opening new
  ground would? THREAD's mechanism already proves this works when it fires;
  the redesign is to make that check run on *every* turn, not on a 17-word
  coincidence gated to fire once per claim.
- **"Going deeper via a second scheduled move" should not be a planner
  option in its current form at all.** STRATEGY measured it as the worst
  available action (2.39 avg signals, 53.8% dead-turn rate — worse than
  abandoning the claim). If a claim has more to give after its opener, the
  next question should come from what the opener's *answer* pointed to, not
  from the next rung of a pre-committed ladder.
- **Abandoning a claim must be evidence-aware, not schedule-aware.**
  STRATEGY found the current switch-or-continue decision is uncorrelated
  with the evidence just produced — the planner abandons a hot trail nearly
  3 times in 10 and persists on a dead one more than 4 times in 10. A
  gap-first planner switches claims specifically when the current claim's
  gaps are exhausted or its answers have gone cold, not on a fixed budget
  countdown.
- **`PERTURB`/transfer reasoning is the one gap type that cannot be
  discovered, only manufactured** (STRATEGY §1, GAPS addendum). A gap-first
  planner still needs a deliberate policy for introducing this need — it is
  the one place "ask about something not yet raised" is correct by design,
  not a lapse into move-first thinking.
- **Claim selection itself should be part of the same gap-first logic**,
  not a one-time pre-interview cut. Given real candidates carry 12-17
  verifiable claims and only 3 are interviewed today (METHOD, citing
  `CLAIM_INVENTORY.md`), and given that per-claim depth is often the worst
  use of a question (above), a gap-first design should treat "which claim
  gets the next question" and "which follow-up on the current claim" as the
  same decision, made on the same basis: which action closes the most
  valuable open gap, across the whole candidate, not just the current claim.

---

## Section 6 — Dimension coverage design

Redesigned around three principles, each directly answering a documented
failure:

**1. A dimension is "opened" only by a genuine targeting act, and that act
is recorded at the moment it happens — never inferred afterward from an
incidental score.** This removes the `score > 0` backdoor (Section 3) and
the probe-level-keyed persistence mismatch (Section 3) in one move: whatever
closes a gap (Section 5) must declare, at ask-time, which dimension(s) it is
attempting to open, and evidence is credited toward exactly and only that
declared target. Coverage numbers computed this way cannot inflate the way
COVERAGE §5 measured (up to 72.8 points for KNOWLEDGE), because there is no
longer a path from "unrelated incidental language" to "dimension marked
open."

**2. Coverage is a planning objective, not a side effect.** Today, coverage
emerges from archetype classification and seniority gates decided before
any question is planned, plus whatever the breadth-first ladder happens to
reach (OPENING, COVERAGE). A gap-first planner (Section 5) makes "which
dimensions have zero genuine attempts so far" a direct input to what gets
asked next, the same way it treats any other open gap — this is what would
have prevented the measured outcome where a candidate's JUDGMENT dimension
received zero probes across a full six-question budget while
`OPERATING_CONTEXT`/`FAILURE` absorbed most of the interview regardless of
whether they were still producing evidence (METHOD C1, citing the Priya
trace; STRATEGY §2's finding that continuation is uncorrelated with
productivity).

**3. Single-opener dimensions are named as a structural risk, not silently
carried forward.** EXECUTION's one path is unrestricted and self-heals at
the candidate level (multiple claims, multiple chances — OPENING §3).
ADAPTABILITY's one path is senior-gated with no fallback, which OPENING
calls "the starkest single point of failure in the six-dimension framework"
— any junior or unknown-seniority candidate has *zero* chance of it, no
matter how the interview goes. V2's dimension-opening methodology needs
either a second, non-gated way to elicit transfer reasoning, or an explicit
product acknowledgment that ADAPTABILITY is conditionally unreachable for
part of the candidate pool — reported as such, not silently absorbed into an
"Unknown" that reads the same as every other kind of gap. This is a MASTER-
level fairness question (candidate fairness: "a coverage gap is Unknown,
never Bad") and should be named rather than resolved by default, the same
way METHOD's C1/C2 were named rather than silently decided.

**4. Coverage reporting must show the structural number only**, with
"declined to answer" (Section 4.5) tracked and surfaced as its own state —
distinct from both "genuinely probed, scored zero" and "never reached" —
because MASTER's explainability commitment requires every number to trace to
something the candidate said or didn't, and today those three situations are
not distinguishable at all (METHOD EC2).

---

## Section 7 — Question generation design

Two design principles carry over unchanged from QUALITY's cross-move
finding, because they were true identically across every move examined, not
specific to any one of them:

1. **Name something specific and real from the candidate's own claim** —
   never a pronoun, never "this work." Every high-yield question in the
   corpus, regardless of move, did this; every wording-caused low-yield
   cluster either failed to do it or had nothing concrete to substitute
   (QUALITY, cross-move comparison).
2. **Ask explicitly for the thing that's hard to fake** — the discovered
   cause, both halves of a decision boundary, the specific comparison behind
   a choice, a concrete already-anchored activity. A question that asks only
   "what happened" or only "what could you decide" reliably underperforms
   the version that also asks for the harder half.

What changes structurally:

- **One generator, one measured prompt family.** The current coexistence of
  a retired probe-level generator, a live default forensic prompt, and an
  unmeasured `v2` variant (METHOD Q6, Top-10 #10) has no place in a
  from-scratch design. V2 needs exactly one generation path, continuously
  measured against real interviews — not against a retired corpus, which is
  METHOD's most repeated methodological complaint (Q4, Q5, Top-10 #5).
- **Validator rules stay Python-enforced, but only where precision is
  established.** `answer_leakage` is the one rule with real measured
  precision (79.2% against human judgment, per METHOD's citations); the
  other six need the same bar before being trusted as-is, and
  `unsupported_premise` — the largest measured recall gap — has a
  demonstrated non-solution (κ=0.477 on its own definition), not a rule to
  port forward wholesale. V2 should carry forward the *validated* fraction
  of the current rule set and treat the rest as open research, not shipped
  logic.
- **A discriminative-power check is a new, required rule.** METHOD measured
  ~10.6% of a real corpus as answerable equally well by someone who only
  read the resume — this consumes scarce budget with zero yield difference
  from an impersonator's perspective and has no current check against it.
- **A dedicated causal/generalizable-reasoning elicitor is a new
  requirement.** Both METHOD (Q3: "CAUSAL_REASONING has no reliable
  elicitor") and GAPS' addendum (the unconfirmed but repeatedly-observed
  "concept explanation" pattern) point at the same hole: nothing in the
  current design reliably asks for the *general mechanism* behind a specific
  event, only the event itself.
- **Fallback generation is anatomy-grounded only**, never leaking a claim's
  own figures (Section 3 deletes the legacy path that does). The fallback
  path is not a lesser concern to be tolerated — METHOD's qpol_2 finding that
  "the fallback is no worse than generated questions, mildly better" means
  the fallback's design quality is a first-class part of question-generation
  methodology, not an afterthought for outages.
- **Thread-style follow-ups use the same generation discipline as scheduled
  questions** — the same two principles above, generated against the
  evidence-gap taxonomy (Section 5) rather than a fixed word-to-question
  lookup, so that a follow-up's wording quality is held to the same
  validated bar a scheduled question is, rather than being a hand-written
  string chosen once at authoring time.

---

## Section 8 — Evidence graph implications

The graph's job, per MASTER, is claim → evidence → competence → job fit,
with evidence as the necessary, non-optional intermediate node. Three
implications follow directly from what the audits found is currently
missing or wrong:

1. **The graph's evidence nodes must carry provenance fine enough that these
   eight audits wouldn't have needed to be run by hand.** Reconstructing
   "which move opened which dimension," "was this credited genuinely or
   incidentally," and "did this follow-up's content match its persisted
   credit" all required re-deriving ground truth from code and re-running
   scoring functions against raw exports (OPENING, THREAD, STRATEGY methods
   sections). An evidence node should record, at the moment it's created,
   what gap it was targeting, what mechanism produced it (a scheduled
   question or a gap-triggered follow-up), and whether it was a genuine
   target or an incidental one — not leave that reconstructable only after
   the fact from a probe-level side channel.
2. **Role dimension weights must actually reach the score they claim to
   affect.** `dimension_weights_for(job_family)` is fetched and silently
   discarded before it reaches `weighted_evidence_score()` (METHOD S1) — a
   configuration surface that has zero effect on any candidate's ranking is
   worse than no surface at all, because it actively misleads whoever
   configures it. This is squarely evidence-graph population: the weights
   are supposed to determine how claim-level evidence rolls up into the
   competence node, and today they don't.
3. **Contradictions need to be first-class graph edges, not orphaned
   strings.** A detected inconsistency currently stores two raw text values
   with no link back to the facts or claims that produced them (METHOD
   Top-10 #9) — it cannot be traced back into the graph a recruiter would
   otherwise be able to click through, which is a direct explainability
   failure under MASTER's own definition of what the graph is for.

Two items are explicitly *not* elaborated here because they cross into
excluded territory (recruiter-facing consumption, dashboard rendering): the
`job_fit.py` crash on unprobed-dimension requirements (METHOD S2) is a
consumption-contract bug against whatever the graph now returns, not a
change to evidence-engine methodology, and is noted only so it isn't
silently forgotten by whoever picks this up next.

---

## Section 9 — Proposed V2 architecture

Stated as stage responsibilities and contracts, not implementation:

**Stage 1 — Claim recall.** Extract every verifiable claim from the resume,
complete and evidence-blind. No ranking, no cutoff, no keyword-scored
prioritization at this stage — this stage's only job is not to lose real
claims (Section 4.1).

**Stage 2 — Claim salience, separated from claim eligibility.** Rank claims
for interview scheduling using signals that don't reward resume-writing
register on their own (Section 4.1, METHOD C2's named conflict) — claim type
and structural properties, not an unverified vocabulary scan. This stage
feeds Stage 5 a prioritized pool, not a frozen slate of exactly three; how
many claims actually get interviewed becomes an outcome of the evidence-gap
planner's budget use (Stage 5), not a number fixed before the interview
starts.

**Stage 3 — Evidence-gap taxonomy, declared per claim.** For each claim in
the pool, identify which of the minimal gap types (Section 5's seven: context,
causal chain, decision rationale, constraint/boundary, ownership, outcome,
and — separately, because it's manufactured not discovered — transfer
reasoning) are plausibly open, without yet committing to a fixed question
sequence. Archetype-style claim shape may still exist as descriptive
metadata that informs *wording*, but must not hard-gate which gaps are even
eligible to be asked about (Section 3.3).

**Stage 4 — Question generation, one path.** A single, continuously-measured
generator produces the actual question for whichever gap Stage 5 selects,
applying the two validated wording principles (Section 7) regardless of
whether the target was a scheduled opener or a same-turn follow-up. Falls
back only to the anatomy-grounded template (Section 3.6), never to a
figure-leaking legacy path.

**Stage 5 — The gap-first planner.** Selects, every turn: open a new claim's
first gap if no claim is in progress; otherwise, check whether the last
answer just made a gap cheaper to close than switching would (thread's
principle, generalized — Section 4.6, Section 5); otherwise, close the
highest-value still-open gap on the highest-priority claim remaining, with
explicit weight given to dimensions that have had zero genuine attempts so
far (Section 6.2) over further depth on dimensions already opened. "Ask a
second scheduled move on the same claim by ladder position" is not a
planner action in V2 (Section 4.3, Section 5).

**Stage 6 — Evidence extraction and dimension crediting.** Extracts
structured signals per answer as today (verbatim enforcement preserved,
Section 2.3), but credits a dimension only against the gap the question
declared it was targeting (Section 6.1) — no incidental-score backdoor, no
probe-level-keyed persistence. Gate-opening evidence for OWNERSHIP/
PROBLEM_SOLVING/JUDGMENT requires a grounding element beyond lexical pattern
match (Section 4.4).

**Stage 7 — Coverage tracking.** Maintained continuously as an input to
Stage 5, not computed only at the end. Reports the structural number only,
with declined-to-answer tracked as a distinct state (Section 6.4), and
names single-opener/gated-dimension risk explicitly per candidate rather
than folding it into an undifferentiated "Unknown" (Section 6.3).

**Stage 8 — Evidence graph assembly.** Populates claim → evidence →
competence with fine-grained provenance on every evidence node (Section 8.1),
applies role dimension weights for real (Section 8.2), and stores
contradictions as edges with traceable origins (Section 8.3).

---

## Section 10 — Migration plan from current engine to V2

Ordered by dependency, not calendar time; each step is checkable against an
audit finding before moving to the next.

1. **Stop the backdoor before building anything new.** Removing the
   `score > 0` incidental-crediting path (Section 3.1) and the probe-level-
   keyed persistence (Section 3.2) can happen against the *current* move
   ladder, with no planner change yet — it only requires that every
   scheduled move and thread follow-up already declares its target, which
   the current `MOVE_DIMENSIONS` table already does for scheduled moves.
   This alone makes every coverage number reported from that point on
   trustworthy, and gives a clean, non-inflated baseline to measure every
   subsequent change against.
2. **Decouple archetype from hard eligibility.** Stop letting claim
   archetype exclude a dimension's opener outright (Section 3.3); let it
   inform wording only. This can be verified against COVERAGE §4's 79%
   figure directly — it should drop to near zero once archetype is no
   longer a gate.
3. **Generalize thread's principle before deleting its implementation.**
   Build the gap-triggered follow-up as a first-class mechanism (Section
   4.6) that runs on every turn, using the evidence-gap taxonomy instead of
   the 17-word list, *before* removing the old thread code — this lets the
   two be compared directly on the same real-interview basis THREAD already
   established as the yield benchmark to beat (4.10 avg signals).
4. **Replace ladder-depth scheduling with gap-first selection.** This is the
   highest-risk step because it's the actual planner rewrite (Section 5) —
   sequence it after steps 1-3 specifically so that its "before" baseline is
   already backdoor-free and archetype-unblocked, isolating what the
   scheduling change itself contributes rather than conflating it with the
   other two fixes.
5. **Revisit seniority gating as an explicit, named decision** (Section
   4.2), not a silent carry-forward — this is a fairness-tradeoff call in
   the same category METHOD flagged as `[product call]` for C1/C2, and
   should be resolved the same way: named, not defaulted.
6. **Consolidate question generation to one measured path** (Section 7),
   retire the unmeasured second architecture, and add the two new validator
   capabilities (discriminative-power check, causal/generalizable-reasoning
   elicitor) once the planner generating their targets is stable.
7. **Wire the evidence graph consequences last** — role dimension weights
   actually applied, contradictions as traceable edges, fine-grained
   provenance on evidence nodes (Section 8) — because these consume whatever
   Stage 5-7 now produce, and building them against a still-changing
   upstream would mean redoing the work.

At every step, the check for "did this help" is the same one these eight
audits already used: re-run the structural coverage measurement, the
move/gap yield measurement, and the switch-vs-continue trace from STRATEGY
§2, and confirm the numbers move in the direction the audit predicted before
proceeding to the next step. A redesign that can't be checked against the
same measurements that motivated it is not a redesign this project can
trust more than the one it's replacing.
