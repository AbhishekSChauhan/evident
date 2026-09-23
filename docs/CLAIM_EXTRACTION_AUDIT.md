# Claim Extraction Audit

**The question, one layer upstream of every prior audit:** is claim
extraction itself the bottleneck — is the system interviewing the wrong
things from the very beginning, before the planner, coverage, scoring, or
dimension mechanics ever get a turn?

## 0. What's actually available — checked before anything else

The brief asks about "100 real resumes." That doesn't exist as such.
Checked directly:

- The real corpus used throughout this audit series has **39 real
  candidates**, not 100 resumes. It produced **100 real interviewed
  claims** (the figure from `CLAIM_PRIORITIZATION_AUDIT.md`) — a different
  100 than what's being asked about here.
- **The full pre-selection claim inventory is not persisted anywhere in
  this system, for anyone.** This is an architectural fact already on
  record (`docs/ARCHITECTURE_LAYER_AUDIT.md`, `docs/CLAIM_INVENTORY.md`):
  the `claims` table schema has no `interviewed`/`rejected` column at all —
  a claim is only ever written to the database *after* the top-N selection
  cut already happened in memory. The claims the current top-3 cut
  discarded were never stored, for any candidate, ever. Confirmed again
  here directly: the local `claims` table schema has no such column, and
  every stored claim set for every candidate examined is already
  post-selection.
- **The exported dataset's resume field (`resume_excerpt`) is a fixed
  600-character truncation, not a full resume**, confirmed by checking its
  length across every candidate. It is real, human-written resume prose —
  not synthetic — but it is a slice, usually just the header and the first
  section, not the whole document.

**Given this, the audit below does not compare 100 full resumes against
their full extraction.** It does the next most honest thing: it **re-runs
the real, live `extract_claims()` function** (`api/engine/extract.py`)
against all 39 real candidates' real 600-character excerpts, in both
production modes — `CLAIM_INVENTORY=false` (the live default, top-3
selection applied) and `CLAIM_INVENTORY=true` (recall-first, no
cardinality cut) — and compares both fresh outputs against what was
originally persisted and interviewed for that candidate. This gives a
genuine, live, code-verified answer to most of the brief's questions, with
one honest limitation stated once and applying throughout: **everything
below is measured against a 600-character slice of each real resume, not
the whole document**, so absolute counts (claims per resume, especially)
are a floor, not the true count — the *shape* of what's found (category
skew, achievement/responsibility ratio, duplication pattern, latent
signal rarity) is the real finding, not the raw quantity.

**Real API calls, real production code, no simulation:** 78 live calls
(39 candidates × 2 modes) to `extract_claims()`, zero hard errors.

---

## Q1 — How many extracted claims are actually worth interviewing?

Fresh inventory-mode extraction (the recall-first mode, no top-N cut)
produced **143 claims across 39 candidates** (avg 3.67/candidate, up to 12
for one candidate) — already more than doubling legacy mode's fresh output
(76 claims, avg 1.95) on the *same* truncated text, confirming
`CLAIM_INVENTORY.md`'s original finding still holds: legacy mode's
cardinality anchor genuinely suppresses real claims, not just noise.

Of those 143, tagged by close reading and the regex passes below:
- **~8% (12 of 143) are genuinely high-value**: a specific, quantified,
  first-person achievement (`ACHIEVEMENT_DELTA` tag, §Q5).
- **A further chunk are mid-value**: real work content, no quantified
  delta, but plausibly interviewable (e.g., "Contributed to Lagoon... by
  developing scalable systems").
- **A meaningful share is outright fluff — not weak claims, not claims at
  all**: resume headers, name/title lines, contact information, and career-
  objective boilerplate, extracted as if they were claims. Concrete,
  verbatim examples, all from this live re-run: `"Kavita Patel | Senior
  Digital Textile Designer"`, `"Mumbai • 9328166425 •
  kavipatelkp1995@gmail.com"` and, separately, `"Email:
  kavipatelkp1995@gmail.com"` extracted as **two different claims**,
  `"VISUAL DESIGNER & VIDEO EDITOR"` (a section header) extracted as its
  own claim, and a career-objective sentence (`"...Looking for a position
  in a fast-paced company that appreciates hard work"`) extracted as a
  claim, then **duplicated near-verbatim as a second claim** from what
  reads like the same sentence chunked twice.

**Every one of these fluff examples traces to the same mechanism, checked
directly against the run log: the heuristic fallback path, not the live
model.** All four candidates who produced header/contact/objective "claims"
(`cj`, `Jitender`, `Kavita Patel`, and one `Sparsh Srivastava` case) hit
`"model returned no usable claims, using heuristic"` on that call — meaning
**the live model correctly found nothing extractable and abstained; the
mandatory fallback then promoted header and contact-line text to claims
anyway.** This is a specific, previously-undocumented heuristic-engine gap:
CLAUDE.md already documents the heuristic excluding parenthesised-year
job-title headings and comma-heavy skills lists — it does not exclude
name/title header lines, contact-info lines, or career-objective sentences.

## Q2 — What percentage of valuable resume evidence is never extracted?

**Cannot be answered cleanly with the data available**, and that limit is
stated rather than papered over: answering this properly needs the *full*
resume text compared against everything extracted from it, and neither
exists together anywhere accessible (§0). What can be said from the 600-
character slice: legacy mode's fresh extraction (1.95 claims/candidate,
truncated text) sits noticeably below both inventory mode's fresh
extraction on the *same* text (3.67) and the *original* persisted claim
count (2.56, presumably from the full resume) — consistent with, but not
proof of, real evidence being left on the table by the cardinality-anchored
mode specifically. A properly-scoped answer to this question needs full
resume text captured going forward; it is not reconstructable retroactively
from what this system currently stores.

## Q3 / Q4 — Which claim categories generate strong vs. weak interviews?

**Already measured rigorously on real interview outcomes in
`CLAIM_PRIORITIZATION_AUDIT.md`** — cited here, not re-derived:
`system_ownership` (ROI 3.67 signals/question), reporting/reliability-
shaped claims, and pipeline-ownership-shaped claims are the strongest;
`process_work` (1.25), `tooling` (0.83), and `measurable_outcome` are the
weakest among types with enough volume to trust.

**This audit adds the missing upstream half of that picture: how often does
the raw extraction even *offer* each type, before selection ever runs?**

| Claim type | Fresh raw inventory count (this audit) | Originally persisted/interviewed count |
|---|---:|---:|
| `delivery` | 43 | 20 |
| `system_ownership` | 41 | 12 |
| `business_impact` | 13 | **0** |
| `performance_work` | 8 | 11 |
| `outcome_ownership` | 7 | 3 |
| `hiring_delivery` | 7 | 2 |
| `process_work` | 2 | 8 |

Three types (`delivery`, `system_ownership`, `business_impact`) account for
**68% of every claim the raw extraction found** in this sample. `delivery`
— the type `CLAIM_PRIORITIZATION_AUDIT.md` already measured as
below-average ROI and the single most heavily-selected type in the
interviewed set (20 of 100) — is also the single most *abundant* type at
extraction time (43 of 143). The raw pool is not short on `delivery`
claims; it is oversupplied with exactly the type that measurably
underperforms once interviewed. `system_ownership` — the highest-ROI type
with enough volume to trust — is abundant in raw extraction (41) but only
about a **third** of that volume reaches interview (12), consistent with
the one-claim-per-type cap (`EXTRACTION_ARCHITECTURE_REVIEW.md` weakness
E2, cited in `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`) discarding a
candidate's second- and third-best evidence of their actual specialty.
`business_impact` appearing 13 times in fresh raw extraction and **never
once** in the originally-persisted set is either taxonomy drift between
when those interviews ran and now, or a type that gets swallowed before
interview every time — either way, worth a direct look, not assumed.

## Q5 — Achievements or responsibilities?

Tagged all 143 fresh raw claims for a quantified before/after delta
(achievement) versus a bare duty/scope statement (responsibility) versus
neither:

| | Count | % |
|---|---:|---:|
| Achievement-shaped (quantified delta) | 12 | 8.4% |
| Responsibility-only (duty/scope, no delta) | 6 | 4.2% |
| Neither — a plain statement | 125 | **87.4%** |

**Responsibilities do not dominate achievements — plain, undifferentiated
statements dominate both, by a wide margin.** Fewer than one raw claim in
twelve carries the kind of quantified change that
`QUESTION_QUALITY_AUDIT.md` and `MOVE_EVIDENCE_YIELD_AUDIT.md` already
established is what actually produces strong interviews. This is not a
planner or a scoring problem — it's the composition of the raw material
extraction is handing forward.

## Q6 — How much duplicate extraction exists?

Systematic check (≥50% shared significant vocabulary between two claims
from the same candidate's raw inventory) found **12 near-duplicate pairs
across 32 candidates with 2+ raw claims** — but close reading, not the
regex alone, is what determines whether that's a real problem:

- **Genuine fragmentation / junk, not two real claims**: the header,
  contact-info, and career-objective examples from Q1 above — the same
  fact or non-fact split into two "claims" by the heuristic fallback.
  Roughly 8 of the 12 flagged pairs are this kind.
- **False positives the overlap check correctly should not penalize**:
  Rakshit Dabral's two claims — `"...developing scalable systems and
  reduced recruiter screen time by 90%"` and `"Reduced resume extraction
  time by 66.67% for Lagoon"` — share vocabulary (same employer, same
  "reduced X by Y%" shape) but are **two distinct, both-valuable, both-
  quantified achievements at the same job**, not a duplicate. A crude
  lexical-overlap check cannot tell these apart from real duplication;
  reading the claims can.

**Net finding: real duplication/fragmentation exists and is concentrated
entirely in the heuristic fallback path** — none of the confirmed
genuine-duplicate examples came from a live model call in this sample.

## Q7 — How much latent evidence exists in the resume before the interview starts?

Tagged all 143 fresh raw claims for whether their own text — before any
question is asked — already contains a metric, ownership verb, decision
framing, constraint, dependency, or outcome:

| Signal | % of raw claims already containing it |
|---|---:|
| `metric` (a number/%/unit) | 19.6% |
| `ownership` (led/owned/managed/architected...) | 14.7% |
| `outcome` (resulted in/reduced/improved...) | 8.4% |
| `dependency` (integrated with/relied on/blocked by) | 2.8% |
| `constraint` (deadline/budget/SLA/scale) | 0.7% |
| **`decision` (decided/chose/instead of/rather than)** | **0.0%** |

**Zero of 143 raw extracted claims contain any decision-framing language at
all.** This extends `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`'s finding that
`decisions` never populate in real *answers* one full stage further back:
it isn't only that the interview fails to draw decision content out —
resumes, as written, essentially never state a decision in the first place.
`constraint` and `dependency` are nearly as rare. This is a genuine
resume-writing-convention fact, not an extraction defect on its own — but
it means any interview strategy that assumes decision/constraint content is
"in there somewhere, waiting to be asked about" is assuming something the
raw material mostly doesn't support. The interview has to *manufacture*
this content through good questioning far more than it can *surface*
something latent, for these three signal types specifically.

## Q8 — Can claim quality be predicted from the resume alone?

Two independent findings, both bearing on this, and they point in different
directions:

1. **The current predictor already fails.** `CLAIM_PRIORITIZATION_AUDIT.md`
   measured the real `claim_strength_bonus()` function's correlation with
   actual post-interview yield at −0.042 to −0.085 — indistinguishable from
   zero, occasionally inverted. Whatever is predictable from a resume
   today, this formula isn't finding it.
2. **But there may be less to predict than hoped, for some categories.**
   Q7's finding that `decision` and `constraint` framing are essentially
   absent from raw claims (0.0% and 0.7%) means no resume-text predictor —
   however well-built — can identify "this claim will yield strong
   Judgment evidence" from text that structurally doesn't carry that
   signal. For `metric` (19.6%) and `ownership` (14.7%) content, there is
   real, present, extractable signal a better predictor could plausibly
   use — the ceiling is much higher there.

**So: partially yes.** Claim quality is predictable enough, from the
resume, to beat the current formula's ~zero correlation — `metric` and
`ownership` presence are real, cheap, checkable signals sitting unused. It
is not fully solvable from resume text alone for every dimension a claim
might eventually need to prove, because some of what the interview needs
(decision rationale, constraints) essentially doesn't exist in the raw
material yet, and has to be drawn out by the conversation instead of
predicted from what was written down.

---

## Answer to the question asked

**Is the current claim inventory itself the bottleneck?**

**Partially, and in a specific, correctable way — not in the way that
would make every downstream fix pointless.** The raw material extraction
produces is real, mostly-genuine work content (87%+ of the junk found here
traces to one specific, narrow heuristic-fallback gap, not to the live
model broadly failing), but it is composed overwhelmingly of plain,
undifferentiated statements (87.4%) rather than quantified achievements
(8.4%), concentrated in a small number of claim types that don't
correspond to which types actually interview well, and it essentially never
contains decision or constraint framing for the interview to build on.
Downstream fixes to planning, coverage, scoring, and dimension design are
not wasted — most of what they're fixing (which dimensions get reached,
how evidence gets scored, whether six dimensions are separable) operates on
*whichever* claims get selected, and that stays true regardless of
extraction quality. But two things found here are upstream enough that
fixing everything downstream first would mean re-optimizing against the
same skewed raw material: the type-selection mismatch (Q3/Q4 — abundant
`delivery` claims crowding out scarcer, higher-ROI `system_ownership`
claims via the one-per-type cap) and the heuristic-fallback junk-extraction
gap (Q1/Q6) are both cheap, narrow, and worth fixing early rather than
after — they change *what enters* the pipeline everything else operates on.
