# Evidence Gap Framework

**Correction (post-publication, same day):** §7's original claim that six
gaps were sufficient was checked against the data on challenge and did not
hold. See the addendum at the end of this document — the minimal set is
eight, not six. The body below is left as originally written, with the
addendum layered on top, so the record shows the error and the correction
rather than silently rewriting history.

**Objective:** identify what evidence is actually still missing after each
real answer, build a taxonomy of gap types, and determine the minimal set
required to turn a claim into strong evidence. No implementation proposal —
this is a diagnosis, continuing directly from `PLANNER_STRATEGY_AUDIT.md`'s
finding that the planner optimizes for move sequence, not missing
information.

**Method.** A gap taxonomy of 12 categories (below) was defined from the
brief's own examples plus the system's existing signal vocabulary
(`AnswerSignals`' buckets, `MOVE_DIMENSIONS`, `THREAD_ENTITY_QUESTIONS`).
Each of the 212 real answers in the 39-candidate corpus
(`studies/evidence_export_prod/03_evidence_yield_per_question.csv`) was
tagged for the *presence* of each category using consistent regex heuristics
— the same rigor level as the prior `QUESTION_QUALITY_AUDIT.md` and
`MOVE_EVIDENCE_YIELD_AUDIT.md` tagging passes, not a claim of perfect
semantic detection. A category **absent** from an answer is the **gap that
remains after that answer**. Sample sizes are reported throughout; anything
under ~10 is flagged as directional, not conclusive.

---

## 1. The taxonomy

| Gap | What "closed" looks like in an answer |
|---|---|
| `OPERATING_CONTEXT_DETAIL` | Names the concrete artifact/system worked from (dashboard, report, log, ticket, pipeline) |
| `CAUSAL_CHAIN` | Cause → effect language (because, led to, resulted in, traced to) |
| `CONSTRAINT` | A limit, threshold, budget, SLA, or compliance boundary that shaped the work |
| `TOOL_USAGE_DETAIL` | A named tool plus *how* it was used, not just that it was used |
| `QUANTITY` | A number, percentage, or measured unit |
| `TRADEOFF` | An explicit comparison ("instead of," "rather than," "versus") |
| `METRIC_DEFINITION` | How a cited metric was actually measured or derived |
| `FAILURE_ANALYSIS` | A root cause identified and a fix applied |
| `OUTCOME` | A stated result or end-state ("resulted in," "improved," "we achieved") |
| `OWNERSHIP_BOUNDARY` | First-person ownership language or a stated handoff point |
| `STAKEHOLDER_INTERACTION` | A named role/person interacting via a real verb (escalated, coordinated, negotiated) |
| `DECISION_RATIONALE` | A decision *and* its stated reason, together |

---

## 2. Which gaps appear most frequently (missing after the most answers)

| Gap | Missing in | Present (n) |
|---|---:|---:|
| `DECISION_RATIONALE` | **99.1%** | 2 |
| `STAKEHOLDER_INTERACTION` | 98.1% | 4 |
| `METRIC_DEFINITION` | 96.7% | 7 |
| `OWNERSHIP_BOUNDARY` | 95.8% | 9 |
| `FAILURE_ANALYSIS` | 94.8% | 11 |
| `OUTCOME` | 94.8% | 11 |
| `QUANTITY` | 94.3% | 12 |
| `TOOL_USAGE_DETAIL` | 94.3% | 12 |
| `TRADEOFF` | 93.4% | 14 |
| `CONSTRAINT` | 88.2% | 25 |
| `OPERATING_CONTEXT_DETAIL` | 83.5% | 35 |
| `CAUSAL_CHAIN` | 83.5% | 35 |

Every single category is missing from a large majority of real answers — the
median real answer in this corpus closes **zero or one** of these twelve
gaps, not several. The most universally missing three are exactly the ones
that require the candidate to *volunteer* something beyond the literal
question asked: a reason for a decision, a named person they interacted
with, and how a cited metric was actually produced. The least-missing two
(`CAUSAL_CHAIN`, `OPERATING_CONTEXT_DETAIL`) are also the two most directly
targeted by the moves asked most often (`FAILURE`/`DEPENDENCY`,
`OPERATING_CONTEXT` — see §4).

## 3. Which gaps are most predictive of high-value evidence

Average `signals_found` when the category is present vs. absent, ranked by
the gap between them (n ≥ 25 marked as robust; n < 10 as directional only):

| Gap | Lift | n present | Confidence |
|---|---:|---:|---|
| `OPERATING_CONTEXT_DETAIL` | **+4.10** | 35 | **Robust** |
| `TOOL_USAGE_DETAIL` | +3.91 | 12 | Directional |
| `TRADEOFF` | +3.71 | 14 | Directional |
| `OWNERSHIP_BOUNDARY` | +3.71 | 9 | Directional |
| `QUANTITY` | +3.65 | 12 | Directional |
| `CONSTRAINT` | **+3.39** | 25 | **Robust** |
| `METRIC_DEFINITION` | +3.36 | 7 | Directional |
| `CAUSAL_CHAIN` | **+2.97** | 35 | **Robust** |
| `FAILURE_ANALYSIS` | +2.42 | 11 | Directional |
| `OUTCOME` | +1.94 | 11 | Directional, **lowest lift** |
| `DECISION_RATIONALE` | +5.16 | 2 | Too small to trust |
| `STAKEHOLDER_INTERACTION` | +3.42 | 4 | Too small to trust |

The three statistically robust findings (n ≥ 25) all point the same
direction: closing `OPERATING_CONTEXT_DETAIL`, `CONSTRAINT`, or
`CAUSAL_CHAIN` in an answer roughly **doubles to triples** the evidence
yield of that turn relative to an answer that doesn't close it. `OUTCOME`
has the lowest lift of any category with a usable sample — an answer that
merely states a result, with no cause or constraint attached, is the weakest
form of "closed gap" this taxonomy can detect. This matches
`EVIDENT_MASTER_CONTEXT.md`'s own framing directly: *"The claim is not
valuable. The evidence behind the claim is valuable"* — a bare outcome is
closer to a claim restated than to evidence.

## 4. Which existing moves are actually attempting to close each gap

| Gap | Move(s) targeting it | How directly |
|---|---|---|
| `OPERATING_CONTEXT_DETAIL` | `OPERATING_CONTEXT` | Direct, by design (its entire brief) |
| `CAUSAL_CHAIN` | `FAILURE`, `DEPENDENCY`, `COHERENCE` | Direct — these are the corpus's actual causal-density leaders (`MOVE_EVIDENCE_YIELD_AUDIT.md` §2) |
| `FAILURE_ANALYSIS` | `FAILURE` | Direct, by design |
| `CONSTRAINT` | `EXCLUSION` (the reason something stayed untouched), `AUTHORITY` (the approval boundary) | Indirect — neither move's brief names "constraint" as its primary target |
| `OWNERSHIP_BOUNDARY` | `OWNERSHIP_BOUNDARY`, `PEOPLE` (partially) | Direct for the first, incidental for the second |
| `STAKEHOLDER_INTERACTION` | `PEOPLE` | Direct, by design, but the least-used move in the system (9.5% of eligible opportunities, `MOVE_EVIDENCE_YIELD_AUDIT.md` §1) |
| `METRIC_DEFINITION` | `METRIC_DEFINITION` | Direct, by design, but the worst-performing move when scheduled cold (§1, same audit) |
| `QUANTITY` | **None, deliberately** | `question.py`'s `_PROHIBITED` regex explicitly forbids asking "how many/how much" directly (`DIMENSION_OPENING_AUDIT.md` §2); this gap is closed only incidentally, never targeted |
| `TOOL_USAGE_DETAIL` | `OPERATING_CONTEXT` (partially), `DEPENDENCY` (partially, via named blocking libraries) | Incidental in both — no move asks "how did you use this tool" as its primary target |
| `TRADEOFF` | None of the ten moves directly | Closest formal analog is `AUTHORITY`'s decision-boundary framing, which asks *what* was decided, not what was weighed against what |
| `OUTCOME` | None of the ten moves directly | `PERTURB` explicitly forbids asking for outcomes by design (`question.py:1246-1252`, "this did not happen, so there are none"); `FAILURE`'s "what happened" implies but doesn't require a stated end-state |
| `DECISION_RATIONALE` | `AUTHORITY` (partially — asks what was decided, not why) | Incidental — the *reason* behind a decision is not the move's stated target, only the decision boundary itself |

## 5. Which gaps currently have no dedicated collection mechanism

Three gaps have **no move whose actual design brief targets them**, and (per
§6) no reliable substitute either:

- **`OUTCOME`** — the weakest-covered gap in the entire framework by every
  measure here: no move's brief asks for it directly, `PERTURB` is
  explicitly forbidden from asking for it, and it also has the lowest
  predictive lift of any category with a usable sample. A claim can move
  through this interview's entire question budget without anything ever
  directly asking "what actually happened as a result."
- **`TRADEOFF`** — no move asks for an explicit comparison between two paths
  considered. `AUTHORITY` gets close (decision boundaries) but its own brief
  asks for the boundary, not the comparison that produced it.
- **`DECISION_RATIONALE`** (the *why*, not the *what*) — `AUTHORITY`
  reliably produces the decision and its escalation boundary
  (`QUESTION_QUALITY_AUDIT.md`'s `AUTHORITY` cluster), but nothing in the
  formal ladder asks the candidate to justify *why* one option was chosen
  over another.

`QUANTITY` is a fourth case, but a different kind: it has no dedicated
mechanism **by explicit design choice**, not by omission — the product
deliberately never asks for a number directly, on the reasoning that a
number requested is a number that can be invented. It is listed separately
because "no mechanism" here reflects a considered decision already visible
in the codebase, not a gap in this taxonomy's coverage.

## 6. Which gaps are being collected accidentally through `thread`

Cross-referencing `THREAD_MECHANISM_AUDIT.md`'s entity table against this
taxonomy:

| Gap | Thread entity that (sometimes) closes it | Observed in the real corpus? |
|---|---|---|
| `CONSTRAINT` | `api`, `approval`, `metric` | Yes — thread has the **highest constraint density of any mechanism measured**, raw or normalized (`MOVE_EVIDENCE_YIELD_AUDIT.md` §2) |
| `METRIC_DEFINITION` | `metric` | Yes — outperforms the formal `METRIC_DEFINITION` move dramatically when triggered (`THREAD_MECHANISM_AUDIT.md` §1, §3) |
| `FAILURE_ANALYSIS` / `CAUSAL_CHAIN` | `report`, `bug` | Yes — `report`-entity threads directly ask "what root cause did that report reveal" |
| `OWNERSHIP_BOUNDARY` | `team`, `ticket` | Yes, partially — "what boundary of responsibility did you own versus the escalation team" |
| `STAKEHOLDER_INTERACTION` | `team`, `manager`, `customer` | Yes, incidentally — these entities name a role, though the canned question doesn't always ask what that person *did* |
| `DECISION_RATIONALE` | `approval`, `manager` | Partially — "what specific criteria... were required" gets at rationale-adjacent content without asking for it as explicitly as a dedicated move would |
| `TRADEOFF` | `library` | **Defined but never observed** — `library` never fired once in 212 real questions (`THREAD_MECHANISM_AUDIT.md` §1); the one thread entity built to close this gap has no evidence it ever has |
| `OPERATING_CONTEXT_DETAIL` | `dashboard`, `report` | Yes, but only as reinforcement of a gap the parent `OPERATING_CONTEXT` move usually already closed |
| `QUANTITY`, `OUTCOME`, `TOOL_USAGE_DETAIL` | None of the 17 entities target these | **Not covered by thread either** |

`OUTCOME` is now confirmed as the single gap with **no collection path at
all** in the current system — not the formal ladder, not the accidental
follow-up mechanism.

---

## 7. The minimal Evidence Gap Framework

Collapsing categories that are either redundant (a quantity is almost always
carried *inside* a metric definition or a constraint, not free-standing) or
that the product has already deliberately chosen not to ask for directly
(`QUANTITY`), the twelve measured categories reduce to **six non-overlapping
gaps** that between them cover what `EVIDENT_MASTER_CONTEXT.md`'s six
competence dimensions actually need to open:

| Minimal gap | Absorbs | Competence dimension it feeds |
|---|---|---|
| **What did they actually work from** (`OPERATING_CONTEXT_DETAIL`) | — | EXECUTION |
| **What went wrong and why** (`CAUSAL_CHAIN` + `FAILURE_ANALYSIS`) | root-cause diagnosis | PROBLEM_SOLVING, KNOWLEDGE |
| **Why this choice, not another** (`DECISION_RATIONALE` + `TRADEOFF`) | the comparison behind a decision | JUDGMENT |
| **What boundary constrained the work** (`CONSTRAINT` + `METRIC_DEFINITION` + `QUANTITY`) | a limit, a threshold, or a measured baseline — the number only counts once it's attached to one of these | JUDGMENT, KNOWLEDGE |
| **What was personally theirs** (`OWNERSHIP_BOUNDARY`) | — | OWNERSHIP |
| **What actually resulted, and for whom** (`OUTCOME` + `STAKEHOLDER_INTERACTION`) | the end-state and who it affected or confirmed it | OWNERSHIP, and the verifiability every other gap depends on |

This is the minimal set in a specific sense: each of the six maps to
evidence a competent human interviewer would consider a claim
under-evidenced without, each is empirically distinguishable from the
others in this corpus (no two collapse to the same regex/behavior), and
removing any one of them would leave a hole none of the remaining five
covers even partially (confirmed against §4's move-mapping and §6's
thread-mapping tables — every one of the twelve original categories maps
into exactly one of these six, none is orphaned).

Two of the six (`OUTCOME`/verifiability, and the "why this choice" pairing)
are the ones this audit found have **no dedicated collection mechanism
today, formal or accidental** — which, read against
`PLANNER_STRATEGY_AUDIT.md`'s finding that the planner tracks move sequence
rather than missing information, is the same diagnosis from a different
angle: a gap-first planner would notice these two are the ones still open
on almost every claim and go looking for them; a move-first planner has no

---

## Addendum — the six were not sufficient

Challenged directly on whether six was really the minimal set, and checked
against the data rather than defended: **no.** Two real omissions, at two
different confidence levels.

### Confirmed empirically: `PROCESS_SEQUENCE`

A multi-step methodology description ("first I did X, then Y, then Z") is
not the same thing as `OPERATING_CONTEXT_DETAIL`. Naming *what artifact* was
looked at is a noun; describing *the sequence of actions taken* is a chain
of steps, and it corresponds to a different bucket in the system's own
`AnswerSignals` schema (`process_steps`, the primary opener of EXECUTION's
scoring gate) — not to the artifact-naming this framework's
`OPERATING_CONTEXT_DETAIL` pattern actually detects. It was present in the
original Question Quality Audit's tagging and was dropped, incorrectly
folded into `OPERATING_CONTEXT_DETAIL`, when this document's twelve
categories were distilled.

Tested against the same 212 real answers:

| | Value |
|---|---|
| Present in | 49/212 answers (23% — more common than `CAUSAL_CHAIN` or `CONSTRAINT`) |
| Lift | **+3.62** (5.67 avg signals present vs. 2.06 absent) — on par with the framework's strongest robust findings |
| Direct proof of non-redundancy | Of the 20 highest-yield answers in the whole corpus, 2 match **none** of the original twelve categories; one of those two is carried entirely by `PROCESS_SEQUENCE` |

This is not a marginal miss — it is independently predictive, more frequent
than two of the "robust" categories already in the framework, and
demonstrably not covered by anything in the six.

### Structurally certain, not independently re-validated: `ADAPTABILITY` / transfer reasoning

Visible by inspection, not by a new regex: re-reading §7's own mapping
table, five of the six competence dimensions (EXECUTION, PROBLEM_SOLVING,
KNOWLEDGE, JUDGMENT, OWNERSHIP) are fed by at least one of the six gaps.
**ADAPTABILITY is fed by none of them.** The reason is already on record in
`PLANNER_STRATEGY_AUDIT.md` §1: `PERTURB` doesn't close a gap latent in what
the candidate already said, the way the other nine moves do — it
*manufactures* a hypothetical the candidate has no prior material for.
Because this framework's twelve categories were built by asking "what is
missing from an answer already given," a need that doesn't exist until a
hypothetical is introduced structurally cannot appear in that taxonomy. A
quick regex attempt to confirm this quantitatively returned too few matches
(n=2) to be worth citing as evidence — this omission is argued from the
structure of the framework's own construction, not newly measured.

### Weaker, unconfirmed candidate: generalizable concept explanation

A recurring pattern in some of the richest answers already quoted across
the prior audits (Ayush's feature-importance/leakage explanation is the
clearest instance) is a **generalizable explanation of a domain mechanism**
("this is usually a sign of X"), distinct from `CAUSAL_CHAIN`'s
instance-specific cause-and-effect and mapping to KNOWLEDGE's separate
`concepts` signal bucket. A quick regex test for it also returned too few
matches (n=2) to validate. Flagged as **argued, not confirmed** — worth a
properly-designed test before being added on the strength of this alone.

### Corrected minimal set: eight, not six

`OPERATING_CONTEXT_DETAIL`, `PROCESS_SEQUENCE`, `CAUSAL_CHAIN` +
`FAILURE_ANALYSIS`, `DECISION_RATIONALE` + `TRADEOFF`, `CONSTRAINT` +
`METRIC_DEFINITION` + `QUANTITY`, `OWNERSHIP_BOUNDARY`, `OUTCOME` +
`STAKEHOLDER_INTERACTION`, and an `ADAPTABILITY`/transfer-reasoning category
that behaves differently from the other seven (manufactured, not
discovered) but is required for the set to actually cover all six
competence dimensions the master context defines. The concept-explanation
candidate is not added pending a real test.
mechanism to notice they're missing at all.
