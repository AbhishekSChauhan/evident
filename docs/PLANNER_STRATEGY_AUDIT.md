# Planner Strategy Audit — Move-First or Evidence-Gap-First?

**Objective:** using the five prior audits (`COVERAGE_REACHABILITY_AUDIT.md`,
`DIMENSION_OPENING_AUDIT.md`, `MOVE_EVIDENCE_YIELD_AUDIT.md`,
`QUESTION_QUALITY_AUDIT.md`, `THREAD_MECHANISM_AUDIT.md`) plus a fresh
turn-by-turn trace of all 39 real interviews, determine whether Evident's
planner is currently optimizing for **(1) the next best forensic move** or
**(2) the next most valuable missing information** — and which of those two
strategies actually serves `EVIDENT_MASTER_CONTEXT.md`'s stated architecture:
**claim → evidence → competence → job fit.** No implementation proposal;
this is a diagnosis.

---

## 0. What "evidence-first" actually requires, per the master context

`EVIDENT_MASTER_CONTEXT.md` is explicit that the product's whole reason to
exist is converting a *claim* into *evidence*, not into a completed
questionnaire: *"The claim is not valuable. The evidence behind the claim is
valuable."* The evidence graph is claim → evidence → competence → job fit —
evidence is the necessary intermediate node, and nothing in that pipeline
rewards having asked a structurally complete set of moves if the moves
produced no evidence. That framing is the yardstick for everything below:
a planner decision is "good" here exactly to the extent it produces evidence,
not to the extent it executes the ladder correctly.

---

## 1. Per-move: information target, gap closed, and follow-up substitutability

| Move | What it collects | Gap it closes | Could a follow-up on the last answer get there more efficiently? |
|---|---|---|---|
| `OPERATING_CONTEXT` | The concrete artifact/telemetry the candidate used day-to-day (`MOVE_BRIEFS`) | EXECUTION (guaranteed ladder position 1, every archetype) | Not applicable to itself — it's the necessary opener, nothing exists yet to follow up on. But its own high-yield answers reliably *name* a follow-up-able entity (a report, dashboard, API), making it a good **seed** for the mechanism that does replace later moves (`THREAD_MECHANISM_AUDIT.md` §1, §4). |
| `FAILURE` | A specific remembered failure episode + its cause | PROBLEM_SOLVING | Partially. Recalling *that* an episode happened cannot be substituted by follow-up — that's new ground. But the causal-diagnosis clause that makes `FAILURE` valuable when it works ("...and what you discovered was the cause," `QUESTION_QUALITY_AUDIT.md`) is *exactly* what the `report`/`bug` thread entities ask for on an answer that already named a failure. Once a failure surfaces, extracting its cause is cheaper via follow-up than via a second cold `FAILURE`-shaped question. |
| `AUTHORITY` | Decision rights vs. escalation boundary | JUDGMENT | **Yes, routinely.** The `manager`/`approval` thread entities ask nearly identical content, fire for free whenever a candidate mentions those words (which happens often, in passing, during unrelated answers), and — unlike `AUTHORITY` — carry **no seniority gate** (`DIMENSION_OPENING_AUDIT.md` §2: `AUTHORITY` blocked on 37.5% of its own eligible opportunities by seniority alone). This is the clearest case in the framework of the same information being reachable two ways at wildly different cost. |
| `DEPENDENCY` | A moment a dependency blocked progress, and what happened | PROBLEM_SOLVING | No — it's the strongest move in the system on its own terms (highest causal density of any mechanism measured, `MOVE_EVIDENCE_YIELD_AUDIT.md` §1, no real low-yield wording cluster, `QUESTION_QUALITY_AUDIT.md`). The efficiency problem here isn't that a follow-up would beat it; it's that it's asked in only 25% of its 44 eligible opportunities (`DIMENSION_OPENING_AUDIT.md` §2) — under-used, not mis-designed. |
| `PEOPLE` | A named role in the loop and what they did | OWNERSHIP | Likely yes. The single least-used move in the system (9.5% of eligible opportunities, `MOVE_EVIDENCE_YIELD_AUDIT.md` §1) and weak when used; the `team` thread entity asks a closely related question (interface boundary/handoff) and performed adequately as a follow-up. Little evidence this move earns its own scheduled slot over a contingent follow-up. |
| `OWNERSHIP_BOUNDARY` | What part of the work was personally theirs | OWNERSHIP | Partially. Strong and specific when it fires (`QUESTION_QUALITY_AUDIT.md`'s high-yield cluster), and the `team`/`ticket` thread entities only approximate it. Its real problem is archetype exclusion (only 21% of claims are ever eligible, `DIMENSION_OPENING_AUDIT.md` §2) — an eligibility problem, not a redundancy with follow-up. |
| `EXCLUSION` | What was deliberately left alone, and why | JUDGMENT | No current substitute either way. Weak as a scheduled move (lowest answer-quality of any move with n≥5, `MOVE_EVIDENCE_YIELD_AUDIT.md` §1) *and* severely seniority-gated (73.4% blocked, `DIMENSION_OPENING_AUDIT.md` §2) *and* nothing in the 17-word thread vocabulary maps to "what didn't you do." This is a genuine gap on both sides of the comparison, not a case for either strategy over the other. |
| `PERTURB` | Hypothetical reasoning under one changed variable | ADAPTABILITY (sole opener) | **No, and this matters.** By construction this manufactures a *new* information need the candidate hasn't already produced material for — a follow-up on the last answer cannot substitute for asking about a scenario that never happened. This is the one move in the ladder that a pure evidence-gap-first strategy could not replace, because there is no existing gap to detect; the need has to be created. |
| `METRIC_DEFINITION` | How a cited metric was actually derived and verified | KNOWLEDGE | **Yes, dramatically.** The formal move's real yield is the worst in the entire system (0.33 avg signals, 66.7% dead-turn rate, `MOVE_EVIDENCE_YIELD_AUDIT.md` §1) and it's archetype-eligible on only 7% of claims. The `metric` thread entity asks almost word-for-word the same question ("what baseline threshold... and how did you verify it") **as a contingent follow-up**, and produced three of the corpus's highest-yield turns overall (sig 9, 7, 6 — `THREAD_MECHANISM_AUDIT.md` §1, §3). Same information target, same wording family, opposite outcome depending on whether it's scheduled cold or triggered by what the candidate just said. |
| `COHERENCE` | Reconcile two facts the candidate has already stated against each other | KNOWLEDGE (+ legacy CAUSAL_REASONING) | This move *is* evidence-gap-first by design — it doesn't introduce a topic, it targets a specific tension between two already-established facts. And it is the least-used move of all ten: **zero times in 212 real questions** (`DIMENSION_OPENING_AUDIT.md` §1), because its precondition (two independently-costed facts from different answers sharing a referent) never accumulates within the budget. The one formally gap-seeking move in the ladder is also the one that never fires. |

---

## 2. Turn-by-turn trace across all 39 real interviews

**Method:** every real turn (212 total, 173 turn-to-turn transitions once the
first turn of each session is excluded) was placed in its true global
chronological order (not per-claim) and classified by what the planner did
next: stay on the same claim with a `thread` follow-up, stay on the same
claim with a different forensic move, or abandon the claim for a different
one.

### How often does the planner abandon an active trail?

**63 of 173 transitions (36.4%) switch to a different claim.** The other
110 (63.6%) continue the same claim — 30 of those via `thread`, 80 via a
new forensic move.

### Does a follow-up produce more evidence than opening a new move?

**Yes, decisively, and the ranking has a specific, non-obvious shape:**

| What the planner did next | n | Avg signals produced | Dead-turn rate |
|---|---:|---:|---:|
| **Continue same claim, `thread` follow-up** | 30 | **4.10 (best)** | 20.0% |
| Switch to a different claim | 63 | 2.79 | 42.9% |
| **Continue same claim, new forensic move** | 80 | **2.39 (worst)** | **53.8% (worst)** |

The important finding is not just that follow-up beats opening a new move —
it's that **"go deeper on the same claim via the formal ladder" is the single
worst-performing action available to the planner, worse even than abandoning
the claim outright.** Asking a second, different scheduled move on a claim
already in progress currently produces less evidence, more often nothing,
than either a cheap contingent follow-up *or* just moving to fresh material.

### Is the switch decision driven by how much evidence was just produced?

**No — and this is the most direct evidence for the "move-first" diagnosis.**
If the planner were evidence-gap-first, switches should concentrate after
unproductive turns and continuations after productive ones. The data show
close to the opposite:

- Average signals of the turn **just before** a switch-away: **3.02**.
- Average signals of the turn **just before** a same-claim continuation:
  **2.73** — *lower*, not higher.
- **28.6% of switches abandon a claim that just produced a genuinely hot
  answer (≥5 signals).**
- **42.7% of same-claim continuations happen right after a turn that
  produced zero signals** — the planner disproportionately "doubles down" on
  material that just proved unproductive, rather than recognizing it and
  moving on.

This is the clearest single result in this audit: **the decision to
continue or abandon a claim is not being made on the basis of how much
evidence the last answer contained.** It is being made on the basis of
structural position — breadth-first-then-depth scheduling, claim budget caps,
and ladder order (`plan_next_forensic`, cited in the coverage and dimension
audits) — which is definitionally a move-first policy: it asks "what does
the ladder say comes next" rather than "what did the candidate just leave on
the table."

### Quantifying the evidence loss from context-switching

Of the 63 switch-away transitions, 22 followed an answer that had already
named a thread-triggerable entity (`report`, `metric`, `api`, etc.) — a
directly observable, specific, missing-information cue that the planner had
in hand and did not act on before moving to different material. Where the
planner *did* act on that same kind of cue (the 30 seized threads), it
averaged 4.10 signals; where it switched away from a cue instead, the next
new-claim turn averaged 2.79.note

Extrapolated across all 63 switches at the gap between `thread`'s and
switching's average yield (4.10 − 2.79 = 1.31 signals): **the corpus would
have produced on the order of 80 additional evidence signals — roughly two
extra per candidate — if switch-away moments had been resolved as
follow-ups at the same rate thread already demonstrates is achievable.**
This is a directional estimate, not a certainty — thread's own vocabulary is
narrow (17 words) and would not have fired on every switch point, and some
switches are switching *to* genuinely necessary new ground (a fresh claim
that has had zero opening move yet). It is reported as an order of magnitude,
not a precise causal count.

*note: the 22-instance subsample where an entity was present but not
threaded skews toward later-in-claim entity mentions (thread's own firing
window is the claim's *first* answer only, `orchestrator.py:2134-2139`), and
in this specific subsample the claim-switch that followed actually
outperformed the seized-thread average (4.68 vs. 4.10) — a reminder that the
advantage demonstrated here is concentrated in the specific window thread
already covers, not a claim that switching is always worse than following
up in every circumstance.*

---

## 3. Synthesis: what is the planner actually optimizing for today?

Every measurement in this and the five prior audits points the same
direction:

- The planner's scheduling priority is **inverted relative to evidence
  value** — its highest-yield real moves (`AUTHORITY`, `OWNERSHIP_BOUNDARY`,
  `DEPENDENCY`) are its rarest and most gated; its guaranteed, always-asked
  moves (`OPERATING_CONTEXT`, `FAILURE`) are mediocre-to-poor
  (`MOVE_EVIDENCE_YIELD_AUDIT.md`).
- Coverage of the six competence dimensions is dictated by **archetype
  classification and seniority gates decided before any question is asked**,
  not by what the interview has actually learned so far
  (`DIMENSION_OPENING_AUDIT.md`, `COVERAGE_REACHABILITY_AUDIT.md`).
- The one formally-designed gap-seeking move, `COHERENCE`, never fires.
  The one mechanism that behaves like an evidence-gap detector, `thread`, is
  a 17-word keyword accident bolted on ahead of the entire forensic system,
  not a designed part of it (`THREAD_MECHANISM_AUDIT.md`).
- Turn-by-turn, the planner's continue-vs-abandon decision is **uncorrelated
  with the evidence value of the answer just given** (§2 above) — it
  abandons hot trails nearly 3 times in 10 and persists on dead ones more
  than 4 times in 10.
- "Going deeper" via the formal ladder is measurably the **worst** action
  available, underperforming both a cheap follow-up and simply moving on.

**Evident's planner today is Move-First.** It executes a pre-committed
archetype ladder, gated by seniority and claim-shape decided at extraction
time, indifferent to what the candidate's actual last answer contained. The
one part of the running system that behaves like an evidence-gap detector
was built as an unrelated hackathon shortcut and happens, by the accident of
which 17 words it watches for, to outperform the designed mechanism it sits
ahead of.

---

## Final determination

> Should Evident be **A) Move-first** or **B) Evidence-gap-first**?

**B) Evidence-gap-first** is the strategy that matches Evident's stated
goal. The master context defines the product's value as the claim → evidence
transition, not as ladder completion; every quantitative result across all
five prior audits and the fresh trace in this one shows evidence produced
per question tracks **what the candidate just revealed, and what is still
missing**, not **which move is next in a pre-set sequence**. The clearest
individual proof is `METRIC_DEFINITION` and `AUTHORITY`: the same
information target, asked cold on schedule, is the system's worst or most
artificially scarce performer; the same information target, triggered by a
gap the candidate's own words just exposed, is among its best. A
move-first planner cannot tell those two situations apart, because it isn't
looking at the answer to decide what to do next — it's looking at the
ladder. An evidence-gap-first planner, by definition, is looking at exactly
the thing the master context says is the whole point: what evidence exists
so far, and what's still missing.
