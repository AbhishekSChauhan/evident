# Extraction Bucket Recovery Audit

**Question:** for the five near-zero extraction buckets first flagged in
`EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md` (`decisions`, `boundaries`,
`constraints`, `concept_explanations`, `facts`, all measured at **0/32** in
that audit's stratified sample) — is the underlying information actually
absent from what candidates say, or is it present and lost somewhere in the
extraction pipeline? And if planner and questioning are frozen exactly as
they are today, how much of that loss is recoverable by fixing extraction
alone?

**Answer, in one line:** for four of the five buckets, the raw information
is genuinely present in a meaningful share of real answers — but it is lost
**before the model's own JSON generation step**, not by schema rejection,
retry, or post-processing. The live model, even on attempts that parse
successfully, essentially never writes anything into `decisions`,
`constraints`, `concept_explanations`, or (via the live path specifically)
`boundaries` — confirmed directly against the **raw, pre-validation JSON**,
not inferred from the final stored record. `facts` is different: it can and
once did work correctly end-to-end in this sample, but genuinely eligible
raw material is scarce even in a sample pre-selected to contain it.

---

## 0. Method

**Same real corpus as `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`**:
`studies/evidence_export_prod/00_full_dataset.json`, 39 real (`llm_mode=live`)
candidates, 212 real questions.

**Sampling.** For each bucket, candidates were sourced two ways and combined:
(a) a keyword pre-filter over the actual bucket definition's vocabulary
(decision language, scope/boundary language, limit/threshold language,
generalization language, and the taxonomy's actual `fact_keys` labels —
`team_size`, `tenure_months`, `headcount_managed`, plus family-specific
metrics like `csat_pct`, `quota_attainment_pct`, `p95_latency_ms`); (b) the
moves whose own design brief targets that content
(`OWNERSHIP_BOUNDARY`/`AUTHORITY`/`PEOPLE`/`EXCLUSION` for `boundaries`;
`AUTHORITY`/`EXCLUSION` for `decisions`; `EXCLUSION`/`DEPENDENCY`/`AUTHORITY`
for `constraints`; `FAILURE`/`DEPENDENCY`/`AUTHORITY` for
`concept_explanations`) — a human reviewer sourcing candidates would
reasonably start in the same two places. **Two buckets could not reach 30
plausible candidates on keyword matching alone** (`boundaries`: 8;
`concept_explanations`: 9) — stated plainly rather than papered over, this
is itself informative about how rare this content's literal vocabulary is
in the real corpus (`decisions`: 20, `constraints`: 26 also needed
move-based supplementation to comfortably clear 30). Move-sourcing brought
every bucket to ≥30 (final: decisions 35, boundaries 31, constraints 40,
concept_explanations 40, facts 40 — capped at 40 for cost where the pool ran
larger).

**Instrumentation — this is the part that goes beyond the prior audit.**
105 unique real answers (the union across all five bucket pools, since one
answer can plausibly qualify for more than one bucket) were re-run through
the **actual live production pipeline** (`evidence_engine.score_response()`,
real `gpt-4o` calls, same SSL/proxy fix used throughout this audit series).
`api.llm._raw_completion` was wrapped — not replaced — to record every raw
model completion in order, still making the real network call underneath.
This captures, per answer: the **raw JSON text** the model actually
returned on attempt 1 (and attempt 2, if a retry fired), whether it passed
Pydantic validation, the fully parsed pre-verbatim signal object when it
did, and the final `ScoreResult` after verbatim enforcement and (for facts)
taxonomy/consistency filtering. This is what makes it possible to answer
the brief's exact classification question precisely rather than by
inference: **for every retry/fallback case found, the raw JSON was also
re-parsed with `json.loads` directly — bypassing Pydantic entirely — to
check whether a target-bucket item existed in the model's output even when
an unrelated field's length violation caused the whole object to fail
schema validation.** Zero hard errors across all 105 live calls.

---

## 1. Per-bucket recovery table

| Bucket | n sampled | Current extraction rate (final, stored) | Any live-model attempt ever populated it (pre-verbatim) | Human-observed presence rate | Theoretical max recovery rate |
|---|---:|---:|---:|---:|---:|
| `decisions` | 35 | **0/35 (0%)** | **0/35 (0%)** | ~11/35 (**31%**) | ~28% (most positives unambiguous) |
| `boundaries` | 31 | 1/31 (3%, via heuristic fallback only) | **0/31 (0%)** | ~9/31 (**29%**) | ~26% |
| `constraints` | 40 | **0/40 (0%)** | **0/40 (0%)** | ~16/40 (**40%**) | ~35% |
| `concept_explanations` | 40 | **0/40 (0%)** | **0/40 (0%)** | ~4/40 (**10%**) | ~8% |
| `facts` | 40 | 1/40 (3%, genuine live-model success) | 1/40 (2.5%) | ~3–5/40 (**8–12%**, most missing a stated value) | ~5% (bounded by how few answers state an actual number against a recognized fact key) |

"Human-observed presence rate" is my own close reading of every sampled
answer against each bucket's actual definition, not the keyword filter used
to source the sample (the filter over-includes on purpose, per
`EVIDENCE_GAP_FRAMEWORK.md`'s established practice of "regex sources
candidates, close reading confirms them"). "Theoretical max recovery rate"
discounts the human-observed rate for genuinely hedged or multi-interpretable
cases (e.g., a PERTURB answer that gestures at a constraint without stating
one; a mention of `cost_per_hire` as a KPI name with no value attached to
it) that a real extractor — however well-built — could not respons
ibly convert into a clean, verbatim-quotable structured item.

**The central, most load-bearing number in this table:** for `decisions`,
`constraints`, and `concept_explanations`, the "any live-model attempt ever
populated it" column is **exactly 0%** — not just the final stored record,
the **raw JSON the model generated**, checked before Pydantic validation,
before verbatim enforcement, before anything else. This rules out three of
the six possible miss categories entirely for these three buckets (see §2).

---

## 2. Root-cause breakdown

Per the brief's six categories, computed per bucket:

| Bucket | Answer genuinely lacks info | Model failed to extract | Schema rejected valid extraction | Retry path discarded extraction | Post-processing removed extraction | Stored but unused |
|---|---:|---:|---:|---:|---:|---:|
| `decisions` | 69% (24/35) | **31% (11/35) — 100% of all misses** | 0% | 0% | 0% | 0% (weight is live, see §5) |
| `boundaries` | 71% (22/31) | **26% (8/31)** | 0% | 0% | 3% (1/31 — see §4a) | 0% |
| `constraints` | 60% (24/40) | **40% (16/40) — 100% of all misses** | 0% | 0% | 0% | 0% |
| `concept_explanations` | 90% (36/40) | **10% (4/40) — 100% of all misses** | 0% | 0% | 0% | 0% |
| `facts` | ~88–92% (35–37/40) | ~5–10% (2–4/40) | 0% | 0% | 0% (0 taxonomy-key rejections observed) | **N/A structurally — see §5** |

**Zero instances of "schema rejected valid extraction" or "retry path
discarded extraction" were found for any of these five buckets, in any of
the 105 live-instrumented answers, including inside the 13 answers that
did trigger a retry and the 10 that fell back to the heuristic engine.**
This was checked directly, not assumed: every failing attempt's raw JSON
was parsed with plain `json.loads` (bypassing Pydantic) specifically to
look for a `decisions`/`boundaries`/`constraints`/`concept_explanations`
item that existed in the model's output but got thrown out along with the
rest of the object when an unrelated field (in every single retry/fallback
case observed, a `causal_links[0].quote` or `.action` field exceeding its
240/160-character limit — the same defect `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`
found) failed validation. **The search came back empty every time.** This
is a materially different, and more specific, finding than "the fallback
mechanism is losing content" — the fallback mechanism is real and costly
(§6), but for these four buckets specifically, it is not the mechanism
losing this particular content, because the content was never in the
model's output to begin with, valid or invalid.

**Concrete, verbatim examples of "model failed to extract" — content
genuinely present, redirected elsewhere:**

- *"I could independently decide which sourcing channels and approaches to
  use... decisions involving final candidate selection would require
  hiring manager approval."* — a textbook decision-plus-boundary statement.
  Attempt 1 parsed cleanly. `decisions: []`. The content: 8 items in
  `process_steps` instead.
- *"So instead of using joins... [Apache AGE] since we have lots of
  many-to-many relationships"* — an explicit technical trade-off, the
  literal shape `_is_strong_decision()` is built to credit. Retried once
  (an unrelated causal_links violation), succeeded on attempt 2.
  `decisions: []` on the successful attempt too. Redirected to
  `causal_links`/`tools`.
- *"The main constraints were around payload size, rate limits, and
  response latency... a payload limit of around 1 MB, a rate limit of
  approximately 100 requests per minute, and an expected response time of
  under 500 ms."* — the exact example `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`
  already flagged, reproduced again here on a fresh live call.
  `constraints: []`. Redirected to `quantities` (3 items).
- *"I independently handled angular level optimizations... changes
  affecting architecture, backend production required approval from the
  relevant teams."* — genuine ownership-boundary content on an
  `AUTHORITY`-move answer. `boundaries: []`, `decisions: []`. Redirected to
  `process_steps`/`tools`/`entities`.
- *"If one feature scores disproportionately high in importance, that's..."*
  — a generalizable diagnostic heuristic (leakage detection), not specific
  to this one instance. `concept_explanations: []`. Not redirected anywhere
  legible — the generalization is simply absent from the structured output,
  though the surrounding narrative is captured as `causal_links`.

**Why "answer genuinely lacks information" is still the majority category
in every bucket:** these are real, low-stakes voice/text answers to a
6-question interview, not prepared essays. Most `AUTHORITY`/`EXCLUSION`
answers in the pool are short, some are non-answers ("what do you mean,"
"All with product appfoval" [sic], a few complete non-sequiturs, two in
Hindi that were transcribed but not translatable content for this bucket).
This is a real ceiling on recovery — see §7 — and it is the majority
outcome even in a sample specifically pre-selected to be bucket-plausible.

---

## 3. `boundaries`' one success is the heuristic fallback, not the model — and it reproduces a known defect

The single populated `boundaries` result in this entire 31-item sample
(*"Sometimes a client was unavailable or delayed in responding... I handled
it by using alternate communication, clearly tracking the pending
requirement, and coordinating internally..."*) came from
`heuristic_signals()`, triggered because both live-model attempts failed
Pydantic validation on an unrelated `causal_links` field. The heuristic's
own regex-based boundary detector fired correctly on "I handled it" — but
produced the exact degenerate structure `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`
already flagged as fallback-specific: `scope_held` and `scope_handed_off`
are **the identical string**, asserting a two-sided handoff the source
text doesn't actually describe in two parts. **The only mechanism in the
current system that has ever produced a `boundaries` item on this content
is, ironically, the weaker fallback path the live model is supposed to be
protecting against** — and it produces a lower-quality version of the
signal than a correctly-working live extraction would.

## 4. `facts`' one success — and why the bucket is rare rather than broken

*"That framing told me what 'success' meant for this analysis, based on
three years of sales data... about 780 rows of invoice data"* → the live
model correctly produced `{"key": "rows_processed", "value_num": 780.0,
"unit": "rows", "quote": "about 780 rows of invoice data"}`. This survived
Pydantic validation, `enforce_verbatim()`, `is_known_fact_key()` (this
candidate's job family carries `rows_processed` as a real taxonomy key),
and `consistency.check_new_facts()` — every gate in the pipeline, correctly,
in order. **The mechanism is not broken.** What is rare is the raw material:
of the other 39 sampled answers — pre-selected via the taxonomy's own real
`fact_keys` vocabulary — only 2–4 others contain a genuinely stable,
quantifiable, taxonomy-shaped fact at all, and most of those name the
*concept* (e.g., "the KPI measured is cost per hire") without stating an
actual *value*, which `check_new_facts()` correctly drops
(`fact.value_num is None and not fact.value_text` → discarded, by design,
not a defect). This is the one bucket where the ceiling is set almost
entirely by content scarcity rather than by pipeline loss — closing that
gap further would require a follow-up question asking for the number, which
is explicitly out of scope under this audit's frozen-questioning premise.

---

## 5. Is any of this "stored but unused"?

Checked directly against the current `api/engine/signals.py` (not assumed
from the earlier `SCORING_SEMANTICS_AUDIT.md` citation — re-verified line by
line, since a recent commit history shows scoring-adjacent changes):

- `decisions` — live, nonzero weight in `score_judgment()` (1.0 strong /
  0.5 weak), `score_ownership()` (0.4, first-person only), and
  `score_adaptability()` (0.5). **Not unused.**
- `constraints` — live, nonzero weight in `score_judgment()` (0.5) and
  `score_problem_solving()` (0.5). **Not unused.**
- `boundaries` — live, nonzero weight in `score_ownership()` (1.0 — the
  single largest per-item coefficient of any signal type feeding any
  dimension, and the only signal type with zero cross-dimension coupling).
  **Not unused.**
- `concept_explanations` — live, nonzero weight in `score_knowledge()`
  (1.0) and `score_adaptability()` (0.5). **Not unused.**
- `facts` — genuinely different. Grepped across every `score_<dimension>`
  function in `signals.py`: **`sig.facts` is never referenced in any of
  them.** Its only real consumer is `merge_signals()` (for cross-answer
  deduplication) and `consistency.check_new_facts()`/`compare()` — the
  contradiction-detection layer, which is a real and legitimate use, just a
  different one than competence scoring. **`facts` is "stored but unused"
  with respect to the six-dimension score, by design, not by accident** —
  it was never supposed to move a dimension score, and it doesn't.

**This is a clean, useful negative result**: four of the five buckets have
fully-wired, waiting scoring logic. The bottleneck for `decisions`,
`boundaries`, `constraints`, and `concept_explanations` is **100%
upstream, in extraction** — recovering them requires no change to
`signals.py`/`scoring.py` at all. `facts` is architecturally scoped away
from dimension scoring on purpose; recovering more of it would improve
contradiction-detection depth, not the six-dimension score.

---

## 6. Estimated impact on Ownership, Judgment, and Adaptability

Worked through the actual live formula (`TARGETS`, `GATES`, `signals.py`),
not simulated from scratch:

**Judgment** (`TARGET = 3.0`, gate ceiling 45 if no qualifying decision/
constraint/causal). In this sample, `causal_links` are common enough that
the JUDGMENT gate is very often already open via a complete causal chain,
independent of `decisions`/`constraints` — so the *gate* is usually not the
binding constraint. The *score* is: each recovered strong decision adds
`1.0 / 3.0 = 33.3` points of headroom directly (before any cap), and each
recovered constraint adds `0.5 / 3.0 = 16.7` points — on top of whatever
`causal_links` already contribute. At the human-observed presence rate
(~31% of decision-plausible turns, ~40% of constraint-plausible turns),
recovering this content would raise JUDGMENT's *achievable ceiling* on a
meaningful share of claims that currently score JUDGMENT from `causal_links`
alone or not at all — a real, additive gain, not a gate-opening one.

**Ownership** (`TARGET = 3.0`, gate ceiling 40 if no explicit boundary).
This is where recovery matters most, structurally: `boundaries` is
OWNERSHIP's only signal with **zero cross-dimension coupling** and the
**largest single coefficient** (1.0) of anything feeding any dimension in
the whole formula. Today, per `SCORING_SEMANTICS_AUDIT.md` and confirmed
unchanged here, the OWNERSHIP gate in practice opens almost entirely via
`_is_first_person_action()` — "does any process step contain the word I" —
a near-unconditional pass in a first-person interview. Recovering even the
~29% of boundary-plausible turns found genuinely present here would let the
gate open on its **intended** mechanism (a real, quotable scope statement)
on a meaningful fraction of claims, rather than exclusively on the loosest
possible backdoor — a qualitative legitimacy gain on top of whatever
numeric score movement follows.

**Adaptability** (`TARGET = 2.0`, gate ceiling 40 if no transfer
reasoning). `concept_explanations` contributes only 0.5 weight here and is
the rarest of the five buckets by human-observed presence (~10%). Fixing
extraction for this bucket alone would move ADAPTABILITY the least of the
three named dimensions — its dominant lever, per `DIMENSION_VALIDITY_AUDIT.md`,
remains `causal_links` (complete or partial), which extraction is already
reasonably capturing. **This audit's finding does not change the earlier
audit's conclusion that ADAPTABILITY's independence problem is a `causal_links`
coupling issue, not primarily a `concept_explanations` extraction issue.**

---

## 7. Answer to the central question

> If planner and questioning were frozen today, how much additional signal
> could be recovered purely by fixing extraction?

**A real, immediate, and bounded amount — concentrated in three of the five
buckets, not all five equally.**

- `decisions`, `boundaries`, and `constraints` each have a genuine,
  human-confirmed presence rate of **29–40%** on turns a reviewer would
  already expect to carry this content — and in **100% of those cases
  checked here**, the reason the structured signal is empty is that the
  live model's own JSON never included it, confirmed against the raw
  pre-validation text itself. None of this loss requires a new question,
  a different move, or a planner change to recover — it requires the
  extractor to route content it is already looking at (and already
  correctly capturing into `process_steps`, `causal_links`, or
  `quantities`) into the schema-correct bucket instead. This is the
  cleanest form of "recoverable by extraction alone" this audit could find:
  the evidence is not missing from the conversation, it is misfiled.
- `concept_explanations` is recoverable to a much smaller degree — not
  because extraction fails it any less thoroughly (100% of its misses are
  also "model failed to extract"), but because genuinely generalizable,
  transferable-mechanism content is rare even in a sample deliberately
  sourced from the moves (`FAILURE`, `DEPENDENCY`, `AUTHORITY`) most likely
  to produce it (~10% human-observed presence). Fixing extraction recovers
  what's there; there is simply less there to recover.
- `facts` is the outlier: extraction is not the bottleneck at all — the
  one instance in this sample worked correctly end to end. The ceiling
  here is set by how rarely a real interview answer states an actual
  *value* against a recognized taxonomy key, which is a **questioning**
  gap (asking for the number), explicitly frozen out of scope for this
  audit.

**Net:** extraction-only fixes, with the current questions and current
planner completely unchanged, could plausibly move `decisions`,
`boundaries`, and `constraints` from a combined **~1% current recovery
rate to somewhere in the 25–35% range** on the population of turns that
already contain this content — a large, immediate, zero-new-questions
gain concentrated on exactly the three buckets `DIMENSION_VALIDITY_AUDIT.md`
already identified as Judgment's and Ownership's only would-be independent
signals. `concept_explanations` and `facts` have a much smaller
extraction-only ceiling, for two different reasons (rarity of the content
itself, and a genuine planner/questioning gap respectively) — recovering
more of either would require the frozen layers this audit was asked not to
touch.

---

## 8. Recommended fixes, ranked by expected signal gain

Extraction-mechanics only, per the brief's instruction — no planner,
scoring, or schema-shape changes proposed.

1. **Fix the causal_links length-ceiling cascade first.** It is the one
   mechanism in this audit found to discard an entire answer's worth of
   correctly-extracted signal — across every bucket, not just the five
   studied here — over a single oversized field unrelated to the buckets
   in question. It fired on 10 of 105 targeted answers here (~9.5%),
   consistent with `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`'s independently-
   measured 14.6% on a differently-composed sample. Confirmed here, on
   fresh live calls, that the raw JSON in every one of these cases still
   contained nothing in the five target buckets regardless — so this fix's
   gain is on the buckets that *do* already populate (`process_steps`,
   `causal_links`, `tools`, `entities`), not on these five directly, but it
   removes a real, quantified source of total-answer signal loss and
   should not wait behind a five-bucket-specific fix.
2. **Give the extraction prompt explicit disambiguation guidance for the
   four confirmed dead buckets**, ranked by measured human-observed
   ceiling: `constraints` (40%) and `decisions` (31%) first, `boundaries`
   (29%) close behind, `concept_explanations` (10%) last. Every
   "model failed to extract" example in §2 shows the same shape: a decision
   phrased with an explicit alternative gets read as a step; a stated
   scope boundary gets read as a task list; a numeric limit gets read as a
   bare quantity. The model is not missing the content — it is not being
   told these are structurally different from what it's already
   confidently extracting into three other buckets it clearly favors
   (`process_steps`, `causal_links`, `quantities`).
3. **Fix the heuristic fallback's degenerate-structure bug**
   (`scope_held == scope_handed_off`, and the parallel `cause == action`
   defect already named in `EVIDENCE_EXTRACTION_FIDELITY_AUDIT.md`) as a
   narrow, contained correction — it is currently the *only* path that has
   ever produced a `boundaries` item in this sample, and it produces a
   structurally false one when it does.
4. **Do not prioritize `facts` or `concept_explanations` extraction work
   ahead of the other three.** Both are extraction-healthy relative to how
   little qualifying content exists to extract; time spent here has the
   smallest measured ceiling of the five buckets audited.
