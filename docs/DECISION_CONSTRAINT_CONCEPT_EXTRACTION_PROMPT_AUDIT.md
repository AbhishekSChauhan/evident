# Decision / Constraint / Concept Extraction Prompt Audit

**Question:** why does the extraction prompt systematically route decision,
constraint, and concept evidence into `process_steps` and `causal_links`
instead of their dedicated buckets — and can this be fixed at the prompt
level alone, without touching the planner or the scoring formulas?

**Answer, in one line:** the live, default extraction prompt
(`api/prompts/extract_signals.txt`) **does not mention `decisions`,
`constraints`, `concept_explanations`, or `boundaries` anywhere** — not in
its instructions, not in the JSON schema it shows the model. A second,
already-written prompt (`api/prompts/v2_extract_signals.txt`) defines all
four correctly and is schema-compatible — but it is gated behind the same
flag (`evidence_planner_v2`) that also swaps out the entire planner, so
turning it on is not a safe fix under this audit's constraint. This is not
primarily a wording-quality problem; it is a **content-omission** problem,
with one genuine, smaller wording-quality problem sitting underneath it
once the omission is fixed.

---

## 1. The exact prompt instructions

**Live prompt (`extract_signals.txt`, the one every real call in
`EXTRACTION_BUCKET_RECOVERY_AUDIT.md` actually used — confirmed:
`settings.evidence_planner_v2` defaults to `False`,
`api/config.py:105`):**

Its "WHAT TO EXTRACT" section lists exactly eight buckets plus `summary`:
`quantities`, `process_steps`, `causal_links`, `tools`,
`metric_definitions`, `incident_markers`, `entities`, `facts`. Its closing
JSON schema template repeats the same eight. **`decisions`, `constraints`,
`concept_explanations`, and `boundaries` do not appear anywhere in this
file — not as instructions, not as schema keys, not as examples.** This is
not a subtle omission to infer from behavior; it is directly visible by
reading the file.

**`v2_extract_signals.txt` (gated off by default) defines all four,
verbatim:**

> `decisions` — *"A choice they made AND why, when the answer states both
> halves. `choice` = what they picked, adopted, or DELIBERATELY RETAINED /
> OPTED NOT TO CHANGE... `reason` = why, in their words... Skip the whole
> item if the answer names a choice with no stated reason, or a reason with
> no stated choice — a decision signal needs both halves present."*
>
> `constraints` — *"A limitation that shaped the work, whatever the field:
> compliance, budget, data availability, latency, headcount, timeline.
> `limitation` = the short kind of constraint... `effect` = what it
> stopped them from doing or forced them to do instead."*
>
> `concept_explanations` — *"An explanation of a domain concept, policy,
> tool or process that explains WHY it works or WHY it applies. `concept`
> = what they explained. `reasoning` = the explanation of why/how."*

`boundaries` is also fully defined there, though out of this audit's
named scope (it was covered separately in `EXTRACTION_BUCKET_RECOVERY_AUDIT.md`
§3, where its one live success came from the heuristic fallback, not
either prompt).

**Field names match the Pydantic schema exactly** — `choice`/`reason`
(`DecisionSignal`, `api/schemas.py:225-228`), `limitation`/`effect`
(`ConstraintSignal`, `:231-234`), `concept`/`reasoning`
(`ConceptExplanation`, `:237-240`). No schema-shape mismatch exists between
what `v2_extract_signals.txt` asks for and what `AnswerSignals` accepts —
if this prompt were live, its output would validate cleanly. All four
fields also carry `Field(default_factory=list)` on `AnswerSignals`
(`:279-282`), which is *why* the live prompt's total silence on them causes
no validation error at all: their absence from the model's JSON is quietly
accepted as an empty list, every time, with no warning anywhere in the
pipeline that four of twelve buckets were never even offered.

---

## 2. Are the buckets defined clearly enough to distinguish from `process_steps`/`causal_links`?

**In the live prompt: the question doesn't apply — there is nothing to be
unclear, because the buckets don't exist.** Every example in
`EXTRACTION_BUCKET_RECOVERY_AUDIT.md` is, at the prompt level, not a
disambiguation failure but a menu-item that was never on the menu.

**In `v2_extract_signals.txt`, the definitions are mostly adequate but
leave one real residual gap on each side of the boundary:**

- **`process_steps`'s own definition is written broadly enough to
  invite decision- and constraint-shaped content in.** *"Distinct steps
  of HOW the work actually ran — a recurring check, a review they ran, **a
  thing they did before another thing**."* Nothing in this definition
  excludes a decision or a boundary statement — "I decided to launch X"
  and "I handled task assignment" both satisfy "a thing they did" exactly
  as well as "I checked the dashboard every morning" does. The four newer
  buckets get their own definitions, but `process_steps`'s definition was
  never tightened to say what it is *not*, the way, for example,
  `question.py`'s `MOVE_BRIEFS[OWNERSHIP_BOUNDARY]` already does for
  question generation elsewhere in this codebase (*"this is a
  contribution question, not an org-chart question — never ask X; 'what
  part did you build' is right, 'who reviewed your work' is wrong"*). The
  extraction prompt has no equivalent negative example anywhere.
- **`causal_links`'s definition overlaps `decisions`, `constraints`, and
  `concept_explanations` structurally, not just superficially.** A
  sentence like *"we used synthetic data because production labels were
  sparse"* — `v2_extract_signals.txt`'s own worked example for
  `decisions` — is *also* a textbook cause → action shape (cause: sparse
  labels; action: used synthetic data). Nothing in either bucket's
  definition tells the model whether to populate one, the other, or both.
  The same is true for `constraints` (a limitation that "forced" an
  action is causally shaped by construction) and for
  `concept_explanations` (a generalizable mechanism explained via "X
  typically causes Y" reads identically to a causal link unless the model
  is told the distinguishing feature is *generality*, not instance-specific
  cause-and-effect — and it is never told this).
- **`decisions`'s "both halves required" rule is, on inspection, the one
  place the definitions actively help rather than hurt** — see §3, where
  it turns out to correctly re-route a meaningful share of what looked like
  "missing decision content" toward `boundaries` instead, which is where
  that content actually belongs.

**Not a factor:** schema shape (already exact match), ordering bias within
`v2_extract_signals.txt` (the four buckets sit between `entities` and
`facts` in both the instruction list and the JSON template, mirroring the
Pydantic class's own field order at `schemas.py:279-282` — not buried at
the end, not competing with a token-budget cliff), or a shortage of worked
examples for `decisions` specifically (it has two clean ones). Worked
examples for `constraints` and `concept_explanations` are thinner (zero
and zero, respectively, versus `decisions`'s two) — a real but secondary
gap, addressed in §5.

---

## 3. Every missed example, reclassified precisely against the real bucket definitions

Pulling the genuine misses directly from `EXTRACTION_BUCKET_RECOVERY_AUDIT.md`'s
own instrumented data (same 105 live calls, same raw pre-validation JSON
already captured — no new model calls needed for this audit). Each row
applies `v2_extract_signals.txt`'s actual definition, not a looser
"decision-adjacent" reading, which produces one **correction** to the
prior audit's own count (flagged explicitly, per this series' standing
practice of visible correction over silent revision).

### `decisions` — reclassified

| Text (what should have triggered the bucket) | Actually entered | Would it validly populate `decisions` under the REAL definition (choice + stated reason, both present)? | Why |
|---|---|:---:|---|
| *"So instead of using joins... [Apache AGE]... **since** we have lots of many-to-many relationships"* | `causal_links`, `tools` | **Yes** | Explicit choice + explicit reason ("since..."). Clean fit. |
| *"Instead of finalising the flows immediately, I used the available information to create an initial prototype"* | `process_steps`, `causal_links` | **Yes, marginally** | Choice stated; reason is contextual (avoiding the wait) rather than an explicit "because" clause — the strictest reading of the rule could still skip it. |
| *"I could independently decide which sourcing channels... decisions involving final candidate selection would require hiring manager approval"* | `process_steps` | **No — correctly** | No stated *reason* for the choice. This is an authority/scope split ("what's mine vs. what needs approval"), which is precisely `boundaries`'s definition, not `decisions`'s. |
| *"Decisions involving pricing changes, major commitments, or strategy would require management approval"* | `process_steps` | **No — correctly** | Same shape: a policy boundary, not a personal choice-plus-reason. `boundaries`, not `decisions`. |
| *"I am the final decision maker not the AI"* | `tools` | **No — correctly** | An authority statement with no stated reason. `boundaries`. |
| *"I could independently handle the print design... Approval was generally required for final designs..."* | `process_steps` | **No — correctly** | Same authority-boundary shape. `boundaries`. |
| *"I was comfortable making decisions independently when they were related to code quality... I could suggest better error handling..."* | `process_steps`, `tools`, `entities` | **No — correctly** | Same shape. `boundaries`. |
| *"I independently handled angular level optimizations... backend production required approval"* | `process_steps`, `tools`, `entities` | **No — correctly** | Same shape. `boundaries`. |
| *"Like I can directly set up the schemas and stores... require input from the backend side"* | `process_steps`, `entities` | **No — correctly** | Same shape. `boundaries`. |
| *"the decision leadership actually needs to make, not the model's output"* (meta-commentary on decision framing in general) | `process_steps`, `causal_links`, `incident_markers` | **Ambiguous** | Reads as generalizable reasoning about decision-making, not a first-person choice — closer to `concept_explanations` than `decisions`. Genuine category overlap, not resolved by either prompt. |
| *"independently I took the decisions like launching a referral mechanism... needed a larger budget... so t[hat...]"* | `quantities`, `causal_links`, `tools`, `entities` | **Likely yes** (truncated in the export; the visible "so..." suggests a stated reason follows) | Choice + apparent reason present. |

**Correction to `EXTRACTION_BUCKET_RECOVERY_AUDIT.md`'s own count:** that
audit reported ~11/35 (31%) "genuine decision content" for this bucket.
Applying the schema's real, strict definition precisely, **only 3 of those
11 cleanly qualify as `decisions`; the other 8 are authority/scope-boundary
content that belongs in `boundaries`, not `decisions`.** This is not an
error in the recovery audit — it correctly identified that *some*
decision-or-boundary-shaped content existed and was lost; this audit
narrows *which* bucket each instance should land in once the actual field
definitions are applied precisely rather than loosely. It also means the
`decisions` bucket's true theoretical ceiling is materially lower than
`boundaries`'s, which absorbs most of the difference.

### `constraints` — reclassified

`constraints`'s real definition (a named limitation; `effect` optional) has
no AND-gate, so the prior audit's classification holds up well here. Every
one of the following clearly names a real limitation:

| Text | Actually entered | Valid `constraints` fit? |
|---|---|:---:|
| *"The main constraints were around payload size, rate limits... a payload limit of around 1 MB... a rate limit of approximately 100 requests per minute... under 500 ms"* | `quantities` (3) | **Yes, cleanly** |
| *"The rate limit constraint was around 100 requests per day... latency thresholds were around 30 seconds"* | `quantities` (2), `entities` | **Yes, cleanly** |
| *"The client's core constraint was that they had three years of sales data but no clear way to tell which product line to prioritize"* | `quantities` (4), `causal_links`, `entities` | **Yes, cleanly** |
| *"the EU regulations were very long like there were 69 pages of compliance which one need to follow"* | (lost entirely — retry/fallback) | **Yes, cleanly** |
| *"can easily exceed this limit"* (memory ceiling in ML libraries causing a crash) | `process_steps`, `causal_links`, `tools` (5) | **Yes, cleanly** |
| *"the sprint plans were very superficial and bandwidth estimate was all over the place"* | `process_steps`, `causal_links` | **Yes** (capacity/bandwidth constraint) |

No case in this bucket required the strict-AND-gate reasoning `decisions`
needed. The prior audit's ~40% human-observed rate is confirmed, not
revised, on closer reading.

### `concept_explanations` — reclassified

Also no AND-gate, but genuinely generalizable content is rare, confirming
the prior audit's low estimate:

| Text | Actually entered | Valid `concept_explanations` fit? |
|---|---|:---:|
| *"If one feature scores disproportionately high in importance, that's..."* (a leakage-detection heuristic, stated as a general rule) | `quantities`, `process_steps`, `causal_links`, `metric_definitions`, `incident_markers` | **Yes** — but also a genuine `causal_links` candidate; the generality ("that's [always] a sign of...") is the only distinguishing cue, and neither prompt names generality as the deciding feature |
| *"standard classification metrics... are typically not the primary evaluation tools unless..."* | (none — thin content) | **Yes, marginally** |
| *"That usually makes bottlenecks and line-balancing issues visible quickly"* | `process_steps`, `causal_links`, `metric_definitions` | **Marginal** — reads more like routine practice than an explained mechanism |

Most of the 36 non-matches in this bucket are pure single-instance incident
narratives (a specific outage, a specific bug, a specific negotiation) with
no generalization language at all — correctly absent, not lost.

---

## 4. What kind of problem is this?

Answering the brief's own checklist directly:

| Candidate cause | Verdict |
|---|---|
| **Bucket definitions** | Not the primary cause (buckets don't exist in the live prompt to be mis-defined). Secondary issue confirmed in `v2_extract_signals.txt`: `decisions`'s AND-gate is *correct* and self-disambiguating from `boundaries`; `constraints`/`concept_explanations` have no equivalent disambiguating clause against `causal_links`. |
| **Examples** | Minor gap: `constraints` and `concept_explanations` have zero worked examples in `v2_extract_signals.txt` versus `decisions`'s two. Not the primary cause. |
| **Ordering bias** | Not a factor. Position in both the instruction list and the JSON template mirrors the Pydantic schema's own field order (between `entities` and `facts`) in the one prompt that includes them at all. |
| **Schema shape** | Not a factor. Field names in `v2_extract_signals.txt` match `DecisionSignal`/`ConstraintSignal`/`ConceptExplanation` exactly; this content would validate cleanly if the model produced it. |
| **Prompt wording** | **The primary cause, in the narrowest sense of the word "wording": the live prompt's wording for these three buckets does not exist.** This is a content-completeness defect, not a phrasing-quality one. |
| **Overlapping categories** | **A real, secondary cause that survives even in `v2_extract_signals.txt`.** `causal_links` is defined broadly enough, and `process_steps` inclusively enough, that decision-, constraint-, and concept-shaped sentences satisfy their definitions too, with no cross-reference either way telling the model which bucket wins or whether both can be populated at once. |

**Direct answer: this is not a subtle prompt-design failure. It is the
plainest possible version of "model failed to extract" — the extraction
prompt actually running in production never asked for this content.** A
second, correctly-defined prompt already exists on disk, unused. Under
that second prompt, one further, smaller, genuine wording problem remains
(category overlap with `causal_links`/`process_steps`), which is worth
fixing at the same time but is not the reason the buckets are at zero
today.

---

## 5. Can this be fixed at the prompt level alone, without touching the planner or scoring?

**Yes — but not by the obvious route.** `evidence.py`'s prompt selection
and the planner's move-selection logic share **the same flag**:

```
api/engine/evidence.py:449   "v2_extract_signals" if settings.evidence_planner_v2 else "extract_signals"
api/engine/orchestrator.py:1224   ... and not settings.evidence_planner_v2   (gates _thread_plan)
api/engine/orchestrator.py:1227-1229   plan_next_evidence(...) if settings.evidence_planner_v2 else plan_next_forensic(...)
```

**Turning `evidence_planner_v2` on would fix the extraction prompt and
simultaneously replace the entire planner** — swapping the Move-ladder
system (`plan_next_forensic`, the subject of every prior audit in this
series) for the EvidenceCategory planner (`plan_next_evidence`), and
disabling `_thread_plan` entirely. That is exactly the kind of planner
change this audit's brief asks to avoid, and it would also invalidate every
planner-side finding in `COVERAGE_REACHABILITY_AUDIT.md`,
`DIMENSION_OPENING_AUDIT.md`, `MOVE_EVIDENCE_YIELD_AUDIT.md`,
`PLANNER_STRATEGY_AUDIT.md`, and `THREAD_MECHANISM_AUDIT.md` in one step,
since none of them would still describe the running system.

**The fix that satisfies the brief's actual constraint:** the four bucket
definitions already exist, verbatim, correctly schema-matched, in
`v2_extract_signals.txt`. They can be copied directly into
`extract_signals.txt` — the prompt `score_response()` uses whenever
`evidence_planner_v2` stays `False` — with no change to
`api/engine/orchestrator.py`, `api/engine/signals.py`, or
`api/engine/scoring.py` at all. This is verifiably a prompt-only change,
for three independent reasons already established in this and the prior
audit: (1) `AnswerSignals` already declares all four fields with
`default_factory=list`, so no schema migration is needed; (2)
`signals.py`'s six `score_<dimension>()` functions already read
`sig.decisions`/`sig.constraints`/`sig.concept_explanations` with live,
nonzero weights (`EXTRACTION_BUCKET_RECOVERY_AUDIT.md` §5) — scoring is
already waiting for this content, unmodified; (3) the planner never reads
`AnswerSignals` fields at question-selection time — `orchestrator.py`
plans from `ledger`/`moves_used`/stored `probe_level`, never from which
extraction prompt produced a given answer's signals. Editing
`extract_signals.txt`'s text cannot, by construction, reach into either.

**Two things worth doing in the same pass, since the file is already being
touched, without expanding scope beyond wording:** add one worked example
each for `constraints` and `concept_explanations` (matching `decisions`'s
existing two), and add a short negative clause to `process_steps`'s and
`causal_links`'s own definitions naming what they are *not* — a decision
with a stated reason, a scope/authority split, or a generalized mechanism
explanation — in the same style `question.py`'s `MOVE_BRIEFS` already uses
successfully elsewhere in this codebase. This addresses §2's residual
overlap risk; it is still a wording-only change to one `.txt` file.

---

## 6. Estimated recovery if extraction alone is fixed

Refined from `EXTRACTION_BUCKET_RECOVERY_AUDIT.md`'s figures using §3's
precise reclassification (not the same numbers — corrected, with the
correction shown):

| Bucket | Prior audit's estimate | Refined estimate | Why it moved |
|---|---:|---:|---|
| `decisions` | ~28–31% | **~10–15%** | Roughly two-thirds of the originally-counted "decision content" is, under the schema's real AND-gate, authority/scope content that correctly belongs in `boundaries` instead. `decisions`'s true addressable population is narrower than it first looked — a real, correctly-behaving disambiguation once the actual bucket exists, not a loss. |
| `constraints` | ~35–40% | **~35–40%, unchanged** | No AND-gate; every reclassified example held up under the real definition. |
| `concept_explanations` | ~8–10% | **~8–10%, unchanged** | Definition is loose enough that the earlier estimate wasn't inflated by a missed disambiguation rule; the content is simply rare. |

**Net implication for `SCORING_SEMANTICS_AUDIT.md` and
`DIMENSION_VALIDITY_AUDIT.md`'s downstream findings:** `constraints`
remains the strongest, most reliably recoverable of the three (feeds both
`JUDGMENT` and `PROBLEM_SOLVING`), and is recoverable by a pure prompt-text
fix with no planner or scoring change. `decisions`'s recoverable share is
smaller than this audit series first estimated, but the content that
doesn't land there does not disappear — it correctly redistributes to
`boundaries`, which independently carries `OWNERSHIP`'s single largest,
least-coupled coefficient (`EXTRACTION_BUCKET_RECOVERY_AUDIT.md` §6). A
correct fix to this one prompt file plausibly moves real signal into
**both** `JUDGMENT` and `OWNERSHIP` simultaneously, even though only three
of the four affected buckets were named in this audit's title. This is the
cleanest, lowest-risk fix identified anywhere in this audit series: it is
one file, it does not touch the planner, it does not touch scoring, and
the scoring logic it feeds is already live and unmodified, waiting for
content it has never once received in a real interview.
