# Post-Recovery Impact Audit

**Question:** if `decisions`, `constraints`, `concept_explanations`, and
`boundaries` begin populating at the recovery rates estimated in
`DECISION_CONSTRAINT_CONCEPT_EXTRACTION_PROMPT_AUDIT.md`, which downstream
findings across the audit series are most likely to materially change, and
which are likely to remain true? This is a specification of what to
re-measure after the one-file prompt fix — not a redesign, and not a new
round of live extraction calls. Every number below is derived from the
actual formula coefficients (`api/engine/signals.py`) and the actual
measured correlations/ablations already on record in this series, not
re-estimated from scratch.

**Calibrating headline, stated before anything else because it tempers the
natural optimism of "the root cause is fixed":** the recovery is real,
correctly the highest-confidence next step, and touches exactly the right
two dimensions — but it is **bounded and uneven, not transformative**. The
estimated recovery rates in the prompt audit (`constraints` ~35–40%,
`boundaries` ~26–29%, `decisions` ~10–15%, `concept_explanations` ~8–10%)
are rates **within an already-narrow, pre-filtered pool** (roughly 15–19%
of all real turns each, since that is how large the bucket-plausible
samples were in `EXTRACTION_BUCKET_RECOVERY_AUDIT.md`). Translated to the
**whole corpus**, not just the targeted subsample, the post-fix population
rate of each bucket across *all* real answers is approximately:

| Bucket | Plausible share of all turns | Recovery rate within that share | Approx. share of ALL real answers gaining this signal |
|---|---:|---:|---:|
| `constraints` | ~19% (40/212) | ~35–40% | **~7–8%** |
| `boundaries` | ~15% (31/212) | ~26–29% | **~4%** |
| `decisions` | ~17% (35/212) | ~10–15% | **~2%** |
| `concept_explanations` | ~19% (40/212) | ~8–10% | **~1.5–2%** |

Compare this to `causal_links` and `process_steps`, which populate on a
clear majority of real answers already (`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`:
19/32 and 24/32 respectively, ~60–75%). **The fix adds real, previously-zero
signal to roughly one in twelve answers for `constraints` and one in
twenty-five for `boundaries` — a genuine, measurable, correctly-targeted
recovery, not a rebalancing of the corpus's dominant signal sources.**
Every answer below is calibrated against this arithmetic, not against the
headline recovery percentages in isolation.

---

## 1. Which `SCORING_SEMANTICS_AUDIT.md` findings would change?

| Finding | Predicted outcome | Why |
|---|---|---|
| §3 "Unprobed dimension forfeits full weight to zero, `total_weight` never renormalises" | **Unchanged** | This is a formula defect (`scoring.py:135`), not an extraction defect. The fix does not touch `claim_score()`. It will simply fire less often for JUDGMENT/OWNERSHIP specifically, on the ~4–8% of claims that now get genuine content — the mechanism itself is untouched. |
| §4 "JUDGMENT's gate has exactly one live route (a complete causal link)" | **Materially changes** | `constraints` (0.5, feeds `gate_open`) and `decisions` become second and third live routes. This is the single most directly falsifiable prediction in this audit (see §7 for the exact re-measurement). |
| §4 "OWNERSHIP's gate reduces to 'does any sentence contain the word I'" | **Partially changes, likely does not stop being true** | The first-person-verb backdoor (`_is_first_person_action`) fires on almost any first-person sentence — near-unconditional in an interview transcript. `boundaries` recovering on ~4% of all answers gives OWNERSHIP a second, genuine route, but at that frequency the backdoor almost certainly remains the *dominant* route by sheer volume. Expect: the gate opens via a genuine boundary on a small, real, non-zero share of claims where today it opens via the backdoor alone or not at all — not a reversal of which route dominates. |
| §6 Sensitivity ablation ("`process_steps`/`causal_links` account for nearly all measurable movement; the other ten types are near-inert, five completely inert because they never populate") | **The "five completely inert" sub-claim changes for four of the five; the headline ranking does not** | `decisions`, `constraints`, `concept_explanations`, `boundaries` move from a hard 0.00 average swing to a small but real nonzero swing (expect single digits, well below `process_steps`'s 16.38 or `causal_links`'s 11.06, given the ~2–8% population rates above). `facts` remains genuinely inert for scoring — untouched by this fix (§5 below). |
| §7 Philosophy table: "`gate_open` via lexical pattern presence, no grounding check" | **Unchanged** | This fix adds *content* to the gate's inputs; it does nothing to verify that content is plausible or connected to the claim beyond the existing verbatim check. A fabricated-but-well-formed constraint or decision opens the gate exactly as easily post-fix as a genuine one does. This finding survives completely intact and is *not* addressed by the recovery. |
| §8 Top-10 risk #4 ("a single `causal_link` moves four of six dimensions") | **Unchanged as a mechanism; slightly less dominant in relative terms** | Still true by formula construction. Its *practical* dominance shrinks marginally as other routes start contributing on a small share of claims, but the underlying coupling is untouched — this requires a scoring-formula change, not an extraction fix. |
| §8 Top-10 risks #1, #6, #7, #8, #10 (total-weight forfeiture, recruiter-weight no-op, presence-not-magnitude bonus, duplicate bonus code paths, incomplete-causal asymmetry) | **All unchanged** | None of these are extraction-caused; none are touched by a prompt-only fix. |

---

## 2. Which `DIMENSION_VALIDITY_AUDIT.md` findings would change?

| Finding | Predicted outcome | Why |
|---|---|---|
| Part 1: "Problem Solving, Judgment, and Adaptability own no exclusive evidence type at all, **by construction**" | **Unchanged** | This is a fact about the *formula* — `constraints` is still shared between JUDGMENT and PROBLEM_SOLVING; `decisions` is still shared between JUDGMENT, OWNERSHIP, and ADAPTABILITY. Fixing extraction populates these buckets; it does not make any of them exclusive to one dimension. **This is the single most important "does not change" finding in this whole audit**, because it means the ceiling on six-way independence is not raised by this fix at all — only the *frequency* with which the existing, still-shared inputs fire changes. |
| Part 2(a)/(b): candidate-level and answer-level correlation matrix | **Judgment↔Adaptability likely softens somewhat; Judgment↔Problem Solving likely does not** | See §6 below for the mechanism — `constraints` is shared between exactly Judgment and Problem Solving, so recovering it does not pull them apart and may very slightly reinforce their co-movement. `decisions` is the one input that could differentiate Judgment from Problem Solving (Problem Solving never reads `decisions`), but it is also the rarest recovered bucket (~2% of all answers) — expect a real but small directional shift, not a change in which pairs are "highly correlated" versus "independent." |
| Part 2(c): the causal-ablation collapse ("removing `causal_links` makes Judgment's and Adaptability's scores mathematically constant") | **The literal result changes; the substance likely survives** | With `constraints` now populating on ~7–8% of all answers, JUDGMENT would no longer be a hard mathematical constant when `causal_links` is zeroed out — a small amount of real variance exists. But `constraints` doesn't feed ADAPTABILITY at all (confirmed in `score_adaptability()`: only `causal_links`, `concept_explanations`, `decisions`), and ADAPTABILITY's two "new" inputs are the two *rarest* recovered buckets (~2% and ~1.5–2% of all answers respectively). **Predicted: re-running this exact ablation post-fix will show JUDGMENT gain a small, real, non-degenerate variance, while ADAPTABILITY remains close to — though probably not literally — constant.** This is the sharpest, most falsifiable single prediction in this document (see §7). |
| Part 3: "Unique evidence" table — Problem Solving/Judgment/Adaptability have **no formula-exclusive evidence type** | **Unchanged** | Same structural reason as Part 1 above — this fix changes real-world population rates, not the formula's exclusivity map. |
| Part 4: three-cluster structure (Knowledge+Execution / Problem Solving+Judgment+Adaptability / Ownership alone) | **Most likely survives as the headline description, with Judgment showing the clearest early signs of partial separation** | Knowledge↔Execution's coupling runs through `process_steps`, entirely untouched by this fix. The Reasoning cluster likely stays recognizable as one cluster — not because nothing changed, but because the magnitude of new independent variance (§ headline table) is small relative to the existing `causal_links`-driven coupling (r=0.78–0.95). Expect the *measured* r-values to move down modestly for pairs involving JUDGMENT specifically, without crossing into "clearly independent" territory. |
| Recommendation (Option C — report composite clusters, not six independent scores) | **Likely still the correct interim call** | Genuine six-way independence requires each dimension to have its own exclusive, non-shared signal — this fix does not create that (Part 1, unchanged). The recommendation should not be revisited until *after* the re-measurement in §7 confirms how much the Judgment-side correlations actually moved. |

---

## 3. Which `COVERAGE_REACHABILITY_AUDIT.md` findings remain unchanged?

This is the most important section to get right, because it is where an
optimistic reading of the prompt fix could overclaim. Coverage in that
audit is governed by three independent gates — **archetype eligibility,
seniority gating, and budget scheduling** — none of which this fix touches
at all, because it changes what the extraction *model* returns, not which
*questions* the planner asks.

- **"OWNERSHIP is unreachable via its intended openers on 79% of claims,
  decided by archetype classification before any question is planned"
  (§4) — completely unchanged.** Recovering `boundaries` extraction only
  matters on claims where `OWNERSHIP_BOUNDARY`, `AUTHORITY`, or `PEOPLE`
  was actually asked — the ~21% of claims whose archetype (`OWNERSHIP` or
  `VOLUME`) makes those moves eligible at all. On the other 79% of claims,
  there is no boundary-shaped *question* being asked, so there is no
  boundary-shaped *answer* to extract from, regardless of how good
  extraction becomes. **This fix cannot manufacture eligibility the
  planner never offers.**
- **Seniority gating of `AUTHORITY`/`EXCLUSION`/`PERTURB` (§2, §7) —
  completely unchanged.** Unrelated to extraction.
- **"Budget exhaustion despite eligibility" (13 instances, §2) —
  completely unchanged.** A scheduling fact, unrelated to extraction.
- **KNOWLEDGE's structural reachability (7.7%, driven by `METRIC_DEFINITION`'s
  7%-of-claims archetype gate and `COHERENCE`'s 0%-selected precondition) —
  almost entirely unchanged**, with one small, real exception:
  `concept_explanations` does feed KNOWLEDGE (weight 1.0), so a small
  number of claims (~1.5–2% of all answers, per the headline table) may
  now genuinely earn KNOWLEDGE credit through this route where none
  existed before. This does not change *which questions get asked*, only
  what a small number of already-asked answers can now correctly earn
  credit for.
- **The corpus-level headline — "only 2/39 candidates structurally reach
  all six dimensions; median reaches 3/6" — unchanged.** This number is
  dominated by move-eligibility and seniority gates, not by extraction
  quality; nothing in this fix changes which moves get scheduled.

**One coverage-adjacent number that *does* move, worth naming precisely
even though it is not from `COVERAGE_REACHABILITY_AUDIT.md`'s own headline
metric:** the *composition* of the `score > 0` backdoor changes.
Currently 23.1% of (candidate × dimension) pairs are credited "probed"
purely by incidental nonzero scoring with no targeting move ever asked
(`COVERAGE_REACHABILITY_AUDIT.md` §5). Post-fix, a larger share of those
same credits will be backed by a *genuine* `constraints`/`boundaries`/
`decisions` item rather than pure incidental noise (a stray causal link, a
first-person verb) — the backdoor's existence and its 23.1%-of-pairs
frequency are unchanged by this fix, but what it's actually crediting
becomes more legitimate on the margin. This is a real, positive,
measurable side effect — but it is a change in **quality of what the
backdoor credits**, not in **whether the backdoor exists or how often it
fires**, and it should not be reported as "the coverage gap closed."

---

## 4. Would the six-dimension collapse still hold?

**Most likely yes, as the overall headline — three recognizable clusters,
not six independent dimensions — with Judgment showing the most visible,
but probably still insufficient, movement toward independence.** The
formula-level reason six-way independence fails (Part 1 of
`DIMENSION_VALIDITY_AUDIT.md`: three dimensions share every one of their
inputs with at least one other dimension, by construction) is untouched by
a prompt-only fix. What changes is the *frequency* with which the existing
shared inputs fire, and that frequency increase is modest (§ headline
table: 2–8% of all answers, not a majority). The single sharpest test of
this prediction is the causal-ablation re-run specified in §7 — if
`JUDGMENT`'s ablated variance is still effectively zero (not literally
`nan`, but close to it in practice) after the fix, the collapse finding
should be reported as substantively unchanged, with the "hard mathematical
constant" framing softened to "still near-total dependence."

## 5. Would Ownership remain isolated?

**Very likely yes — and the fix may make the isolation more legitimate
rather than eliminating it.** Ownership is already the one dimension
statistically distinct from the other five (r = 0.05–0.68 candidate-level,
per `DIMENSION_VALIDITY_AUDIT.md` Part 2), but that distinctness currently
runs substantially through a noisy backdoor (`_is_first_person_action`)
rather than a genuine signal. Recovering real `boundaries` content on
~4% of all answers replaces some of that noise with a qualitatively
different kind of statement — an organizational/scope claim, not a
procedural or causal narrative — which is a poor match for what drives the
Knowledge+Execution and Reasoning clusters. **Prediction: Ownership's
correlation with the other five dimensions does not move sharply in either
direction, but the *reason* it is isolated shifts from "driven by
near-universal lexical noise" toward "driven by a rarer, more genuine
signal" — worth re-measuring specifically because the current isolation
finding, read uncharitably, could be mistaken for evidence that Ownership
is already well-measured. It is currently isolated because its practical
gate is nearly unconditional noise, which is a different, weaker claim
than "isolated because it captures something real." Post-fix is the first
point at which that distinction becomes testable.**

## 6. Would Judgment still collapse into Problem Solving?

**Most likely yes, essentially unchanged — this is the single least
intuitive, most important prediction in this document, and it runs
against the natural optimism of "we just gave Judgment two new inputs."**
`constraints` feeds **both** `score_judgment()` (0.5) and
`score_problem_solving()` (0.5) — identically. A claim that gains a
`constraints` item post-fix gains it in *both* dimensions' formulas
simultaneously, which does not pull Judgment and Problem Solving apart; if
anything, it is a new *shared* driver that could very slightly reinforce
their co-movement on the subset of claims where it fires. The one signal
that could differentiate them — `decisions`, which `score_problem_solving()`
never reads at all — is also the *rarest* of the three fixed buckets in
absolute terms (~2% of all answers, per the headline table, and further
narrowed by `DECISION_CONSTRAINT_CONCEPT_EXTRACTION_PROMPT_AUDIT.md`'s own
correction that most of what looks like decision content is actually
boundary content once the schema's real AND-gate is applied). **Prediction:
re-measuring Judgment↔Problem Solving's correlation post-fix will show
little to no material change from its current 0.945–0.949, because the
one lever that recovers most (`constraints`) is shared between them and
the one lever that could differentiate them (`decisions`) is too rare to
move the number much.**

## 7. Which baseline numbers should be re-measured immediately after deployment?

Ranked by how decisively each one tests a specific prediction above, all
reusing methodology already built and proven in this series — no new
audit design required, only re-execution against fresh post-deployment
data:

1. **Actual achieved population rates**, using
   `EXTRACTION_BUCKET_RECOVERY_AUDIT.md`'s exact instrumentation
   (`_raw_completion` wrapping, raw-JSON-before-Pydantic capture) against a
   fresh sample of real post-deployment answers. This is the prerequisite
   for trusting anything else here — every prediction in this document is
   conditioned on the estimated rates actually landing close to
   `constraints` ~35–40%, `boundaries` ~26–29%, `decisions` ~10–15%,
   `concept_explanations` ~8–10% *within their respective plausible
   subpopulations*.
2. **`SCORING_SEMANTICS_AUDIT.md` §6's exact per-bucket ablation** (score
   with vs. without each signal type, on real production data) — the
   direct, decisive test of whether these four buckets moved off 0.00
   average swing, and by how much relative to `process_steps`/`causal_links`.
3. **`DIMENSION_VALIDITY_AUDIT.md`'s exact three-grain correlation
   analysis**, especially Part 2(c)'s causal-ablation (`causal_links`
   zeroed out, check whether JUDGMENT's and ADAPTABILITY's scores are
   still literally constant or now show real, if small, variance). This
   is the single sharpest test of §4 and §6 above.
4. **`SCORING_SEMANTICS_AUDIT.md` §4's gate-route composition for JUDGMENT
   and OWNERSHIP specifically** — what fraction of gate-openings now come
   from a genuine `decisions`/`constraints` item versus `causal_links`
   alone (JUDGMENT), and what fraction come from a genuine `boundaries`
   item versus the first-person-verb backdoor (OWNERSHIP). This is the
   most direct test of whether "JUDGMENT's gate has exactly one live
   route" and "OWNERSHIP's gate reduces to the word I" are still true as
   stated, or merely mostly true.
5. **`COVERAGE_REACHABILITY_AUDIT.md` §5's reported-vs-structural coverage
   gap**, specifically the composition of the 23.1%-of-pairs
   "credited-by-backdoor-with-no-targeting-move" figure — expect the
   *frequency* to hold roughly steady while the *legitimacy* of what it's
   crediting improves, per §3 above. This confirms or corrects that
   specific reading.
6. **`CLAIM_TYPE_ROI_VALIDATION_AUDIT.md`'s simulated-interview pipeline**,
   re-run unchanged against the fixed extraction prompt. This is a useful
   cross-check specifically because that finding (claim type explains only
   9.6% of yield variance) is about **planner move-selection being
   type-invariant**, which this extraction fix does not touch at all —
   re-running it should reproduce a very similar 9.6% figure, and if it
   does not, that is a signal something in the re-measurement methodology
   changed, not that the planner did.
7. **A simple before/after count of OWNERSHIP's zero-rate and JUDGMENT's
   average score** on the exact same 143-claim raw inventory the ROI audit
   already extracted and tagged, using the same 2-question-budget
   simulation — the fastest, cheapest way to get a first real number on
   whether the predicted modest gains in §4–§6 materialize at the scale
   this document estimates, before committing to any further remediation
   sequencing decisions.

---

## Summary table: predicted to change vs. predicted to survive

| Will most likely **change** | Will most likely **survive unchanged** |
|---|---|
| JUDGMENT's gate having only one live route (§1, §7.4) | The `total_weight` unrenormalized-forfeiture defect (§1) |
| The "five buckets completely inert" ablation sub-claim (§1) | The formula's structural non-exclusivity (Part 1 of `DIMENSION_VALIDITY_AUDIT.md`) (§2) |
| The *legitimacy* (not frequency) of the coverage backdoor's credits (§3) | Archetype-based 79% exclusion of OWNERSHIP openers (§3) |
| OWNERSHIP gate opening via a genuine route on a small, real share of claims (§1) | Seniority gating of `AUTHORITY`/`EXCLUSION`/`PERTURB` (§3) |
| JUDGMENT↔ADAPTABILITY correlation, modestly (§2, §4) | JUDGMENT↔PROBLEM SOLVING correlation, essentially (§2, §6) |
| — | Ownership's isolation as an outcome, though not its cause (§5) |
| — | Gate-opening via lexical pattern with no grounding check (§1) |
| — | The overall three-cluster (not six-independent) picture (§2, §4) |

The one-line summary for whoever reads this before deciding what to do
next: **this is still the correct highest-confidence, lowest-risk fix to
make first — but it should be sold internally as "closes a real, specific,
provable extraction gap," not as "fixes Judgment" or "fixes Ownership."**
Both dimensions get *some* genuine, previously-impossible signal; neither
becomes independently well-measured as a result of this fix alone, and
§7's re-measurements are what will show exactly how much ground was
actually gained versus predicted here.
