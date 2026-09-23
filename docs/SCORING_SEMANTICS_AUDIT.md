# Scoring Semantics Audit

**Question:** even if evidence collection were perfect tomorrow, does the
arithmetic in `signals.py` and `scoring.py` convert that evidence into
scores that reflect demonstrated competence — or does the math itself
reward, penalize, or distort independent of evidence quality? Traced
directly from the two files that hold every formula, cross-referenced
against the real extraction data already gathered in
`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`, and validated with a real ablation
run against the production scoring code (not a re-derivation).

---

## 1. Score flow audit — one claim, traced exactly

```
Answer text
  → AnswerSignals (12 typed buckets, LLM #3 — out of scope here, audited in
    EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md)
  → score_answer(sig, job_family)                              [signals.py:586]
      six pure functions, each independently:
        weighted = Σ (signal-type count × a fixed per-type multiplier)
        value    = 100 × min(1, weighted / TARGET[dimension])   [signals.py:116-119]
        if gate_open is False: value = min(value, GATE_CEILING) [signals.py:130-135]
  → score_claim(answers, levels, job_family, moves)             [signals.py:697]
      re-runs score_answer once over merge_signals(all answers for this
      claim) — union, not best-of [signals.py:648-694] — then sets
      entry.probed = (a targeting move was on record) OR (entry.score > 0)
      [signals.py:746]
  → claim_score(dimensions, job_family, weights, signals)       [scoring.py:119]
      content = Σ dimension_weight[d] × dimension_score[d]  ⁄  total_weight
      total_weight = Σ of ALL SIX declared weights, unconditionally
        [scoring.py:135] — not renormalised over probed dimensions
      content ×= operational_bonus (1.0 + up to 0.10 + 0.10 + 0.05)
        [scoring.py:154-184]
  → weighted_evidence_score(claims, claim_weights)              [scoring.py:205]
      role-weighted mean of claim scores, renormalised over claim TYPES
      actually present (this renormalisation exists; the dimension-level
      one above does not)
  → competence_score = weighted_evidence × consistency_multiplier
      [scoring.py:245-247]
  → badge (verified/partial/unverified thresholds)               [scoring.py:250-255]
```

Every arrow is real arithmetic on stored numbers — no step here calls a
model, confirming `scoring.py`'s own header claim. The distortions found
below are all in what the arithmetic does with the numbers it's given, not
in any hidden model call.

## 2. Evidence contribution audit — every signal type, every dimension it can move

Read directly from the six live rubric functions (`signals.py:310-578`):

| Signal type | Dimensions it can move, and at what weight |
|---|---|
| `process_steps` | EXECUTION (1.0, or **1.5 if it matches a troubleshooting keyword**, `signals.py:424-428`) · KNOWLEDGE (0.4) · OWNERSHIP (0.5, **only** if phrased first-person) |
| `causal_links` (complete) | KNOWLEDGE (0.6) · PROBLEM_SOLVING (1.0) · JUDGMENT (0.4, as a "causal tradeoff") · ADAPTABILITY (1.0) — **four of six dimensions from one signal** |
| `causal_links` (incomplete/partial) | ADAPTABILITY only (0.6) — the sole dimension that credits an incomplete chain at all |
| `decisions` | JUDGMENT (1.0 "strong" / 0.5 "weak", `signals.py:293-295`) · OWNERSHIP (0.4, first-person only) · ADAPTABILITY (0.5) |
| `constraints` | JUDGMENT (0.5) · PROBLEM_SOLVING (0.5) |
| `incident_markers` | KNOWLEDGE (0.6) · PROBLEM_SOLVING (1.0) |
| `metric_definitions` (with `how_measured`) | KNOWLEDGE (0.5) |
| `concept_explanations` | KNOWLEDGE (1.0) · ADAPTABILITY (0.5) |
| `entities` (team/person/role kind) | OWNERSHIP (0.3) |
| `tools` (with `usage`) | EXECUTION (0.5) |
| `quantities` | EXECUTION (capped at 1.0 total, `min(1.0, count×0.3)`) |
| `boundaries` | OWNERSHIP (1.0) — **the only signal type with zero cross-dimension coupling** |

**Answer to "can it affect multiple dimensions": yes, for eight of the
twelve types, and dramatically for `causal_links` and `decisions`.** A
single complete causal chain is not a Problem-Solving signal that happens
to also be logged elsewhere — it is architecturally a simultaneous input to
KNOWLEDGE, PROBLEM_SOLVING, JUDGMENT, and ADAPTABILITY. This is stated
plainly because it is the direct, quantified mechanism behind Section 5's
finding.

## 3. Unknown vs. zero audit

**Not mathematically distinguishable, at the point that matters.**
`score_claim()` does track *why* a score is zero in one field
(`DimensionScore.probed`, and `basis="not probed"` when true) — that much is
real (`signals.py:745-748`). But that field never reaches the arithmetic:

- `claim_score()`'s `total_weight` sums **all six declared dimension
  weights unconditionally** (`scoring.py:135`) — it is not renormalised
  over only the probed dimensions. An unprobed dimension's numerator
  contribution is `weight × 0 = 0`; its weight still counts in the
  denominator. The practical effect: if JUDGMENT carries, say, 20% of a
  family's dimension weight and is never probed, **20% of that claim's
  achievable score is permanently forfeited to zero**, not redistributed
  across the five dimensions that were actually measured. "Never asked,"
  "asked and produced nothing," and "asked and produced weak evidence" are
  three different real situations that all collapse to the identical
  arithmetic contribution: zero, at full declared weight.
- `probed` is reported *alongside* the score, never folded into how it's
  computed — exactly the C1 finding from `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`,
  now confirmed at the line level rather than asserted from behavior alone.

## 4. Gate audit

Six gates, read exactly from `signals.py`, cross-checked against
`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`'s real bucket-usage counts
(`decisions`, `constraints`, `concept_explanations`, `boundaries`, `facts`
all measured at **0/32** in real extractions) to state what each gate
*actually* runs on in practice, not just what it's designed to run on:

| Dimension | Opens on (OR, any one suffices) | What this means in practice today |
|---|---|---|
| KNOWLEDGE | concepts, defined metrics, complete causals, incidents, **or any process step** | Trivially open whenever `process_steps` is non-empty — which is 24 of 32 real answers |
| EXECUTION | **any** process step, regardless of content | Opens on a single generic, even mis-segmented, step |
| PROBLEM_SOLVING | incidents or complete causals | Realistically causal-link-dependent (incidents fired 2/32) |
| JUDGMENT | decisions, constraints, or complete causals | **Since decisions and constraints measured 0/32, this gate is reachable in practice by exactly one route: a complete causal link.** Not a design alternative — the only live path. |
| OWNERSHIP | boundaries, first-person steps, first-person decisions, or (team/role entity **and** any step/decision) | **Since boundaries and decisions measured 0/32, this reduces to: does any `process_steps` entry contain a first-person verb or the word "I"** (`_is_first_person_action`, `signals.py:281-283` — "i " anywhere in the text qualifies). Given these are first-person interview answers, this is close to always true whenever any step exists at all. |
| ADAPTABILITY | complete or **partial** causals, concepts, or decisions | Since concepts and decisions measured 0/32, reachable in practice by any causal link — complete or not, the only gate that credits an incomplete one |

**Can generic language open a gate?** Yes, confirmed exactly:
`_is_first_person_action()` matches on *any* sentence starting with or
containing "i " — OWNERSHIP's real-world gate is not "did the candidate
state a scope boundary," it is "did they use the word I while describing a
task," which is nearly unconditional in a first-person interview.

**Can fabricated content open a gate?** By the same mechanism, yes —
nothing in `gate_open` logic checks the causal_link's or process_step's
plausibility, specificity, or connection to the actual claim; it checks
list-non-emptiness and a lexical pattern. This is `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`'s
EC1, reconfirmed at the exact source line.

**What bypasses or closes a gate?** Nothing bypasses a closed gate except
providing the qualifying signal type. Nothing actively *closes* an open
gate once any one qualifying item exists — nowhere does the code re-check
gate conditions downward; it is monotonic (more evidence can only raise the
ceiling, never lower it), which is a defensible design choice given the
product's own "evidence accumulates, never regresses" philosophy — noted
here as neutral, not a defect.

## 5. Dimension independence audit

**Not independent.** Section 2's table is the complete answer, and the
concentration is severe: of the six live dimensions, KNOWLEDGE,
PROBLEM_SOLVING, JUDGMENT, and ADAPTABILITY all draw weight from the same
`causal_links` signal simultaneously. A single fluent causal narrative —
real or fabricated, per `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`'s finding
that this specific signal type is where the live model is most
conservative, but not immune — can move four of the six "universal
competence" dimensions the master context defines as domain-independent
and, implicitly, as separately meaningful axes. `process_steps` similarly
feeds three (KNOWLEDGE, EXECUTION, OWNERSHIP). `decisions` feeds three
(JUDGMENT, OWNERSHIP, ADAPTABILITY) — though, per Section 3's extraction
data, this coupling is currently inert since `decisions` never populates.
**`boundaries` is the only signal type with no coupling at all** — and it is
also the one signal type measured at zero usage, so this is the one place
in the whole formula where true independence exists and currently
contributes nothing.

## 6. Sensitivity audit — measured, not estimated

Real ablation run: the 32 genuine, non-empty live extractions from
`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md` were scored with the actual
production `score_answer()`/`claim_score()` functions, once as extracted
and once with each signal bucket individually zeroed out, holding
everything else fixed.

| Signal category removed | Avg claim_score point swing | Answers affected (of 32) | Largest single swing |
|---|---:|---:|---:|
| **`process_steps`** | **16.38** | 24 | 38 |
| **`causal_links`** | **11.06** | 19 | **52 — largest of any category** |
| `incident_markers` | 0.81 | 2 | 13 |
| `tools` | 0.75 | 8 | 5 |
| `metric_definitions` | 0.38 | 3 | 6 |
| `entities` | 0.38 | 6 | 2 |
| `quantities` | 0.34 | 5 | 4 |
| `decisions` | **0.00** | 0 | 0 |
| `constraints` | **0.00** | 0 | 0 |
| `concept_explanations` | **0.00** | 0 | 0 |
| `boundaries` | **0.00** | 0 | 0 |
| `facts` | **0.00** | 0 | 0 |

**`process_steps` and `causal_links` alone account for nearly all
measurable movement in this system's scores today; the other ten signal
types are collectively near-inert, and five of them are completely inert
because they never populate at all.** This is the single most important,
fully quantified finding in this audit: the entire scoring system's
real-world behavior currently reduces to two levers, and both of them are
also the two categories `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md` flagged for
quality problems — `process_steps` for over-segmentation inflation and for
absorbing decision/ownership content that belongs elsewhere, `causal_links`
for a 36% incompleteness rate. The score is maximally sensitive to exactly
the two categories whose fidelity is weakest.

## 7. Philosophy alignment audit

Against `EVIDENT_MASTER_CONTEXT.md`'s six commitments and the rules
`CLAUDE.md` derives from them:

| Rule / behavior | Alignment | Why |
|---|---|---|
| Model never scores; Python rubrics decide | **Supports** | Confirmed structurally true in both files — no model call anywhere in the scoring path. |
| Verbatim quotes required on every signal | **Supports** | Enforced upstream; scoring correctly trusts it rather than re-checking. |
| Un-probed dimension contributes literal 0 at full weight (§3) | **Conflicts** | Directly contradicts "a coverage gap is Unknown, never Bad" — the arithmetic cannot currently produce anything else. |
| `gate_open` via lexical pattern presence, no grounding check (§4) | **Conflicts** | Contradicts evidence-first hiring's own premise — a gate meant to certify "real evidence exists" opens on "the word 'I' appears," which measures nothing about whether the work happened. |
| Operational bonus computed from **presence**, not magnitude, of incident/causal/constraint signals (`scoring.py:154-162`) | **Neutral-to-conflicts** | A candidate with one weak incident marker and a candidate with five strong ones receive the identical +10% — proportionate evidence isn't proportionately rewarded once the bonus threshold is cleared. |
| Recruiter-custom dimension-weight overrides fetched but never passed into `claim_score()`'s `weights=` argument (the mechanism behind `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`'s S1) | **Conflicts** | Directly contradicts "recruiter outcomes" and "explainability" — a configuration surface that visibly persists and silently does nothing is worse than not offering it. |
| `role_coverage` kept separate from `competence_score` (`scoring.py:216-218`) | **Supports** | A genuine, correctly-implemented instance of "evidenced badly" vs. "never claimed it" being kept distinct — the one place this principle survives all the way to the arithmetic. |
| Causal links, decisions, and process steps simultaneously feeding 3-4 "independent" dimensions (§5) | **Conflicts** | The master context frames the six dimensions as a *universal competence framework* implying separable axes; the arithmetic makes several of them statistically the same measurement wearing different labels. |
| Quote truncation to `[:4]` positional, non-deterministic across runs (`signals.py:141`, previously flagged) | **Conflicts, minor** | Explainability requires a stable trace from number to quote; a positional cut sensitive to unrelated ID lengths isn't one. |
| Monotonic gates (evidence can only raise, never lower, a ceiling) | **Neutral** | A defensible product stance ("evidence accumulates"), not itself a philosophy violation. |

## 8. Top 10 scoring risks (arithmetic only)

1. **Un-probed dimensions are mathematically indistinguishable from
   proven-zero performance** — `total_weight` never renormalises, so a
   missing dimension's full declared weight is forfeited to zero rather
   than redistributed or excluded (§3).
2. **`gate_open` for OWNERSHIP, in practice, reduces to "did any sentence
   contain the word I"** — because `boundaries` and `decisions` never
   populate, the theoretically strongest gate collapses to the weakest
   possible check (§4).
3. **JUDGMENT's gate has exactly one live route** (a complete causal link) —
   not one of three designed alternatives; `decisions` and `constraints`
   are dead weight in the formula as currently fed (§4).
4. **A single causal_link can move four of six competence dimensions
   simultaneously** — the "universal competence framework" is not
   measuring six independent things for a large share of its real-world
   signal (§2, §5).
5. **Scoring is measurably dominated by two of twelve signal types**
   (`process_steps`, `causal_links`), both independently flagged for
   fidelity problems (over-segmentation, incompleteness) in the companion
   extraction audit — the score is most sensitive exactly where accuracy is
   weakest (§6).
6. **Recruiter-configured dimension-weight overrides never reach the
   formula that claims to apply them** — a live, silent no-op on a
   persisted configuration surface (§7, and `METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md` S1).
7. **The operational-evidence bonus rewards presence, not magnitude** — one
   weak incident marker and five strong ones both earn the flat +10%,
   understating genuinely richer evidence (§7).
8. **Two independent code paths compute the same operational bonus** — one
   reading structured signals directly, one regex-matching free-text
   `basis` strings (`scoring.py:163-184`) — a wording change to any rubric's
   basis text could silently break the fallback path with no structural
   test necessarily catching it.
9. **EXECUTION's gate opens on any single process step regardless of
   content or count** — combined with finding §6's over-segmentation
   sensitivity, a single enumerated resume-style list can both open the
   gate and substantially move the score.
10. **ADAPTABILITY is the only dimension crediting incomplete causal
    chains**, at 0.6× weight — meaning the 36% of real causal_links measured
    incomplete in the extraction audit contribute to ADAPTABILITY even
    while contributing nothing to KNOWLEDGE, PROBLEM_SOLVING, or JUDGMENT,
    an inconsistency in how "how much does an incomplete chain count"
    varies by dimension with no stated rationale for the asymmetry.

---

## Answer to the question asked

**No — the arithmetic is not currently aligned with "score demonstrated
evidence, not presentation quality," in two specific, measured ways.**
First, coverage gaps and proven weaknesses are computationally identical
(§3), which means the master context's fairness commitment is true only in
the reporting layer, not in the number that actually determines a badge or
a ranking. Second, and more consequential given §6's real measurement: the
system's score is not actually reading six independent competence signals —
it is reading `process_steps` and `causal_links` almost exclusively, routed
through gates that, per the real extraction data, open on generic
first-person phrasing rather than on the specific structured signals
(`decisions`, `boundaries`, `constraints`) the rubric was designed to gate
on. The formulas are internally consistent and entirely free of hidden
model calls, exactly as the architecture intends — the distortion is not
that the arithmetic is broken, but that it is faithfully computing a
six-dimension score from what is, in the data measured across two
companion audits, much closer to a two-dimension signal.
