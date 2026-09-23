# Evidence Extraction Fidelity Audit

**The assumption every prior audit rested on, tested for the first time
here:** that `signals_found`, `answer_score`, and the persisted evidence
record actually reflect what the candidate said. This audit does not use any
pre-computed export field as ground truth — it re-runs the real, live
production extraction pipeline against real answers and reads the raw
structured output against the source text by hand.

## 0. Method — what was actually done, and a genuine infrastructure obstacle

**A stratified sample of 48 real answers** (from the same 39-candidate,
212-question corpus used throughout this audit series) was drawn across
three yield bands — 18 high-signal (≥6), 18 mid (2-5), 12 low (0-1) — so the
sample could speak to recall on rich answers and to hallucination risk on
thin ones alike.

**Every sample was re-extracted by calling the actual live pipeline** —
`api.engine.evidence.score_response()`, the same function `_persist_evidence`
calls in production, against `gpt-4o` with the real `extract_signals` prompt
— not a simulation, not a re-derivation from stored fields. This required
fixing a real local obstacle first: outbound HTTPS from Python was failing
with `CERTIFICATE_VERIFY_FAILED` because this network runs behind a
corporate TLS-inspecting proxy (Netskope) whose root the OS trusts (curl
worked) but Python's bundled `certifi` store does not. The fix was to export
the already-OS-trusted root from the System keychain and combine it with
`certifi`'s bundle for this session's HTTP client only — the same trust the
machine already extends to every other application, not a weakened or
bypassed check. Noted here because it is a real, previously-undiscovered
local environment gap, not a finding about the product.

This cost 48 real `gpt-4o` calls (well under $1 based on this project's own
documented per-call costs elsewhere in `docs/`).

## 1. Precision by signal type

Of 48 samples, 32 produced genuine, non-empty, live-model extractions (7
silently fell back to a heuristic — see §8 — and 9 were correctly-recognized
non-answers). Precision below is read from close comparison of each
extracted signal against its quote and the surrounding sentence — not
whether a quote merely exists (every quote checked was genuinely verbatim;
`enforce_verbatim()` is doing its job, see §1d).

**(a) High precision, minimal issues:** `quantities` (9 items, all
correctly transcribed values with sensible `refers_to` labels — e.g. "1 MB,"
"100 requests per minute," "500 ms" all matched their real referents
exactly) and `tools` when a tool is genuinely described in use (Jenkins with
"build automated unit, integration, E2E and smoke tests," Grafana-style
monitoring tools named alongside a real described action). `metric_definitions`
is honest about its own limits — `how_measured` is correctly left `null` when
the candidate only named a metric without explaining it, rather than
inventing a derivation (this is the one place the system's own design intent
— "an absent `how_measured` should read as CHEAP, not DEAR" — visibly works).

**(b) Real precision defects, found repeatedly, not once:**

- **Over-segmentation.** A single descriptive sentence listing several
  parallel items ("I checked LangFuse for all the insights, I checked the
  latency, I checked...") is routinely exploded into 3-4 separate
  `process_steps`, each with its own (correctly verbatim, but redundant)
  quote — even though nothing in the sentence expresses sequence. One answer
  produced **12 separate `entities`** from two enumerating sentences ("API
  endpoints, permissions, environment variables, notification settings..."),
  four of them sharing the exact same quote. The words are real; treating an
  enumerated list as N independent signals inflates apparent evidence density
  without N times the actual evidence.
- **Thin/circular interpretive fields.** `ToolMention.usage` and
  `DecisionSignal`-shaped content frequently gets an interpretive field that
  just restates the quote rather than adding synthesis (`"usage": "checked
  LangFuse for all the insights"` — identical to the quote itself). Not
  fabrication, but not the added interpretation the schema's own docstring
  ("`usage` present = they described using it") implies either.
- **Causal-link mislabeling under the heuristic fallback specifically**
  (not the live model — see §8): in two heuristic-path samples, a
  `causal_link`'s `cause` and `action` fields were set to the *identical*
  string, and one `OwnershipBoundary`'s `scope_held` and `scope_handed_off`
  were also set identically — degenerate structures that assert a
  cause-and-effect or a two-sided handoff where the heuristic engine
  actually found only one span of text. This pattern was **not observed once
  in the 32 genuine live-model extractions** checked — it is specific to the
  weaker fallback path.

**(c) The clearest hallucination found, and it is fallback-specific.** One
heuristic-path extraction invented two metric labels — `"Positions
closed"` and `"Time to fill"` — attached to real, verbatim quotes that
never mention either concept; the candidate's answer was about pipeline
tracking gaps, not stated recruiting KPIs. This is the exact "quote exists,
meaning doesn't" pattern named in the brief — real text, invented
interpretation layered on top. **No comparably clear hallucination was found
in the 32 live-model extractions in this sample.** This is worth stating
plainly: `enforce_verbatim()` plus a real model call appears to be
meaningfully more conservative about invention than the heuristic fallback
is, which makes §8's fallback-rate finding matter more, not less.

**(d) Verbatim enforcement itself works as designed.** Across the sample,
`log.warning` fired three times for "quote not verbatim in the answer,"
correctly dropping those signals rather than keeping them — the one
mechanism this whole pipeline leans on hardest is functioning exactly as
documented.

## 2. Recall by signal type — the headline finding

Across all **32 genuine, non-empty live extractions**, tallying every
signal bucket used at all:

| Bucket | Answers using it | Total items |
|---|---:|---:|
| `process_steps` | 24 / 32 | 72 |
| `entities` | 24 / 32 | 45 |
| `causal_links` | 19 / 32 | 25 |
| `tools` | 13 / 32 | 14 |
| `quantities` | 5 / 32 | 9 |
| `metric_definitions` | 5 / 32 | 7 |
| `incident_markers` | 2 / 32 | 2 |
| **`decisions`** | **0 / 32** | **0** |
| **`constraints`** | **0 / 32** | **0** |
| **`concept_explanations`** | **0 / 32** | **0** |
| **`boundaries`** | **0 / 32** | **0** |
| **`facts`** | **0 / 32** | **0** |

**Five of the twelve structured signal categories were never populated once,
in this entire sample, including in answers whose content is unambiguously
that category.** This is not a low-recall problem for these five buckets —
it is a functionally dead pathway. Confirmed by close reading, at least six
of the 32 answers contain textbook-clear content for one of these five
categories and none of it was captured in its intended bucket:

- Jyoti (`thread`/manager): *"I had ownership of the day-to-day recruitment
  process... I could independently decide which sourcing channels...
  For decisions involving final candidate selection... I would coordinate
  with the hiring manager and seek the required approval/sign-off."* — a
  textbook `OwnershipBoundary` (scope held vs. handed off) and a textbook
  `DecisionSignal` (choice + reason), in one answer. `boundaries: []`,
  `decisions: []`.
- SK (`AUTHORITY`): *"independently I took the decisions like launching a
  referral mechanism... I needed a larger budget... so that required
  approval."* Same shape, same result: both empty.
- Renuka Malhotra (`AUTHORITY`): *"I could use the reports to... Decisions
  involving pricing changes, major commitments, or strategy would require
  management approval."* Same shape, same result.
- Tushar (`OWNERSHIP_BOUNDARY` — the move whose entire purpose is this
  signal): *"I worked on task assignment, bandwidth management, automation
  system design, mentoring, peer review."* `boundaries: []`.
- `t` (`thread`/api): *"payload limit of around 1 MB... rate limit of
  approximately 100 requests per minute... expected response time of under
  500 ms"* — textbook `ConstraintSignal` content, captured instead as
  `quantities` only. `constraints: []`.
- Ayush (`thread`/report): *"I corrected both before doing anything else...
  **rather than** just dropping or ignoring the bad values"* — an explicit
  trade-off/decision statement. `decisions: []`.

Every one of these got its real content redirected into `process_steps` or
`causal_links` instead — which is precisely §3's finding.

## 3. Causal chain fidelity

25 `causal_links` were produced across the 32 live extractions; **16 (64%)
were complete** (cause, action, and outcome all present) and **9 (36%)
incomplete**, almost always missing `outcome`. The specific, repeated pattern
behind the incomplete ones: the candidate's actual resolution or result *is*
present in the answer, but it gets extracted into a separate `process_steps`
entry rather than closing the causal chain as its `outcome`. Example: Tushar's
answer states a clear cause ("sprint plans were very superficial") and a
clear fix ("implemented work breakdown strategy to enable better
estimation") — the extraction captures the cause correctly, sets
`outcome: null`, and puts the fix in `process_steps` instead, as an
unconnected fact rather than the chain's resolution. The same disconnection
appears in Ayush's richest answer in the whole sample (the funnel-bug/ROC-AUC
story): three separate causal_links, two with `outcome: null`, while the
actual overarching resolution ("the ROC-AUC of 0.82 became a number I
trusted") sits in `metric_definitions`, structurally cut off from the causal
chain it's the outcome of. **The individual pieces of a causal chain are
usually all present somewhere in the extraction; connecting them into one
complete chain is where fidelity breaks down.**

## 4. Ownership fidelity

Zero `boundaries` were extracted anywhere in the sample (§2). The specific
check the brief asked for — does "I worked on X" get inflated into "I owned
X" — did not occur in the direction feared; if anything the opposite
distortion happens: genuine, explicit ownership-boundary language ("I had
ownership of," "I took ownership of," "I could independently decide")
is *under*-captured, redirected into generic `process_steps` rather than
into a structure that would actually credit ownership as a bounded scope.
The risk this audit did find is different from the one hypothesized: not
that thin engagement gets inflated into ownership, but that explicit,
strong ownership language gets flattened into an undifferentiated list of
tasks, indistinguishable from a `process_work` claim with no ownership
framing at all.

## 5. Decision vs. process confusion

This is the single most reproducible failure mode in the whole sample.
Every one of the four clearest `AUTHORITY`/`OWNERSHIP_BOUNDARY`-move answers
examined — content whose entire purpose is to state a decision, a choice, or
a bounded responsibility — had that content extracted as `process_steps`
instead: "I took the decisions like launching a referral mechanism" became
step *"launching a referral mechanism"*; "I could independently decide which
sourcing channels..." became step *"decide which sourcing channels and
approaches to use"*; "I worked on task assignment... mentoring..." became
five separate steps. **Decision-shaped and ownership-shaped sentences are
being systematically read as procedural sequences** — the schema
distinguishes `process_steps` (execution) from `decisions` (judgment) from
`boundaries` (ownership) precisely so these can be scored as different
competence dimensions, and in this sample that distinction was never
observed to survive extraction.

## 6. Missing high-value evidence

Cross-referencing against `EVIDENCE_GAP_FRAMEWORK.md`'s minimal eight-gap
set: the gaps that framework already identified as having "no dedicated
collection mechanism" (`OUTCOME`, `TRADEOFF`, `DECISION_RATIONALE`) are made
structurally worse by what this audit found — even on the answers where a
move *did* successfully ask for decision rationale or a trade-off, and the
candidate *did* answer it, the extractor's `decisions` bucket still didn't
fire. The gap identified previously as a *planning* problem (nothing asks
for this) is compounded by an *extraction* problem (even when something
does ask, and gets an answer, the structured signal meant to capture it is
dead). The same is true for `boundaries`/ownership.

## 7. Top 20 extraction failure modes

Ranked by how often each was observed in this sample, most frequent first:

1. Decision-shaped content extracted as `process_steps` (4 of 4 clear
   `AUTHORITY`/`OWNERSHIP_BOUNDARY` cases checked).
2. Ownership-boundary content extracted as `process_steps`, never
   `boundaries` (same 4 cases; `boundaries` never fired at all, 0/32).
3. `constraints` never populated even when explicit numeric limits are
   stated (`t`'s payload/rate/latency example).
4. `decisions` never populated even when explicit decision language is
   present ("I decided," "independently," "rather than").
5. Complete causal chains split apart — cause and action captured, real
   stated outcome orphaned into `process_steps` (9 of 25 causal_links, 36%).
6. Over-segmentation of one enumerating sentence into 3-4 `process_steps`.
7. Over-segmentation of one enumerating sentence into many `entities`
   sharing identical quotes (one case: 12 entities from 2 sentences).
8. `concept_explanations` never populated, even on answers with
   generalizable domain reasoning (Ayush's leakage-detection explanation
   qualifies and was not captured as one).
9. `facts` never populated in this sample (the consistency-engine memory
   layer had nothing to compare across answers, for any of the 32).
10. Schema-driven total extraction loss when one field overflows its
    character limit (§8) — discards every other correctly-extractable signal
    in that answer, not just the offending field.
11. Same root cause (10) recurs deterministically — the model regenerates an
    equally-long violation on the mandatory retry, so the retry never
    rescues it.
12. Heuristic-fallback-specific: degenerate `causal_link` with identical
    `cause`/`action` text.
13. Heuristic-fallback-specific: degenerate `OwnershipBoundary` with
    identical `scope_held`/`scope_handed_off` text.
14. Heuristic-fallback-specific: invented metric labels attached to a real
    but unrelated quote (§1c).
15. Heuristic-fallback text truncation mid-word, producing quotes that end
    on a fragment ("...with acc").
16. Thin/circular `usage` and `reason` interpretive fields that restate the
    quote rather than synthesizing it.
17. Faithful-but-nonsensical extraction of garbled voice-to-text input
    (e.g., "psychic learns dummy classifier" for a mis-transcribed
    "scikit-learn") — not an extraction defect, but a real artifact that
    reaches the evidence record looking like one.
18. Non-determinism: identical input, re-extracted, yields a different
    signal count 23% of the time (11/48), by an average of 1.45 signals
    when it differs.
19. `incident_markers` rarely used (2/32) even on answers describing a
    specific one-off episode with enough detail to qualify.
20. Weak `metric_definitions` entries where `how_measured` is correctly
    left null but the metric itself is only half-real (e.g., a metric name
    volunteered as a hypothetical example during a hedged/generic answer,
    still recorded as if it were a personal metric).

## 8. Most damaging misses

The five silently-dead buckets (§2) are the most damaging miss in the audit,
for a structural reason beyond their own absence: `decisions`, `boundaries`,
and `constraints` are exactly the signal types the earlier
`METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md` (finding EC1) identified as the
*intended*, structured route to opening the JUDGMENT and OWNERSHIP scoring
gates — as opposed to the generic first-person-verb-matching route EC1 flagged
as gameable. This audit shows the intended route isn't merely weaker than
the verb-matching fallback — in this sample it **never fired at all**. That
means the gameable, lexical-pattern-match pathway EC1 warned about is not
one of two routes to opening those gates; on this evidence, it may be
functioning as close to the *only* route in practice.

## 9. Most damaging hallucinations

Both damaging hallucinations found are specific to the heuristic fallback,
not the live model:

1. **Invented recruiting-metric labels** ("Positions closed," "Time to
   fill") attached to a real quote that discusses neither — the clearest
   "quote exists, meaning doesn't" case in the sample.
2. **Degenerate self-referential structures** (`cause == action`,
   `scope_held == scope_handed_off`) that assert a two-part relationship
   the source text doesn't actually contain in two parts.

No comparably clear hallucination was found in the 32 live-model
extractions — the live path's failures in this sample are almost entirely
**miscategorization and incompleteness**, not invention. This is a real,
positive finding and is reported as such: `enforce_verbatim()` combined with
a live model call is doing meaningfully better anti-fabrication work than
the fallback it's protecting against — which raises the stakes on how often
that fallback actually fires (see next).

## Additional finding: a measured 14.6% silent degradation rate

7 of 48 real extraction attempts (14.6%) fell back to the heuristic engine
— **and all seven trace to the identical root cause**: the model produces a
`causal_links[0].quote` or `.action` field that exceeds the schema's
240/160-character maximum, the mandatory single retry regenerates an
equally-long violation, and the entire structured extraction for that
answer — not just the offending causal link, everything — is discarded in
favor of the weaker, faithfulness-verified-lower fallback. This is a single,
well-defined, narrow defect (a field-length ceiling that a genuinely
complete causal sentence routinely exceeds) causing a disproportionate
14.6% full-quality loss rate. Combined with §9's finding that the fallback
path is also where this sample's clearest hallucinations live, this specific
mechanism is the highest-leverage, most narrowly-scoped fix this audit
surfaced.

## Additional finding: extraction is measurably non-deterministic

Re-running the identical live pipeline against the identical stored answer
text produced a different `signals_found` count than the historical run in
11 of 48 cases (23%), averaging a swing of 1.45 signals. This is worth
stating plainly because it explains, from a new angle, why this product's
own architecture (`docs/CLAUDE.md`'s D8 replay principle: extraction is
recorded once and never re-run) is designed the way it is — extraction
itself is not guaranteed to reproduce, so anything built to *replay* rather
than *re-extract* is correctly avoiding a real instability this audit now
has direct evidence for.

---

## Is extraction quality currently the bottleneck?

**Partially, and in a specific, non-obvious way.** For the two guaranteed,
highest-volume dimensions (EXECUTION via `process_steps`, PROBLEM_SOLVING
via `causal_links`), extraction is a real but secondary bottleneck: signal
is captured, sometimes inflated (over-segmentation) and sometimes
incompletely linked (causal chains missing their outcome), but it is not
*absent*. Planner-level and coverage-level constraints, measured in the
prior audits, remain the dominant limiter for those two dimensions.

**For JUDGMENT and OWNERSHIP, extraction is not a secondary bottleneck — it
may be the primary one.** Every prior audit in this series that measured
JUDGMENT/OWNERSHIP under-coverage attributed it to planner scheduling,
seniority gating, or archetype exclusion — all real, all upstream of
extraction. This audit adds a finding none of those could see: **even when a
question successfully reaches a candidate and the candidate gives a clean,
on-topic, textbook decision or ownership-boundary answer, the extraction
layer routes that content away from the structures (`decisions`,
`boundaries`, `constraints`) that are supposed to carry it, in every case
checked.** Fixing the planner to ask more `AUTHORITY`/`OWNERSHIP_BOUNDARY`
questions, per `EVIDENCE_ENGINE_V2_DESIGN_AUDIT.md`'s recommendation, would
not by itself fix JUDGMENT/OWNERSHIP coverage if this specific extraction
defect isn't fixed alongside it — the better questions would still land on
an extraction path that empties `decisions` and `boundaries` regardless of
how well-targeted the question was. **This is the one place in the whole
audit series where the answer to "which layer should be fixed first" is not
clearly the planner** — it is at minimum tied with it, and for these two
specific dimensions, extraction fidelity is the more direct cause.
