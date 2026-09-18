# Dimension Opening Audit

**Scope, strictly:** the mechanics of how a claim's interview turns into an
opened competence dimension — which moves can do it, how often each step of
that path actually fires, and where it breaks. Not scoring quality, not
question wording, not evidence-extraction fidelity. Those are covered
elsewhere (`docs/METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`,
`docs/COVERAGE_REACHABILITY_AUDIT.md`) and are explicitly excluded here.

**Dataset:** same 39 real (`llm_mode=live`) finalized evaluations, 100
interviewed claims, 212 questions, from `studies/evidence_export_prod/`, used
in the companion coverage audit — the only fully-real dataset available (see
that document's §0 for why this is 39, not the 57 originally asked for).

**Method:** ground truth for "which move opens which dimension" is read
directly from `MOVE_DIMENSIONS` (`api/engine/question.py:1151-1173`), which
`score_claim()` (`api/engine/signals.py:697-749`) uses to credit a dimension
from a move actually on record. Availability/selection/blocking counts are
computed per (claim, move) instance by re-running the live
`ARCHETYPE_LADDER`, `LEVEL_RESTRICTED`, `level_appropriate()`, and
`move_available()` against each claim's real archetype (`analyse()`,
`api/engine/anatomy.py`) and the moves its actual stored turns used. One
caveat stated once, up front: **archetype is recomputed from the claim's
stored text**, not read from a live session-time field, so a handful of
counts below could drift from what the running system actually saw if a
claim's classification depends on more than stored text (it does not appear
to, per `anatomy.py`, but this dataset spans real interviews over time and a
code-version mismatch cannot be fully ruled out).

---

## 0. Two mechanics that apply to every dimension before the per-dimension detail

These aren't specific to any one dimension, but they gate every path below,
so they're stated once here rather than repeated six times.

**(a) ~20% of the real interview budget carries no `Move` at all.**

| Question source | Count | % of 212 |
|---|---:|---:|
| `model` (forensic Move-ladder path) | 166 | 78.3% |
| `thread` — a hardcoded "answer-thread follow-up," explicitly commented in code as `"Hackathon demo: answer threading. No model call"` (`orchestrator.py:1298-1306`) | 30 | 14.2% |
| `repair` (non-answer recovery turn) | 12 | 5.7% |
| `regenerated` / `fallback` | 4 | 1.9% |

**170 of 212 questions (80.2%) carry a `Move` that can credit a dimension
through the intended mechanism at all.** The other 42 (19.8%) — `thread` and
`repair` turns — have no move, so `score_claim()` falls back to
`PROBE_LEVEL_DIMENSIONS`, a coarser probe-level-keyed table
(`signals.py:60-67`) that only maps `DECISION→JUDGMENT`,
`VALIDATION→KNOWLEDGE`, `OUTCOME→OWNERSHIP`, etc. — one dimension per
level, not the move-specific set. In practice this means roughly a fifth of
every candidate's fixed six-question budget is structurally weaker at
opening any specific dimension on purpose, before any archetype or seniority
gate is even reached.

**(b) The claim-aggregate `probed` flag is not a reliable "this path opened
the dimension" signal — it has a backdoor.**

`score_claim()`'s exact line: `entry.probed = dimension in probed or entry.score
> 0`. A dimension is marked open either because a mapped move was asked
(the real path) **or** because the score is simply nonzero for any reason —
including incidental language in a completely unrelated answer. Measured
directly (isolating candidates where *neither* of a dimension's opener moves
was ever asked, anywhere in their interview):

| Dimension | Candidates where neither opener move was ever asked | ...of which the dimension still scored > 0 |
|---|---:|---:|
| KNOWLEDGE | 36/39 | **26 (72%)** |
| JUDGMENT | 24/39 | 12 (50%) |
| OWNERSHIP | 31/39 | 11 (35%) |

This means most of what follows about "how often a move successfully opened
a dimension" has to be read carefully: a move being asked and the dimension
scoring nonzero often are **not** causally connected. Per-dimension sections
below report both the move-level mechanics and this attribution caveat where
it matters.

---

## 1. Per-move mechanics table (all nine moves, full corpus)

"Available" = the move is in the claim's archetype ladder, seniority allows
it, and its runtime precondition (`move_available()`) is met. "Selected" =
actually asked. "Opened" (rightmost column) = of the times it was
**selected**, how often that specific turn's `signals_found > 0` (the
one per-turn, move-agnostic yield signal in the export that isn't corrupted
by the probe-level/move mismatch described in §4).

| Move | Live dimension(s) it maps to | In-ladder opportunities | Available | Selected | Selected as % of available | Signal yield when selected |
|---|---|---:|---:|---:|---:|---:|
| `OPERATING_CONTEXT` | EXECUTION | 100/100 | 100 | 52 | 52.0% | 33/52 (63.5%) |
| `FAILURE` | PROBLEM_SOLVING | 100/100 | 100 | 43 | 43.0% | 22/43 (51.2%) |
| `PERTURB` | ADAPTABILITY | 100/100 | 53 | 31 | 58.5% | 16/31 (51.6%) |
| `AUTHORITY` | JUDGMENT | 56/100 | 35 | 14 | 40.0% | 10/14 (71.4%) |
| `EXCLUSION` | JUDGMENT | 79/100 | 21 | 6 | 28.6% | 4/6 (66.7%) |
| `DEPENDENCY` | PROBLEM_SOLVING | 44/100 | 44 | 11 | 25.0% | 7/11 (63.6%) |
| `OWNERSHIP_BOUNDARY` | OWNERSHIP | 11/100 | 11 | 6 | 54.5% | 5/6 (83.3%) |
| `PEOPLE` | OWNERSHIP | 21/100 | 21 | 2 | **9.5% (lowest of all nine)** | 1/2 (50%) |
| `METRIC_DEFINITION` | KNOWLEDGE | 7/100 | 7 | 3 | 42.9% | 1/3 (33.3%) |
| `COHERENCE` | KNOWLEDGE | 100/100 | *unmeasurable precisely (needs the live per-claim ledger; see below)* | **0** | **0.0%** | n/a |

`COHERENCE`'s precondition (`seam_pair(ledger) is not None`, requiring two
`MID`/`DEAR`-cost facts from *different* answers on the same claim sharing a
referent) can't be recomputed offline without the live signal ledger, so its
"available" count above is not claimed precisely. What is certain, directly
from the stored turns: **`COHERENCE` was asked zero times in all 212
questions across all 39 real interviews.** Whatever its true availability
rate is, its real-world selection rate is 0%.

---

## 2. Per-dimension: all paths, and where each one fails

### KNOWLEDGE — openers: `METRIC_DEFINITION`, `COHERENCE`

Both paths are close to non-functional in practice, for two different
reasons:
- `METRIC_DEFINITION` is archetype-gated to `Archetype.METRIC_MOVE` only —
  **7% of all claims** are even eligible, because a claim needs a
  pre-extracted metric to classify that way. Available 7, selected 3
  (42.9%), one produced a signal.
- `COHERENCE` requires a cross-answer seam that a 2-3-question-per-claim
  budget rarely accumulates enough material to produce. Selected **0/100**.

Failure mode: **archetype exclusion + an unmet runtime precondition**,
compounding — not budget, not seniority, not planner choice; there is
almost nothing to plan around. The dimension's 79.5% *reported* probe rate
(from the companion coverage audit) is real only 7.7% of the time
structurally; the rest is the `score > 0` backdoor (§0b: 72% of candidates
who got neither opener still scored KNOWLEDGE > 0).

### EXECUTION — opener: `OPERATING_CONTEXT` (only one path)

Unrestricted — no archetype gate (every archetype's ladder opens with it, no
exceptions) and no seniority gate. Available on all 100 claims. Yet
**selected on only 52** — despite being documented as the guaranteed first
move for every claim (`CLAUDE.md`'s "Execution-First Opening" note). The
actual first-turn move distribution across the 100 interviewed claims:

| Actual first move | Count |
|---|---:|
| `OPERATING_CONTEXT` | 46 |
| `PERTURB` | 21 |
| `FAILURE` | 20 |
| `AUTHORITY` | 6 |
| `DEPENDENCY` | 4 |
| `METRIC_DEFINITION` | 1 |
| `OWNERSHIP_BOUNDARY` | 1 |
| `EXCLUSION` | 1 |

Fewer than half of real claims actually open with `OPERATING_CONTEXT` in
this corpus. Failure mode here is **pure planner choice** — the move is
never blocked by archetype, seniority, or a precondition; something in the
live planner's actual move ordering (or the momentum/breadth/seam logic
overriding the nominal ladder start, or `thread`/`repair` turns consuming
the first slot) chooses differently in roughly half of real claims. This is
the one dimension where "single unrestricted path" does not translate into
"reliably taken" — reconcile with the coverage audit's 100% *candidate*-level
EXECUTION probe rate by noting the grain difference: a candidate with up to
3 claims only needs `OPERATING_CONTEXT` on *one* of them to register fully
covered, so the per-claim 52% still nets out to full coverage at the
candidate level.

### PROBLEM_SOLVING — openers: `FAILURE`, `DEPENDENCY`

`FAILURE` is nominally the guaranteed move #2 in every ladder; selected on
43/100 claims (43.0%), never blocked by archetype/seniority/precondition —
same **planner-choice** failure mode as EXECUTION. `DEPENDENCY` is
archetype-gated to `METRIC_MOVE`+`BUILD` (44% of claims), selected 11/44
(25.0%), also unblocked otherwise — its shortfall is planner choice, not a
structural gate. At the candidate level, `FAILURE` is asked to essentially
every candidate on at least one claim (0 of 39 candidates got neither
opener), which is why PROBLEM_SOLVING reads 100% at the aggregate level in
the coverage audit despite each individual claim only having a ~43-68%
chance of it.

### JUDGMENT — openers: `EXCLUSION`, `AUTHORITY`

The two-path dimension most damaged by seniority gating:

- `EXCLUSION`: in-ladder on 79 claims, but **only 21 clear the senior-only
  gate** — 58 of 79 (73.4%) are blocked by seniority outright, the single
  largest seniority block of any move in the system. Of the 21 that clear
  it, only 6 are actually asked (28.6%); 15 more are eligible and simply
  never reached.
- `AUTHORITY`: in-ladder on 56 claims, mid/senior gate blocks 21 (37.5%),
  leaving 35 available; of those, 14 asked (40%) and 21 eligible-not-selected
  (exactly as many as were blocked outright — seniority and pure scheduling
  contribute equally here).

Failure mode: **seniority first, budget position second.** At the candidate
level, 24 of 39 candidates (61.5%) never had either opener asked at all —
and 12 of those 24 (50%) still scored JUDGMENT > 0 anyway, via the backdoor
in §0b, not via either intended path.

### OWNERSHIP — openers: `OWNERSHIP_BOUNDARY`, `PEOPLE`

The worst-covered dimension in the whole framework, and archetype exclusion
is why: both openers exist only in `Archetype.OWNERSHIP` and
`Archetype.VOLUME` — **21% of all claims, combined.** `OWNERSHIP_BOUNDARY`:
available 11, selected 6 (54.5%, the *highest* selection rate of any
archetype-restricted move when it is available — this path works fine when
offered). `PEOPLE`: available 21, selected just **2 (9.5%)** — the least-used
move in the entire nine-move system, with no seniority or precondition gate
explaining the gap; this is pure planner-choice neglect of an eligible,
unblocked move.

Failure mode: **archetype exclusion first** (79 of 100 claims never offer
either opener at all, regardless of anything else), **planner choice
second** for the 21% that do. Candidate-level: 31 of 39 (79.5%) never got
either opener; 11 of those 31 (35%) still scored OWNERSHIP > 0 via the
backdoor.

### ADAPTABILITY — opener: `PERTURB` (only one path)

The single most fragile dimension in the framework: one path, and that path
is senior-only. In-ladder on all 100 claims (every archetype), but the
`LEVEL_RESTRICTED = {"senior"}` gate blocks 47 of them (47.0%) outright —
before budget or planner logic ever gets a say. Of the 53 that clear the
gate, 31 are selected (58.5%, the highest available→selected conversion of
any restricted move), with 20 more eligible-and-unblocked-but-not-reached
and 2 lost to planner choice specifically.

Failure mode: **seniority, categorically** — any junior or `seniority=None`
candidate (18 of 39, 46% of this corpus) has zero chance of ADAPTABILITY
being genuinely opened, no matter how the rest of the interview goes,
because there is no second path to fall back on. This is the one dimension
where "only one viable opening path" and "that path is gated" compound into
the starkest single point of failure in the six-dimension framework.

---

## 3. Which dimensions have only one viable opening path

**EXECUTION** (`OPERATING_CONTEXT`) and **ADAPTABILITY** (`PERTURB`) are the
only single-opener dimensions. They fail in opposite ways:

- EXECUTION's one path is *unrestricted* (no archetype or seniority gate) but
  under-*selected* in practice (52% per-claim) — a planner-ordering problem
  with no structural blocker behind it, and it's rescued at the candidate
  level by having up to 3 chances per interview.
- ADAPTABILITY's one path is *restricted* (senior-only) and has no fallback —
  a structural blocker with no planner fix available, because there is no
  second move to reach for. This is a categorically worse failure mode than
  EXECUTION's: a scheduling problem can be fixed by reordering the planner;
  a single seniority-gated path with no alternative cannot be fixed without
  either loosening the gate or adding a second opener.

## 4. Which dimensions are blocked by which mechanism

| Mechanism | Dimensions it dominates | Evidence |
|---|---|---|
| **Archetype exclusion** | OWNERSHIP (79% of claims structurally ineligible), KNOWLEDGE (93% ineligible for `METRIC_DEFINITION`) | Decided by a text regex on the claim (`anatomy._archetype()`) before any question is planned |
| **Seniority gate** | ADAPTABILITY (47% blocked outright), JUDGMENT (`EXCLUSION` 73.4% blocked, `AUTHORITY` 37.5% blocked) | `LEVEL_RESTRICTED` in `question.py:1094-1098`; `seniority=None` blocks all three restricted moves at once |
| **Budget position / scheduling** | JUDGMENT (36 eligible-not-selected instances combined), OWNERSHIP (24 combined), ADAPTABILITY (20) | Moves that cleared every gate and still weren't reached before the 6-question ceiling |
| **Planner choice** (move fully available, unblocked, still skipped) | EXECUTION (48% of claims), PROBLEM_SOLVING (57%/75% for `FAILURE`/`DEPENDENCY`), OWNERSHIP's `PEOPLE` (90.5%) | These moves have zero archetype or seniority restriction — their under-use is entirely an ordering/momentum decision, not a structural gate |
| **Runtime precondition** (not one of the four requested, but real and load-bearing) | KNOWLEDGE's `COHERENCE` (0% selected corpus-wide) | Needs two cross-answer facts sharing a referent — a bar most short claim interviews never clear |

A fifth mechanism outside all four requested categories also constrains
every dimension simultaneously: **~20% of the total question budget
(`thread` + `repair` turns) carries no `Move` at all** (§0a), shrinking the
effective budget available for any dimension-opening move before archetype,
seniority, or planner logic ever applies.

---

## Answer to the question asked

> For each dimension, what are all possible paths from claim → move →
> question → evidence → dimension opening, and where do those paths fail in
> practice?

- **EXECUTION**: one path (`OPERATING_CONTEXT`), structurally always open,
  fails on **planner choice** — asked on only 52% of individual claims
  despite zero gating, rescued at the candidate level by repetition across
  claims.
- **PROBLEM_SOLVING**: two paths (`FAILURE`, `DEPENDENCY`), both structurally
  open, both fail on **planner choice** the same way EXECUTION does.
- **ADAPTABILITY**: one path (`PERTURB`), fails on a hard **seniority gate**
  (47% blocked with no fallback) — the most fragile single point of failure
  in the framework.
- **JUDGMENT**: two paths (`AUTHORITY`, `EXCLUSION`), both fail primarily on
  the **seniority gate** and secondarily on **budget position**; over half
  the corpus never had either genuinely asked.
- **OWNERSHIP**: two paths (`OWNERSHIP_BOUNDARY`, `PEOPLE`), fail primarily
  on **archetype exclusion** (79% of claims never eligible) and secondarily
  on **planner choice** (`PEOPLE` used in only 9.5% of its eligible
  opportunities).
- **KNOWLEDGE**: two paths, one gated by **archetype** to 7% of claims, the
  other dead on **runtime precondition** (0% selected corpus-wide) — the
  weakest dimension in the framework by every measure that isolates it from
  the scoring-side backdoor described in §0b.

Layered on top of all six: roughly a fifth of every interview's fixed
question budget is spent on `thread`/`repair` turns that cannot open any
dimension through its intended path at all, and the claim-aggregate `probed`
flag credits a dimension from incidental scoring often enough (up to 72% of
"neither opener asked" cases, for KNOWLEDGE) that a large share of what any
dashboard currently reports as "opened" did not travel through any of the
paths documented above.
