# Evident Methodology Audit — Claim-to-Competence Pipeline

**Author framing:** Principal I-O Psychologist / Forensic Interview Designer / Hiring
Intelligence Researcher review, external to the engineering team.
**Question answered:** can this system reliably convert resume claims into
competence evidence, under a 6-question / 3-claim / WhatsApp-only budget?
**Optimized for:** evidence acquisition efficiency, not conversational quality —
per the brief, this review does not credit the system for reading naturally if
that naturalness trades against forensic yield.

**Method note.** This does not restate the fourteen engineering audits already
in `docs/` — `EXTRACTION_ARCHITECTURE_REVIEW.md`, `CLASSIFICATION_PHASE2_REVIEW.md`,
`FAMILY_TAXONOMY_REVIEW.md`, `CLAIM_INVENTORY.md`, `QUESTION_GENERATION_FINDINGS.md`,
`PHASE_3_VALIDATION_STUDY.md`, `studies/phase5/unsupported_premise_research.md`,
`TRANSFER_DESIGN_AUDIT.md`, `EVALUATION_ARCHITECTURE_PRINCIPLES.md`,
`PROOFSCREEN_DOMAIN_MODEL.md`, `STATE_MACHINES.md`, `DEEP_DIVE.md`,
`CURRENT_STATE.md`. Those are cited, not copied. What this document adds is a
psychometric/forensic-interview reading of facts already measured there —
validity, bluff resistance, and adverse-selection framing the engineering
audits weren't scoped to make — plus the four-part weakness format and Top-10
rankings the brief asked for.

**Per `CLAUDE.md`'s standing instruction, two findings below are named as
conflicts with `EVIDENT_MASTER_CONTEXT.md` rather than silently resolved.**
See §0.

---

## §0. Conflicts with the master context (read first)

### C1 — "Unknown ≠ Bad" is true in language, not in arithmetic

`EVIDENT_MASTER_CONTEXT.md` ("Coverage Gaps"): *"We do NOT assume weakness. We
mark: Unknown. Unknown ≠ Bad."*

`CLAUDE.md` ("Design decisions worth defending out loud"): *"Un-probed
dimensions contribute 0, with `probed_dimensions` reported... this is a
confidence score."*

These are both defended, and they disagree at the point that matters:
`scoring.claim_score()` computes a **weighted mean across all six dimensions**,
substituting literal `0` for any unprobed dimension, then that claim score
feeds `competence_score` directly. `probed_dimensions` is reported
*alongside* the number, not baked into how the number is computed. A coverage
gap is arithmetically indistinguishable from a proven-zero performance at the
one number recruiters will read fastest.

This is not hypothetical: in the one fully-logged real trace in the repo
(`docs/DEEP_DIVE.md` §3, candidate Priya Raghavan, fixture mode, `qpol_3`),
JUDGMENT was never probed in a 6-question interview. Her `competence_score`
came out to **24**, below her own `resume_score` of **28** — the exact
inversion the product's flagship claim ("competence beats resume") says
should not happen, produced with zero fabrication, zero adversarial
behavior, purely by ordinary budget attrition. A recruiter reading
`competence_score: 24` without also holding `probed_dimensions: 5/6` at equal
visual weight will read "Unknown" as "worse than the resume," which is the
specific outcome the master context rules out.

**This is named, not fixed here**, because resolving it means picking a side
between two decisions the project has already defended in writing. Options
are in the roadmap (§4), but the choice is a product call.

### C2 — Claim selection is scored by resume-writing craft, which is a presentation proxy

`EVIDENT_MASTER_CONTEXT.md`'s own diagnosis of the problem: *"Resumes are
increasingly AI-generated... Recruiters evaluate presentation quality instead
of actual competence."* CLAUDE.md rule 6: *"Never score presentation...
anywhere, ever."*

`claim_strength_bonus()` (`engine/signals.py:395-411`) is a pure
keyword/regex scan of the candidate's own resume prose — incident words
(+3.0), causal phrasing (+2.0), any number/percent (+2.0), constraint
vocabulary (+1.5), leadership verbs (+1.5) — with **no verification against
anything**, run before a single interview question is asked. It, plus
`claim_type` weight, is the *entire* mechanism deciding which 3 of a
candidate's real claims (12–17 per resume, per `CLAIM_INVENTORY.md`'s
measurement) get interviewed at all.

This is not the literal "accent/fluency/grammar" the rule names, but it is
the same category of thing under a different name: a candidate's skill at
writing resume prose in the register this scanner rewards — which is
*exactly* what an AI resume-writing tool optimizes for — determines
evidentiary opportunity before any evidence exists. The candidate whose real
strongest claim is plainly worded ("Collaborated with backend teams to fix
recurring integration bugs") loses the interview slot to a buzzword-dense
claim of unknown truth value ("Led incident response during a critical
outage, achieving 40% latency reduction within strict SLA constraints"),
regardless of which is actually true. The product's evidence-collection stage
downstream is genuinely bluff-resistant (see §5); its claim-*selection* gate,
upstream of all of it, is not — and is gameable by the precise skill the
product exists to see past.

Not fixed here; see roadmap.

---

## §1. Stage-by-stage assessment

Each stage is scored on the eight requested criteria (Strong / Moderate /
Weak, one line each) then given its highest-value weaknesses in the required
four-part format. The Claim → Evidence Gap → Evidence Target → Question →
Evidence chain is threaded through using the real Priya Raghavan trace where
it illustrates a finding concretely.

### Stage 1+2. Claim Extraction & Claim Prioritization

**These are not separate stages in the current implementation.** Both run
inside `engine/extract.py` before typing is finalized and before any
interview evidence exists (`extract.py:710-750`). `EXTRACTION_ARCHITECTURE_REVIEW.md`
labels the missing separation "Planning" and records it as still open (P1).
This fusion is itself the first-order finding: recall (what's on the resume)
and ranking (what's worth interviewing) are the same keyword pass, so a
claim's fate — asked or discarded — is sealed by two regex scanners
(`claim_type` keyword weight + `claim_strength_bonus`) before the system has
any evidence-quality information to rank on.

| Criterion | Rating | Basis |
|---|---|---|
| Information yield | Weak | Top-3 cut from a 12–17-claim pool (`CLAIM_INVENTORY.md:89-97`) discards most of a rich resume before interview |
| Bluff resistance | Weak | Selection scores the candidate's own prose, unverified — see C2 |
| Evidence quality | Moderate | Typed-against-taxonomy claims are structurally sound *if* the type lands correctly |
| Signal-to-noise | Moderate | One-claim-per-type cap forces diversity but discards duplicate strong evidence of one type |
| False positive risk | Low-moderate | `fallback_claim_type()` inflates ambiguous claims into the heaviest type (up to 95% collapse pre-fix, `CLASSIFICATION_PHASE2_REVIEW.md:8-23`), overstating that dimension's apparent claim density |
| False negative risk | High | Plainly-worded true achievements without incident/causal/quantity/ownership vocabulary score a 0 bonus and lose the interview slot outright |
| Gaming resistance | Weak | Directly gameable by resume vocabulary; see C2 |
| Recruiter usefulness | Moderate | What gets shown is real and typed, but the recruiter never sees what got silently dropped at extraction |

**Weakness E1 — claim prioritization rewards vocabulary, not verifiability.**
- *Why it matters:* the single gate deciding what gets interviewed runs before any bluff-resistance mechanism exists.
- *Example failure:* two candidates, one true-but-plain claim, one fabricated-but-buzzword-dense claim; the fabricated one scores +9.5 bonus over +0 and is the one selected for the 3-claim interview slate.
- *Recommended fix:* split "claim salience" (interview scheduling order) from "claim eligibility" (which claims are even candidates for the 3 slots) — guarantee at least one claim per type-category regardless of bonus score, or select the interview slate randomly among claims above a low verifiability floor rather than by keyword-maximizing rank.
- *Expected impact:* removes the single clearest gaming surface in the pipeline; directly targets the AI-resume threat the product's own vision names as the reason it exists.

**Weakness E2 — one-claim-per-type cap discards a candidate's second-strongest evidence of their actual specialty.**
- *Why it matters:* a specialist (e.g., two strong, distinct `system_ownership` claims) is capped to one, in favor of a weaker claim of a different type picked purely for type diversity; this also removes the one condition (two related claims from one candidate) that `consistency.py` and TRANSFER's own-skeleton substitution need to cross-check.
- *Example failure:* backend engineer with two verifiable ownership claims and one weak process claim gets 1 ownership + 1 weak-process interviewed; the second ownership claim, and the cross-check it would have enabled, never happens.
- *Recommended fix:* use type-diversity as a tiebreaker only when scores are close, not a hard exclusion; when a claim type dominates a resume, deliberately keep 2 of that type specifically to enable TRANSFER's own-skeleton substitution (`TRANSFER_DESIGN_AUDIT.md` §1's stated preferred design already needs two same-candidate claims).
- *Expected impact:* increases the frequency the strongest anti-fabrication probe (TRANSFER) actually has usable material, which today depends on incidental type diversity.

**Weakness E3 — `fallback_claim_type()` defaults to the *heaviest*-weighted type on zero keyword hits, not a neutral one.**
- *Why it matters:* ambiguous, plainly-worded claims are typed into the highest-scoring bucket by construction, inflating exactly the dimension the system should be least confident about.
- *Example failure:* measured 95% collapse into `system_ownership` pre-fix, 30% residual post-fix (`CLASSIFICATION_PHASE2_REVIEW.md:8-23,113-130`).
- *Recommended fix:* default to family-average weight (or an explicit `unclassified` bucket scored conservatively), not the maximum.
- *Expected impact:* removes an unearned Ownership-dimension inflation that has already been measured once and only partially corrected.

---

### Stage 3. Question Planning

This is the strongest-engineered stage in the pipeline: a fixed
`ARCHETYPE_LADDER` per claim shape, hard Python-enforced prohibitions on
duration/headcount/scale questions (`_PROHIBITED` regex,
`engine/question.py:1423-1456`) applied *regardless* of what the prompt says,
seniority gating, and a momentum→breadth→seam→depth planner
(`plan_next_forensic`, `orchestrator.py:2217-2317`) that is legibly reasoned
in its own code comments. Credit where due: the prohibition list is defense
in depth exactly where CLAUDE.md's "never score presentation" line would be
easiest to violate by accident (asking headcount reads as scoring team size,
not competence).

| Criterion | Rating | Basis |
|---|---|---|
| Information yield | Moderate | Breadth-first guarantees coverage of every claim's opening move, at the cost of depth |
| Bluff resistance | Weak | Fabrication-resistant TRANSFER/PERTURB competes for the same scarce budget as everything else rather than being guaranteed |
| Evidence quality | Strong | Move preconditions (`move_available()`) prevent asking for facts the anatomy can't support |
| Signal-to-noise | Weak | ~1 in 10 generated questions is answerable purely from the resume (§3 below) |
| False positive risk | Moderate | COHERENCE/seam logic only fires with a real cross-answer fact pair — conservative, low false-trigger |
| False negative risk | High | 6-question/3-claim budget structurally starves at least one of six dimensions in real runs (Priya: JUDGMENT, 0 probes) |
| Gaming resistance | Moderate | Strong at the question-mechanics level; undermined by whatever gate_open accepts downstream (§ Evidence Extraction) |
| Recruiter usefulness | Weak | A fully-unprobed dimension is not distinguished from a poorly-scored one at the number the recruiter sees first (see C1) |

**Weakness Q1 — breadth-first-then-depth guarantees structural coverage gaps under this budget.**
- *Why it matters:* with `MAX_QUESTIONS=6` and `MAX_CLAIMS=3` (`config.py:38-39`), breadth alone consumes 3 of 6 turns before any claim gets a second question; only 3 turns remain for seam, depth, and transfer probing *combined*, across 3 claims × 6 dimensions.
- *Example failure:* the real Priya trace — JUDGMENT dimension received zero probes across all 6 questions; `probed_dimensions=5/6`.
- *Recommended fix:* either raise the ceiling for high-signal candidates (the deprecated `MAX_QUESTIONS=12` restores this without a code change per `config.py:35-38`), or make dimension-coverage an explicit planner objective competing with claim-breadth, not a byproduct of it.
- *Expected impact:* directly reduces the frequency of the C1 conflict manifesting as a recruiter-visible score inversion.

**Weakness Q2 — no check for low-discriminative-power questions.**
- *Why it matters:* questions answerable equally well by someone who only read the resume ("How long did the X project take?") consume the same scarce budget slot as a forensic one, with zero yield difference from an impersonator's perspective.
- *Example failure:* measured at 55/519 attempts (10.6%) of the corpus, passing all seven validator rules (`QUESTION_GENERATION_FINDINGS.md:71-74`).
- *Recommended fix:* an eighth check (or a generation-time bias in `PROBE_BRIEFS`) requiring a causal or mechanism clause, not just a fact-anchored one.
- *Expected impact:* reclaims up to ~1 of 6 questions per interview from pure overhead — meaningful at this budget size.

**Weakness Q3 — CAUSAL_REASONING has no reliable elicitor.**
- *Why it matters:* `PROBLEM_SOLVING` and `JUDGMENT` gate-open on `causals` (`signals.py:502` etc.); if no question archetype reliably produces causal_links, those gates are starved independent of true candidate competence.
- *Example failure:* corpus-wide CAUSAL_REASONING lowest of all measured dimensions (34.1 mean); DECISION vs OUTCOME probe types show no reliable difference (t=−0.25, CI [−10.5, 8.1] straddles zero) — `QUESTION_GENERATION_FINDINGS.md:118-127`.
- *Recommended fix:* a dedicated causal-elicitation move ("walk me through why X led to Y," not "what did you do") rather than assuming INCIDENT/DECISION/OUTCOME produce it as a byproduct.
- *Expected impact:* targets the single weakest, most load-bearing dimension for exactly the gates that most need it.

---

### Stage 4. Question Generation (wording, LLM #2)

| Criterion | Rating | Basis |
|---|---|---|
| Information yield | Moderate | Regeneration-by-retargeting (qpol_3) fixed the measured 19% "regenerate by deleting words" defect from the retired path |
| Bluff resistance | Moderate-weak | Prompt-level anti-genericity ("two people reply" test) is real but unenforced in Python, unlike the 7 hard rules |
| Evidence quality | Unmeasured on live path | Every quality number cited anywhere in the repo is against the retired `qpol_2` corpus, not today's default `qpol_3` |
| Signal-to-noise | Moderate | Live M7h reject rate 25.5% vs corpus's 100% — "different populations," not yet characterized for the current generator |
| False positive risk | Low | Fallback path (unvalidated by design) fires ~8% of attempts; forensic fallback avoids leaking metric values (`question.py:1493-1496`) |
| False negative risk | High | `unsupported_premise` (invented tool/metric/outcome) accounts for 100% of Phase 3's reviewed false negatives and remains unimplemented |
| Gaming resistance | Weak, in one specific way | A candidate can be led into affirming a system-invented artifact the claim never established |
| Recruiter usefulness | Moderate | Naturalness ("hiring manager test") is well-designed for candidate experience, orthogonal to forensic yield per this review's brief |

**Weakness Q4 — the largest measured recall gap has a validated non-solution, not a fix.**
- *Why it matters:* `unsupported_premise` (the model asserting a tool/metric/event the claim never established, e.g. "the macros," "the transcription tool") is where all 9 reviewed false negatives in Phase 3 landed, and it remains open specifically because a rule to detect it only reaches κ=0.477 human agreement on its own existence (`studies/phase5/unsupported_premise_research.md:34-39`).
- *Example failure:* verbatim examples quoted in the study — questions presupposing a system component the candidate's claim never mentioned, which the candidate can then answer around, manufacturing false evidence for an object that was never theirs.
- *Recommended fix:* the study's own narrower path — ship containment-check-only detection for `invented_tool` (highest-frequency subtype at 8.0%, most entailment-testable), gated on a second human reviewer validating the entailment boundary; leave the other five subtypes unencoded, as the study recommends (`:492-497`).
- *Expected impact:* closes the majority of the known validity gap without absorbing the low-agreement six-way taxonomy.

**Weakness Q5 — validator precision on 4 of 7 rules is not established, only assumed.**
- *Why it matters:* `duplicate_content` (38.5%), `no_claim_anchor` (28.6%), `multiple_fact_targets` (0%), `scope_drift` (0%) precision against a single human reviewer, on samples of n=13, n=7, n=3, n=2 (`PHASE_3_VALIDATION_STUDY.md:792-796`) — too small to trust, and no second reviewer exists to compute agreement.
- *Example failure:* roughly half of what the validator blocks, a human would have sent (`:788-789`) — meaning false rejections are burning the single regeneration attempt available before fallback.
- *Recommended fix:* run the sealed second-reviewer sample the team has already prepared and flagged as ready ("15 minutes," `PHASE_3_VALIDATION_STUDY.md:824,836-838`) before trusting any of these four numbers.
- *Expected impact:* converts provisional precision numbers into trustworthy ones in either direction — currently unknown which way they're wrong.

**Weakness Q6 — the stronger prompt variant is the one that's off by default.**
- *Why it matters:* `v2_forensic_question.txt`'s "ANCHORING IS MANDATORY" instruction (forcing the question to name a specific entity from the established facts) is materially stronger anti-genericity language than the live default `forensic_question.txt`, but `v2` is gated off (`EVIDENCE_PLANNER_V2`, off by default, `config.py:98-100`) and never measured against the live generator.
- *Example failure:* none observed directly — this is a latent risk: whichever prompt ships is unvalidated either way (v2 untested at all; default lacks the stronger instruction).
- *Recommended fix:* port the mandatory-anchoring instruction into the live default prompt and run a matched-pair comparison before keeping both variants in the repo.
- *Expected impact:* low-cost improvement to anchoring compliance, and removes an unvalidated code path risk under demo pressure.

---

### Stage 5+6. Evidence Collection & Evidence Extraction

This is where the product's central bluff-resistance claim lives or dies, and
it is the most consequential finding in this review.

| Criterion | Rating | Basis |
|---|---|---|
| Information yield | Moderate | Real trace shows 0–9 signals per answer; a single fluent paragraph can populate most of the 12 signal buckets at once |
| Bluff resistance | **Weak at the layer that matters most** | `gate_open` is satisfiable by generic first-person verb matching with zero grounding check — see EC1 |
| Evidence quality | Strong on the narrow claim it makes | `enforce_verbatim()` guarantees "these words were said" reliably; it does not and was never designed to guarantee "this happened" |
| Signal-to-noise | Moderate | Sliding-window causal-chain scan (sizes 4,3,2) captures multi-sentence evidence well when it exists |
| False positive risk | Moderate | Non-numeric consistency check is exact-string-equality — "call center" vs "contact center" reads as a contradiction |
| False negative risk | Moderate-high | AUTHENTICITY/incident-marker heuristics anchor on service-industry time language; other domains' genuine incidents may not match |
| Gaming resistance | **Weak** | A candidate with 2-3 memorized generic incident-response narratives can open 3 of 6 gates on any claim, true or fabricated |
| Recruiter usefulness | Moderate | Verbatim quotes are real and traceable; which 4 quotes survive per dimension is a non-deterministic positional artifact, not a curated selection |

**Weakness EC1 — gate_open is a lexical pattern match, not a grounding check. This is the review's top finding.**
- *Why it matters:* `_is_first_person_action()` (`signals.py:281-283`) opens the OWNERSHIP gate on any sentence containing one of ~25 generic verbs (*isolated, handled, led, fixed, resolved, deployed*...) or simply starting with/containing "i ". A single sentence — *"I isolated the root cause and rolled it back"* — simultaneously: opens OWNERSHIP (first-person action verb), contributes to EXECUTION's 1.5× troubleshooting weight (`_is_troubleshooting_step()` keyword match on "isolated"/"rollback"/"root cause"), and can register as a complete causal chain opening PROBLEM_SOLVING and JUDGMENT. `enforce_verbatim()` confirms the words were spoken; nothing confirms the underlying event occurred, correlates with the specific claim, or couldn't have been produced by memorizing a generic incident-response STAR story — a widely available, work-independent interview-prep tactic.
- *Example failure case:* a candidate who has never touched the specific system in their resume claim, but has rehearsed 2–3 generic "I found the problem, I fixed it, I owned the outcome" narratives, can open the majority of the competence framework's gates on a fabricated claim, indistinguishably from a candidate who actually did the work — as long as the sentence structure matches the verb list.
- *Recommended fix:* require gate-opening evidence for OWNERSHIP/PROBLEM_SOLVING/JUDGMENT to *also* include a specific named entity, tool, or system unique to that claim (the anchoring test already written for question generation, applied retroactively to answer-side grounding) — or make survival of a TRANSFER probe on that specific claim a *required* input to the gate, not an independent, budget-competing dimension probe.
- *Expected impact:* this is the single highest-leverage fix available. It converts the product's flagship anti-fabrication claim from aspirational (present in the TRANSFER probe's design intent) to load-bearing (present in the arithmetic that actually opens scoring gates). Nothing else in this pipeline currently defends against a fluent, well-rehearsed fabricator.

**Weakness EC2 — memory-exhaustion is a cost-free evasion, and is recorded identically to "never reached."**
- *Why it matters:* `is_memory_exhausted_or_skip()` steering advances the planner to the next claim/move with 0 signals and **no penalty, no repair turn** — which is also exactly what happens when a dimension simply never gets probed due to budget. A rational candidate who cannot defend a specific claim has no incentive to attempt an answer that risks a scoreable weak signal or a later contradiction; "I don't recall the specifics" is a strictly dominant evasion, and the system cannot currently tell the difference between someone who evaded and someone who was never asked.
- *Example failure case:* Phase 3's own finding that the repair turn fired **zero times in 68 real interviews** because `is_non_answer()` only matches a canned phrase or <12 characters, while a real evasive answer like *"I don't remember the details, it was a while ago"* reads as a genuine attempt (`PHASE_3_VALIDATION_STUDY.md:552-560,753-765`) — the team's own report notes a persona coached to say "ok" would be "fitting the data to the test," meaning this has never been tested against realistic evasion at all.
- *Recommended fix:* track memory-exhaustion as a distinct third state (not "0 signals, not probed" but "declined, probed") that is surfaced separately to the recruiter and, when it clusters on one claim across multiple dimensions, triggers a low-cost specificity fallback question before the claim is abandoned.
- *Expected impact:* restores the explainability commitment (a 0 should trace to something the candidate said or didn't) and removes a documented, zero-cost gaming strategy.

**Weakness EC3 — consistency checking is real but narrow: 3 numeric keys, exact-string non-numeric comparison.**
- *Why it matters:* `stable` fact-key contradiction detection only covers `team_size`, `direct_reports`, `tenure_months` (`consistency.py:11-24`); a fabricator who never restates one of these three numbers inconsistently is invisible to the one cross-answer verification mechanism that runs by default. Non-numeric comparison is bare string inequality with no synonym tolerance, so a benign paraphrase ("call center" vs "contact center") reads as a false-positive contradiction.
- *Example failure case:* an internally-consistent fabricator sails through the entire session-level consistency multiplier untouched, since nothing they said moved on any of the three tracked numeric keys.
- *Recommended fix:* extend `fact_is_stable()` coverage where the taxonomy supports it, and add a lightweight canonicalization step (or an explicit synonym list, following the same "neutralize, don't special-case" principle the team already applies to prompts) before non-numeric equality comparison.
- *Expected impact:* modestly widens fabrication-catching surface without touching the deliberately conservative floor-at-20 penalty design.

---

### Stage 7. Competence Scoring

| Criterion | Rating | Basis |
|---|---|---|
| Information yield | Moderate | Weighted-mean claim_score with operational-evidence multipliers is a sound aggregation *if* its inputs (weights) are actually applied |
| Bluff resistance | N/A at this layer | Scoring only aggregates what extraction already decided; it cannot recover ground truth lost upstream |
| Evidence quality | Strong on paper | Six fixed dimensions, gates, and an explicit consistency multiplier — clean, auditable formula |
| Signal-to-noise | Weak | Un-probed dimensions dilute claim_score at full weight (C1) |
| False positive risk | Moderate | Operational-evidence bonus (+0.10/+0.10/+0.05) can be earned by the same generic-verb fabrication described in EC1 |
| False negative risk | High | Legitimate non-metric-owning roles (ICs, designers, junior PMs) are capped by `METRIC_OWNERSHIP`-style gates regardless of true competence |
| Gaming resistance | Weak, inherited | Same upstream issues; scoring has no independent verification layer of its own |
| **Recruiter usefulness** | **Broken in the common case** | `job_fit.py:107` raises `AttributeError` on any evaluation where a JD requirement maps to an unprobed dimension |

**Weakness S1 — role-weighted dimension scoring is a silent no-op.**
- *Why it matters:* `dimension_weights_for(job_family)` is fetched and bound to `_dim_weights` in `build_candidate_graph`, then **never read** — only `claim_weights` reach `weighted_evidence_score()` (`EVALUATION_ARCHITECTURE_PRINCIPLES.md` V1, lines 237-261). A recruiter can configure "Judgment matters 2× Knowledge for this role" through the API, see it persist, and it has zero effect on any candidate's score or ranking.
- *Example failure case:* two role profiles with opposite dimension-weight configurations produce identical rankings for the same candidate pool.
- *Recommended fix:* wire `_dim_weights` into the claim-score aggregation (or explicitly remove the configuration surface until it's wired, rather than presenting a control that lies about its effect).
- *Expected impact:* this is a config-surface integrity issue, not a subtle one — it directly contradicts "recruiter outcomes" and "explainability" and should be treated as a correctness bug, not a backlog item.

**Weakness S2 — `job_fit.py` crashes on the realistic case, not the edge case.**
- *Why it matters:* `verify_requirement_coverage()` (`job_fit.py:107`) reads `dp.gate_open`, a field that exists only as a local parameter inside `signals.py`'s scoring helpers and was **never added to the `DimensionScore` schema** (`schemas.py:292`). Any JD requirement mapping to a dimension with `probed=False` triggers `AttributeError: 'DimensionScore' object has no attribute 'gate_open'`, a live 500 on `POST /api/job-fit` and `/api/job-fit/rank`. Existing tests hard-code `probed=True` everywhere, which is why this is invisible in CI.
- *Example failure case:* the Priya trace, again — her JUDGMENT dimension is unprobed, and the sample JD asks for Judgment; job matching for exactly this candidate against exactly this JD crashes today.
- *Recommended fix:* one-line fix already specified in `docs/DEEP_DIVE.md` — `getattr(dp, "gate_open", False)` or drop the clause.
- *Expected impact:* this blocks the product's core recruiter-facing output (ranked job fit) in what is likely the *median* case given a 6-question budget across 6 dimensions, not a tail case. Highest-severity, lowest-cost fix in this entire review.

**Weakness S3 — the flagship "competence beats resume" claim inverts under ordinary, non-adversarial budget attrition.**
- *Why it matters:* in the only fully-logged real trace, `competence_score` (24) came in *below* `resume_score` (28) — with zero fabrication and zero gaming, purely because 5 of 6 questions were fallback/memory-exhausted and JUDGMENT never got probed. The product's core value proposition depends on this ordering holding in the demo and pilot conditions that will actually be run.
- *Example failure case:* exactly this trace, currently reproducible from the repo's own fixture.
- *Recommended fix:* see C1 — report a "proven competence, probed-dimensions-only" number as primary alongside a separately-labeled coverage-discounted comparability score, rather than collapsing both into one number that silently penalizes coverage gaps.
- *Expected impact:* protects the product's central demo claim from being falsified by its own short-interview budget, independent of any gaming concern.

---

## §2. Top 10 Architecture Weaknesses (system-level)

1. **Role-weighted dimension scoring is a silent no-op** (S1) — a persisted, API-exposed configuration with zero effect on any score.
2. **`job_fit.py` crashes on any JD requirement mapped to an unprobed dimension** (S2) — breaks the core recruiter output in the realistic case, one-line fix, currently live.
3. **Claim extraction and claim prioritization are fused into one keyword pass with no independent planning stage** — recall and ranking collapse before evidence exists, contradicting the team's own intended architecture (`EXTRACTION_ARCHITECTURE_REVIEW.md` P1).
4. **"Unprobed = 0" vs "Unknown ≠ Bad" — the fairness commitment is honored in language, not arithmetic** (C1) — demonstrated live in the Priya trace.
5. **All evaluations in the repo are fixture/heuristic-mode** — the real (non-heuristic) LLM scoring path has never been observed end-to-end (`DEEP_DIVE.md:216-217`), a material risk given a fixed hackathon demo date.
6. **`CLAIM_INVENTORY` (recall-first extraction) is blocked indefinitely on an unfixed `graph.py` zero-weighting bug** — the system is structurally capped at 3 interviewed claims regardless of resume richness, as a side effect of a bug in a different module.
7. **Family/taxonomy routing has self-documented irreducible keyword collisions** (Operations Manager, Business Analyst, PM/PgM) with no candidate self-report fallback for the genuinely ambiguous cases (`FAMILY_TAXONOMY_REVIEW.md:118-134`).
8. **Phone-number-keyed session routing can misattribute WhatsApp answers across two open candidacies for one person** (`PROOFSCREEN_DOMAIN_MODEL.md` F1) — a cross-candidate evidence-integrity risk, not merely a UX one.
9. **Contradictions store two raw strings with no fact or claim IDs** — a detected inconsistency cannot be traced back into the evidence graph, weakening explainability at the one place a recruiter would want to click through.
10. **Two parallel question-generation architectures and two prompt variants coexist**, and only the retired one (`qpol_2`) has ever been measured against a validation study — the shipping default's real-world behavior is asserted, not verified.

## §3. Top 10 Evidence Collection Weaknesses

1. **`gate_open` is satisfiable by generic first-person verb matching with zero grounding check** (EC1) — the review's top finding; a memorized STAR fragment opens most of the competence framework regardless of truth.
2. **Memory-exhaustion is a cost-free evasion, indistinguishable from "never asked"** (EC2) — a documented, zero-penalty dominant strategy for any claim a candidate cannot defend.
3. **TRANSFER/PERTURB — the one probe explicitly designed to catch a fluent bluffer — is optional and budget-competing, not load-bearing in the gate logic** that actually opens scoring.
4. **The repair turn has fired zero times in 68 real interviews** — its trigger condition doesn't match how real evasive answers are phrased, making it dead code in practice.
5. **Consistency checking covers only 3 numeric fact keys**, with exact-string equality (no synonym tolerance) for everything else — both false-positive (paraphrase) and false-negative (a consistent fabricator) risk.
6. **`enforce_verbatim()` guarantees "these words were said," never "this happened"** — real, valuable, and frequently mistaken (by design docs and by extension) for more than it is.
7. **AUTHENTICITY/incident-marker heuristics anchor on service-industry/BPO time language** ("at 3am," "the postmortem") — a false-negative risk for other domains' genuine incident vocabulary.
8. **Recruiter-facing quote selection ([:4] positional truncation) is non-deterministic and sensitive to unrelated ID-length changes**, not a curated "most representative" selection.
9. **`AnswerSignals` responses over the 240-char quote cap silently downgrade to heuristic scoring**, invisibly, at unmeasured frequency.
10. **`METRIC_OWNERSHIP`-style gates systematically under-credit legitimate non-metric-owning roles** (ICs, designers, junior PMs) — a false negative in the rubric, not the interview.

## §4. Top 10 Question-Generation Weaknesses

1. **No check against low-discriminative-power questions** — ~10.6% of the measured corpus is answerable equally well by someone who only read the resume, burning scarce budget on non-forensic content.
2. **`unsupported_premise` (invented tool/metric/outcome) is the largest measured recall gap and remains unimplemented**, blocked on its own detection rule reaching only κ=0.477 human agreement.
3. **Validator precision on 4 of 7 rules is unestablished** (0–38.5%, samples of n=2–13, no inter-rater κ) — roughly half of what's blocked would have been sent by a human.
4. **CAUSAL_REASONING has no reliable elicitor across any measured question archetype**, starving the PROBLEM_SOLVING/JUDGMENT gates that depend on it.
5. **Every quality number in the repo is measured against the retired `qpol_2` path** — the live default generator (`qpol_3`) has never been re-run through the validation study.
6. **Fallback questions leak the claim's own figures verbatim by design**, and fire on ~8% of measured attempts — the LLM-outage resilience mechanism is also the least forensically sound question a candidate can receive.
7. **The stronger prompt variant (mandatory-anchoring) is the one gated off by default** — the live default lacks it, and neither variant has a measured comparison.
8. **Breadth-first-then-depth planning under a 6-question/3-claim budget structurally leaves at least one dimension unprobed in real interviews** — demonstrated, not hypothetical.
9. **Anti-genericity instructions ("two people reply" test, HIRING MANAGER TEST) are prompt-level only**, unlike the seven hard Python rules — compliance is model-dependent and unmeasured.
10. **Regeneration retry-hints measurably make `duplicate_content` worse on the second attempt** on the retired path (16.5% vs 6.3%); the architectural fix (retarget to a new Move in `qpol_3`) has not been isolated and re-measured for this specific rule.

## §5. Roadmap — toward gaming-resistant, enterprise-grade

Ordered by blast radius and dependency, not calendar time. Items marked
**[product call]** require resolving a documented tension (§0) rather than an
engineering decision, and should not be made unilaterally by whoever picks up
the task.

### Now — safe, single-owner, no schema change
- Fix `job_fit.py:107` (`getattr(dp, "gate_open", False)`) — S2, highest severity, lowest cost in this review.
- Wire `_dim_weights` into `weighted_evidence_score()`, or remove the dimension-weight configuration surface until it's wired — S1.
- Port `v2_forensic_question.txt`'s mandatory-anchoring instruction into the live default prompt; measure before keeping both variants.
- Add an 8th validator check (or `PROBE_BRIEFS` bias) against pure duration/scale/timeline questions lacking a causal clause — Q2.
- Run the sealed second-reviewer sample already prepared for validator κ (~15 minutes per the team's own estimate) — Q5.

### Near-term — needs a measurement pass, still inside current architecture
- Re-run the `QUESTION_GENERATION_FINDINGS.md` / `PHASE_3_VALIDATION_STUDY.md` methodology against the live `qpol_3` generator specifically — every number currently cited is provenance-stale for what candidates experience today.
- Ship the narrow `invented_tool`-only `unsupported_premise` check (highest-frequency, most entailment-testable subtype), gated on a second human reviewer validating the boundary — Q4.
- Instrument memory-exhaustion as a distinct, recruiter-visible state, separate from "not reached" — EC2.
- Replace positional `[:4]` quote truncation with a deterministic, content-based selection rule.
- Measure how often `AnswerSignals` hits the 240-char cap and silently falls back to heuristic scoring; extend the cap if material.
- Add a canonicalization/synonym layer to non-numeric consistency comparison — EC3.
- Fix the `graph.py` zero-weighting bug blocking `CLAIM_INVENTORY` (`CLAIM_INVENTORY.md`'s own self-identified blocking dependency), enabling recall-first extraction to actually ship.

### Structural — requires explicit product sign-off, named conflicts
- **[product call]** Resolve C1: either keep "unprobed = 0, folded into competence_score" as the intentional confidence discount it was designed to be, or introduce an explicit "insufficient evidence" state that propagates as N/A rather than 0 through `claim_score`/`competence_score` arithmetic. Recommend surfacing both a probed-only "proven competence" number and a separately-labeled coverage-discounted comparability number, rather than collapsing to one.
- **[product call]** Resolve C2: decide whether claim *selection* is allowed to run on unverified resume-prose scoring, or whether it needs a bluff-resistance-aware ranking (e.g., verifiability floor, random slate selection above that floor) before the interview is scheduled.
- Make TRANSFER/PERTURB (or an equivalent own-claim-skeleton substitution check) a **required** input to opening OWNERSHIP/PROBLEM_SOLVING/JUDGMENT gates on high-stakes claims, not an independent, budget-competing probe — this is the single highest-leverage structural change available (EC1) and converts the product's own stated anti-fabrication design intent into something the scoring arithmetic actually enforces.
- Add fact/claim IDs to stored `Contradiction` rows so a detected inconsistency traces back into the evidence graph, not just two raw strings.
- Stand up inter-rater reliability (a second independent human reviewer, not a model stand-in) as a recurring measurement on validator judgments, not a one-off study — every precision/recall number in the repo currently rests on a single annotator.
