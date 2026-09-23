# Dimension Validity Audit

**Question:** do Knowledge, Execution, Problem Solving, Judgment, Ownership,
and Adaptability measure six distinct competencies in real interview data,
or is the current system measuring the same underlying evidence multiple
times under different labels? Tested three ways, at three different
grains, against real data: the formula itself (`signals.py`), all 39 real
candidates' final scores, and 32 real individually re-extracted answers with
signal-level ablation. All three agree.

---

## Part 1 — Signal → dimension dependency map

Read directly from the six live rubric functions
(`signals.py:310-578`, confirmed in `SCORING_SEMANTICS_AUDIT.md` §2) and
cross-checked against real usage frequency from
`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`'s 32-answer sample:

| Signal | Knowledge | Execution | Problem Solving | Judgment | Ownership | Adaptability | Real usage (of 32) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---:|
| `process_steps` | 0.4 | 1.0–1.5 | — | — | 0.5* | — | 24 |
| `causal_links` (complete) | 0.6 | — | 1.0 | 0.4 | — | 1.0 | 19 (16 complete) |
| `causal_links` (partial) | — | — | — | — | — | 0.6 | (9 of the 19) |
| `decisions` | — | — | — | 1.0/0.5 | 0.4* | 0.5 | **0** |
| `constraints` | — | — | 0.5 | 0.5 | — | — | **0** |
| `boundaries` | — | — | — | — | 1.0 | — | **0** |
| `concept_explanations` | 1.0 | — | — | — | — | 0.5 | **0** |
| `incident_markers` | 0.6 | — | 1.0 | — | — | — | 2 |
| `metric_definitions` (defined) | 0.5 | — | — | — | — | — | 5 (3 defined) |
| `tools` (used) | — | 0.5 | — | — | — | — | 13 (8 used) |
| `quantities` | — | ≤1.0 total | — | — | — | — | 9 |
| `entities` (team/role) | — | — | — | — | 0.3 | — | 24 (some qualifying) |

`*` = only counts when phrased first-person (`_is_first_person_action`).

**Overlap count per signal:** `causal_links` feeds **four** dimensions,
`decisions` feeds **three**, `process_steps` feeds **three**,
`constraints` and `concept_explanations` each feed **two**. Only five
signal types are exclusive to one dimension: `boundaries` and `entities`
(Ownership), `metric_definitions`-defined and `concept_explanations`… no —
`concept_explanations` is shared (Knowledge + Adaptability); the true
exclusives are `boundaries` (Ownership), `entities` (Ownership),
`metric_definitions`-defined (Knowledge), `quantities` (Execution), `tools`-
used (Execution). **Every signal type real data shows populating more than
trivially (`process_steps`, `causal_links`) is shared across multiple
dimensions; every signal type that would be exclusive to Problem Solving,
Judgment, or Adaptability specifically (`decisions`, `constraints`,
`boundaries`, `concept_explanations`) measures at 0/32 real usage.**

**Is the overlap justified?** Some of it is defensible in principle — a
complete causal chain plausibly *is* evidence of domain knowledge (you
understood the mechanism), problem-solving (you diagnosed it), and
judgment (you chose the fix), and a real assessor might reasonably credit
several angles from one strong answer. What is not justified is the
*asymmetry*: three dimensions (Problem Solving, Judgment, Adaptability) have
**no signal type of their own at all** in the live formula — every input
they read is borrowed from another dimension's formula too. A framework
that calls something a "universal competence dimension" while giving it zero
independently-owned evidence is a labeling choice, not a measurement.

## Part 2 — Correlation analysis (measured, three ways)

**(a) All 39 real candidates, final reported scores** (includes every
mechanism already flagged elsewhere — the `score > 0` backdoor, unprobed=0):

| Pair | r |
|---|---:|
| Knowledge ↔ Execution | **0.973** |
| Problem Solving ↔ Judgment | **0.949** |
| Problem Solving ↔ Adaptability | 0.874 |
| Judgment ↔ Adaptability | 0.841 |
| Knowledge ↔ Adaptability | 0.819 |
| Execution ↔ Adaptability | 0.754 |
| Knowledge ↔ Problem Solving | 0.732 |
| Knowledge ↔ Judgment | 0.676 |
| Execution ↔ Problem Solving | 0.615 |
| Execution ↔ Judgment | 0.589 |
| Knowledge ↔ Ownership | 0.546 |
| Execution ↔ Ownership | 0.524 |
| Ownership ↔ Adaptability | 0.378 |
| Problem Solving ↔ Ownership | 0.352 |
| **Judgment ↔ Ownership** | **0.168 — the one genuinely weak pair** |

Filtering to only candidates where *both* dimensions were flagged `probed`
(controlling for the shared-budget confound) does not meaningfully change
this — Knowledge↔Execution stays at 0.961, Problem Solving↔Judgment at
0.935, Problem Solving↔Adaptability at 0.859 — except Judgment↔Ownership,
which drops further to **0.053** (n=15), i.e. indistinguishable from zero.

**(b) 32 real individual answers, re-scored at answer-level granularity**
(a completely independent check, at a finer grain than (a), using the same
real extractions from `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`):

The pattern replicates almost exactly — Problem Solving↔Judgment r=0.945,
Judgment↔Adaptability r=0.840, Problem Solving↔Adaptability r=0.778,
Knowledge↔Execution r=0.853 — **confirming the coupling is not an artifact
of aggregating many claims into one candidate score; it is present at the
level of a single answer**, which means it is a property of the formula,
not of interview length or candidate consistency.

**(c) Correlation after removing the shared signal (the causal experiment):**
re-running the same 32 answers with `causal_links` zeroed out:

- **Problem Solving↔Judgment, Judgment↔Adaptability, and Problem
  Solving↔Adaptability all become mathematically undefined (`nan`)** —
  because Judgment's and Adaptability's scores stop varying at all. Removing
  one signal type collapses two of six "universal competence dimensions" to
  a constant. This is not a correlational inference; it is a direct
  demonstration that, as currently implemented, **Judgment and Adaptability
  have no existence independent of `causal_links`.**
- Removing `causal_links` *increases* Knowledge↔Execution (0.853 → 0.889) —
  because that pair's coupling runs through a *different* shared signal.
  Removing `process_steps` as well collapses it from 0.889 to 0.236,
  isolating the true driver: **Knowledge↔Execution is coupled through
  `process_steps`, not `causal_links`** — the two high-correlation clusters
  in this framework each have their own distinct, identifiable mechanical
  cause, not one general "everything correlates" effect.

**(d) Correlation at the evidence level** (dimension score vs. a raw signal
count, not another dimension's score):

| | r |
|---|---:|
| Adaptability score ↔ raw `causal_links` count | **0.954** |
| Judgment score ↔ raw `causal_links` count | 0.729 |
| Knowledge score ↔ raw `causal_links` count | 0.261 |

**Direct answer to the questions asked:**
- *Does high Execution almost always imply high Ownership?* No —
  Execution↔Ownership sits at r=0.52 (candidate level) and even goes
  **negative** (−0.13 to −0.31) once the shared `process_steps`/`causal_links`
  signal is stripped out at answer level. Execution and Ownership are
  genuinely closer to independent than any other pair examined besides
  Judgment↔Ownership.
- *Does high Judgment almost always imply high Problem Solving?* Yes,
  essentially — r=0.945–0.949 across both grains, collapsing to an
  undefined (constant) relationship once their shared input is removed.
  These two are not measuring separable competencies in this data.
- *Does Adaptability simply mirror causal chains?* Yes, nearly exactly —
  r=0.954 between the Adaptability score and the raw count of causal links
  in the same answer, the single highest correlation found anywhere in this
  audit, evidence-level or dimension-level.

## Part 3 — Unique evidence analysis

For each dimension, what evidence increases *only* it, per the formula:

| Dimension | Formula-exclusive evidence | Real-world status |
|---|---|---|
| Knowledge | `metric_definitions` with `how_measured` | Rare but real (5/32, 3 with real derivations) |
| Execution | `quantities`, `tools` with `usage` | Present and real (9/32, 8/32 respectively) |
| **Problem Solving** | **None** | Every input (`incidents`, `causals`, `constraints`) is shared with Knowledge, Judgment, or Adaptability |
| **Judgment** | **None** | Every input (`decisions`, `constraints`, `causals`) is shared with Ownership, Problem Solving, or Adaptability |
| Ownership | `boundaries`, `entities` (team/role kind) | `boundaries` measured at **0/32**; `entities` present but weakly weighted (0.3) and itself frequently inflated (`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`'s over-segmentation finding) |
| **Adaptability** | **None** | Every input (`causals`, `concepts`, `decisions`) is shared with Knowledge, Problem Solving, Judgment, or Ownership |

**Three of six dimensions — Problem Solving, Judgment, and Adaptability —
own no exclusive evidence type at all, by construction, not by extraction
accident.** No amount of fixing extraction fidelity for `decisions` or
`constraints` changes this, because even a perfectly-extracted `decisions`
signal is *itself* shared across Judgment, Ownership, and Adaptability in
the formula (Part 1). The other three dimensions each have at least one
formula-exclusive input, but two of those three exclusives are themselves
rare (`metric_definitions`-defined) or currently zero (`boundaries`) in real
data — leaving Execution as the only dimension with both a real formula-level
exclusive *and* real-world usage of it.

## Part 4 — Redundancy analysis

The empirical picture resolves cleanly into three groups, not six:

1. **Knowledge + Execution** — r = 0.85–0.97 across every grain tested,
   mechanically driven by shared `process_steps`.
2. **Problem Solving + Judgment + Adaptability** — r = 0.78–0.95 across
   every grain tested, mechanically driven by shared `causal_links`, and
   two of the three pairs become mathematically undefined the instant that
   one shared signal is removed.
3. **Ownership** — the one dimension that behaves statistically distinct
   from everything else (r = 0.05–0.68, and negative against Execution once
   shared signals are stripped). This is not, on its own, evidence that
   Ownership is a *well-measured* construct — `SCORING_SEMANTICS_AUDIT.md`
   already found its practical gate reduces to "does the sentence contain
   the word I," a different and weaker kind of noise, not a more valid
   signal. It is simply evidence that whatever Ownership is measuring is
   *not the same thing* the other five are measuring.

**Important caveat, stated precisely so this finding isn't overclaimed:**
this audit measures whether the *current* extraction-and-scoring apparatus
can tell these six dimensions apart — not whether the six concepts are
inherently invalid in principle. A skilled human interviewer could
plausibly ask questions that pull Problem Solving and Judgment apart (root
cause identified vs. trade-off reasoned through) even though this system's
formula currently cannot, because `decisions` and `constraints` — the
signals that would carry that distinction — are extracted at 0/32 in real
answers (`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`) and, even when extracted,
are shared inputs in the formula rather than exclusive ones (Part 1/3
above). The finding is: **six independent dimensions are not currently
demonstrated, and the reason is structural (shared formula inputs) as well
as extractive (the would-be distinguishing signals never populate) — both
would need to change before six-way independence could be fairly
re-tested.**

---

## Recommendation

**Option C, not A or B, and not permanently.** The data do not support
reporting six independently-meaningful competence scores today — Knowledge
and Execution are one statistical factor, Problem Solving/Judgment/
Adaptability are a second, and Ownership is a third, weak, and separately
noisy signal. Collapsing outright to a fixed smaller number (Option B)
would discard the *conceptual* distinctions the master context correctly
cares about, and would freeze in place a three-cluster structure that is
itself an artifact of which two signal types (`process_steps`,
`causal_links`) happen to be over-weighted and which four
(`decisions`/`constraints`/`boundaries`/`concept_explanations`) happen to
be unextracted right now — not necessarily the right permanent shape.

The evidence instead supports reporting what the data actually show:
a small number of genuinely-distinguishable composite scores (an
Execution/Knowledge cluster, a Reasoning cluster covering Problem
Solving/Judgment/Adaptability, and Ownership on its own) **alongside** the
underlying evidence categories already validated in
`EVIDENCE_GAP_FRAMEWORK.md`, rather than presenting six numbers whose
independence this audit's own data — at the candidate level, the answer
level, and under direct signal ablation — could not confirm. Whether the
six-dimension framework can be *earned back* depends on two prerequisite
fixes named in `SCORING_SEMANTICS_AUDIT.md` and
`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`: giving Problem Solving, Judgment,
and Adaptability at least one real, formula-exclusive signal each, and
fixing the extraction path so `decisions`, `constraints`, and `boundaries`
actually populate. Until both hold, six is not a validated number — it is
a label on what is measurably closer to two clusters and one outlier.
