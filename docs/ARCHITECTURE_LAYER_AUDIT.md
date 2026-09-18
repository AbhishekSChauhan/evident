# Evident — Layer-by-Layer Architecture Audit

**2026-09-18, against `api/` at `2659f20`.** Every claim below is a file:line
citation or a direct grep result, not an inference from a design doc. Where a
prior document (`docs/EVIDENT_MASTER_CONTEXT.md`, `CLAUDE.md`,
`docs/CURRENT_STATE.md`, `docs/DEEP_DIVE.md`) says something this audit
confirms, verifies differently, or contradicts, that is stated explicitly —
per the standing instruction, a conflict with the master context is surfaced,
not silently resolved.

**Companion, not duplicate:** `docs/METHODOLOGY_AUDIT_EVIDENCE_ENGINE.md`
(written concurrently, different session) audits the claim→competence
*pipeline* stage by stage. This document audits the *architecture layers* —
dimensions, categories, signals, nodes, graph, matching — as separately
requested. The two overlap in places and were derived independently; neither
assumes the other's conclusions.

---

## Layer 1 — Competence Dimensions

**Defined:** `api/schemas.py:44-57`. The `Dimension` enum has **twelve
members, not six**:

```python
class Dimension(str, Enum):
    SPECIFICITY = "SPECIFICITY"                # legacy
    PROCESS = "PROCESS"                        # legacy
    METRIC_OWNERSHIP = "METRIC_OWNERSHIP"      # legacy
    CAUSAL_REASONING = "CAUSAL_REASONING"      # legacy
    AUTHENTICITY = "AUTHENTICITY"              # legacy
    TOOL_FAMILIARITY = "TOOL_FAMILIARITY"      # legacy

    KNOWLEDGE = "KNOWLEDGE"                    # UCF — live
    EXECUTION = "EXECUTION"                    # UCF — live
    PROBLEM_SOLVING = "PROBLEM_SOLVING"        # UCF — live
    JUDGMENT = "JUDGMENT"                      # UCF — live
    OWNERSHIP = "OWNERSHIP"                    # UCF — live
    ADAPTABILITY = "ADAPTABILITY"              # UCF — live
```

**Scores calculated:** `engine/signals.py` — one `score_<dim>(sig, ...)`
function per dimension, all pure functions of `AnswerSignals` counts, no LLM.
`engine/scoring.py` then applies dimension + role weights and the consistency
multiplier. This matches the master context and `CLAUDE.md` rule 1 exactly.

**Evidence contribution:** verified per dimension in Layer 3's table below —
each UCF `score_*` function reads specific `AnswerSignals` fields.

### The finding: the six legacy dimensions are answered "conflated?" with total precision — they are dead code, not conflated code

Traced the entire call chain:

1. `score_specificity`, `score_process`, `score_metric_ownership`,
   `score_causal_reasoning`, `score_authenticity`, `score_tool_familiarity`
   are fully implemented in `signals.py:155-267`.
2. **Nothing calls them.** `grep -rn` across `api/` and `tests/` for each name
   returns zero hits outside their own `def` line.
3. `score_answer()` — the function that actually builds the scored dict fed
   into `score_claim()` — is hardcoded to six keys, all UCF
   (`signals.py:586-598`):
   ```python
   def score_answer(sig, job_family="general") -> dict[Dimension, DimensionScore]:
       return {
           Dimension.KNOWLEDGE: score_knowledge(sig, job_family),
           Dimension.EXECUTION: score_execution(sig, job_family),
           Dimension.PROBLEM_SOLVING: score_problem_solving(sig),
           Dimension.JUDGMENT: score_judgment(sig),
           Dimension.OWNERSHIP: score_ownership(sig),
           Dimension.ADAPTABILITY: score_adaptability(sig),
       }
   ```
4. `scoring.DIMENSION_ORDER` (`scoring.py:61-68`) — the tuple every weighting,
   ranking and dashboard-facing computation iterates — has exactly these same
   six members. The legacy six never appear in it.
5. `ClaimState.weakest_dimension()` (`orchestrator.py:396-410`), which decides
   which dimension gap the planner chases next, walks `scoring.DIMENSION_ORDER`
   only — so a legacy dimension can never be selected as a probing target.
6. **They are still referenced**, but only in places that feed a dimension
   name into targeting/wording tables that a UCF-only selector then filters
   through: `question.py`'s `GAP_HINTS` (six legacy entries, reachable only
   via `target_dimension`, which is always UCF — `question.py:919`),
   `MOVE_DIMENSIONS` (every forensic Move maps to a *mix* of legacy and UCF
   dimensions, e.g. `Move.OPERATING_CONTEXT: (PROCESS, TOOL_FAMILIARITY,
   EXECUTION)` — `question.py:1152-1161`), and `PROBE_LEVEL_DIMENSIONS`
   (`signals.py:60-78`, the pre-forensic qpol_2 equivalent).
7. Inside `score_claim()` (`signals.py:697-745`), the `probed` set genuinely
   does get populated with legacy dimension names from those tables — then
   `for dimension, entry in scores.items(): entry.probed = dimension in
   probed` only ever iterates the six UCF keys `scores` actually has. The
   legacy entries sitting in `probed` are computed and discarded every time.

**Verdict:** this is not dimension conflation in the sense of two systems
scoring the same evidence differently and disagreeing — it is **one live
system (UCF) and one fully dead system (legacy) sharing an enum and several
targeting tables**, with zero test coverage on the dead half
(`grep -rn "score_specificity\|score_process\b\|..." tests/` → nothing). The
risk is not incorrect scores; it is maintenance cost and reader confusion —
anyone reading `MOVE_DIMENSIONS` or `GAP_HINTS` without doing this trace would
reasonably conclude the legacy six still matter.

---

## Layer 2 — Evidence Categories

**The closest code artifact to what's being asked about is `EvidenceCategory`,
`engine/v2_evidence_planner.py:23-33`** — ten members: `OWNERSHIP`, `PROCESS`,
`METRIC_DEFINITION`, `DECISION`, `DEPENDENCY`, `INCIDENT`, `CONSTRAINT`,
`CAUSAL_CHAIN`, `ARTIFACT`, `CROSS_CLAIM_LINK`.

**This entire mechanism is gated by `EVIDENCE_PLANNER_V2`, default `false`**
(`config.py:105`). It is wired into the orchestrator
(`orchestrator.py:54,215-322,1153-1193` — imported, called from
`ClaimState.evidence_state`, `plan_next_evidence`) but does not run unless the
flag is flipped. The *live* default categorization mechanism is the forensic
`Move` enum under `qpol_3` (nine members: `METRIC_DEFINITION`,
`OWNERSHIP_BOUNDARY`, `OPERATING_CONTEXT`, `FAILURE`, `EXCLUSION`,
`DEPENDENCY`, `PEOPLE`, `AUTHORITY`, `COHERENCE`, `PERTURB`), which is a
different vocabulary for a similar purpose.

| Category (as asked) | Exists | Used in Planning | Used in Questioning | Used in Scoring | Notes |
|---|---|---|---|---|---|
| **Decision** | ✅ `EvidenceCategory.DECISION` + `AnswerSignals.decisions` (always live) | ⚠️ Only if `EVIDENCE_PLANNER_V2=true` | ✅ Live via `Move.AUTHORITY`/qpol_2 `ProbeLevel.DECISION` regardless of the flag | ✅ `score_judgment`, `score_ownership`, `score_adaptability` all read `sig.decisions` | Two parallel category systems point at the same signal type |
| **Metric Definition** | ✅ `EvidenceCategory.METRIC_DEFINITION` + `AnswerSignals.metric_definitions` | ⚠️ v2-only | ✅ Live via `Move.METRIC_DEFINITION` | ✅ `score_knowledge` | Fully wired in the live path independent of the dormant v2 category |
| **Constraint** | ✅ `EvidenceCategory.CONSTRAINT` + `AnswerSignals.constraints` | ⚠️ v2-only | ⚠️ No dedicated live Move targets it directly; captured incidentally | ✅ `score_problem_solving`, `score_judgment` | Live scoring exists; live *targeted questioning* for it does not |
| **Incident** | ✅ `EvidenceCategory.INCIDENT` + `AnswerSignals.incident_markers` | ⚠️ v2-only | ✅ Live via `Move.FAILURE` | ✅ `score_knowledge`, `score_problem_solving` | Confirmed in the trace in `docs/DEEP_DIVE.md`: gates PROBLEM_SOLVING, frequently unmet |
| **Causal Chain** | ✅ `EvidenceCategory.CAUSAL_CHAIN` + `AnswerSignals.causal_links` | ⚠️ v2-only | ⚠️ No single Move owns it; produced incidentally across several | ✅ Read by five of six UCF score functions | The most heavily reused signal type; also the one measured as most often incomplete (`outcome: null`) in fixture mode |
| **Ownership Boundary** | ✅ `EvidenceCategory.OWNERSHIP` + `AnswerSignals.boundaries` | ⚠️ v2-only | ✅ Live via `Move.OWNERSHIP_BOUNDARY` | ✅ `score_ownership` | Named `OWNERSHIP` in `EvidenceCategory`, collides in name (not meaning) with `Dimension.OWNERSHIP` |
| **Cross Claim Link** | ✅ `EvidenceCategory.CROSS_CLAIM_LINK` | ❌ **Triple-gated**: (1) `EVIDENCE_PLANNER_V2=false` by default, (2) even when true, explicitly excluded from `PRIORITY_ORDER` at `orchestrator.py:1191`, (3) depends on `claim_graph.txt` — **a prompt file that exists on disk (`api/prompts/claim_graph.txt`) but is never loaded or rendered anywhere in `api/`** | ❌ | ❌ | The clearest "exists in name only" category. `orchestrator.py:1164`: *"CROSS_CLAIM_LINK is simply never offered — not a crash, not a bug"* |
| **Tradeoff** | ❌ No `EvidenceCategory` or `Dimension` member. Exists only as a **keyword heuristic** inside `_is_strong_decision()` (`signals.py:286-295`: `"evaluated", "compared", "versus", "tradeoff"...`) that upweights a `DecisionSignal` from 0.5x to 1.0x in `score_judgment` | — | — | ⚠️ Indirectly, as a weight multiplier only | Not a category; a quality flag on an existing category |
| **Risk** | ❌ Does not exist as an evidence category anywhere. The only "risk" in the codebase is `risk_areas` in `job_fit.JobFitResult` (`job_fit.py:252,271`) — a **recruiter-facing label for an unmet job requirement**, semantically unrelated to a candidate's risk-awareness or risk-taking as evidence | — | — | — | If "did the candidate reason about risk" is the intended meaning, nothing captures it |
| **Transfer** | ⚠️ Exists as a *probing strategy* (`ProbeLevel.TRANSFER`, `Move.PERTURB`), not as a captured evidence structure. Its output is scored as "prospective reasoning" inside `score_adaptability`, reading the same `causal_links`/`decisions`/`concept_explanations` fields any other move produces | N/A — it's a move, not a category | ✅ Live, `Move.PERTURB` | ✅ `score_adaptability` | There is no `TransferSignal` type distinct from a regular causal/decision signal; "transfer" is a property of *when* it was asked, not *what* was extracted |

**Missing categories:** Risk (no analog at all) and Tradeoff (heuristic only,
not a structure) as stated above.

**Duplicate categories:** `EvidenceCategory.OWNERSHIP` (v2, dormant) vs
`Dimension.OWNERSHIP` (live) — same word, different layer, easy to conflate
when reading code cold.

**Categories present in code but absent from architecture docs:**
`ARTIFACT` and `DEPENDENCY` in `EvidenceCategory` have no mention in
`EVIDENT_MASTER_CONTEXT.md` or `CLAUDE.md`'s architecture section. `ARTIFACT`
maps to `Dimension.SPECIFICITY` only (`question.py:1171`) — i.e. to a
dimension already established as dead — so even if `EVIDENCE_PLANNER_V2` were
turned on, targeting `ARTIFACT` would credit a dimension nothing reads.

---

## Layer 3 — Signals

**Reframing required before the table means anything:** the six terms in the
prompt (*Specificity, Process, Metric Ownership, Causal Reasoning,
Authenticity, Tool Familiarity*) are not a signals layer in this codebase's
vocabulary — **they are the six legacy `Dimension` members from Layer 1**,
already shown dead. Answering the requested table literally would report
"exists, scored" and silently misrepresent the system, since "scored" here
means "a function exists that is never called."

**The actual signal layer is `AnswerSignals`** (`schemas.py:269-284`), LLM
call #3's output — eleven typed lists plus `facts`, none of which is named
after a dimension:

| Signal (real name) | Extracted | Persisted | Scored (feeds which live UCF dimension) | Used in Graph | Notes |
|---|---|---|---|---|---|
| `quantities` | ✅ LLM #3 / heuristic | ⚠️ Inside `responses.signals_json` only — no dedicated column | EXECUTION | ⚠️ Only via `evidence.quotes_json` text, unindexed | Also the sole input to `total_signals()`'s quantity count |
| `process_steps` | ✅ | ⚠️ blob only | KNOWLEDGE, EXECUTION, OWNERSHIP | ⚠️ | — |
| `causal_links` | ✅ | ⚠️ blob only | KNOWLEDGE, PROBLEM_SOLVING, JUDGMENT, ADAPTABILITY | ⚠️ | Read by **four of six** score functions — the single most load-bearing signal type, and per `docs/DEEP_DIVE.md` the one most often incomplete (`outcome: null`) in fixture mode |
| `tools` | ✅ | ⚠️ blob only | EXECUTION | ⚠️ | Legacy `TOOL_FAMILIARITY` was the dimension actually named for this; now folded into EXECUTION only |
| `metric_definitions` | ✅ | ⚠️ blob only | KNOWLEDGE | ⚠️ | — |
| `incident_markers` | ✅ | ⚠️ blob only | KNOWLEDGE, PROBLEM_SOLVING | ⚠️ | Gates PROBLEM_SOLVING; the coverage audit found this open in only 6/23 evidence rows locally |
| `decisions` | ✅ | ⚠️ blob only | JUDGMENT, OWNERSHIP, ADAPTABILITY | ⚠️ | `_is_strong_decision()` weight logic (Tradeoff, above) lives here |
| `constraints` | ✅ | ⚠️ blob only | PROBLEM_SOLVING, JUDGMENT | ⚠️ | — |
| `boundaries` | ✅ | ⚠️ blob only | OWNERSHIP | ⚠️ | Highest-priority OWNERSHIP evidence per `CLAUDE.md`; first-person verbs are a secondary, weaker path in the same function |
| `concept_explanations` | ✅ | ⚠️ blob only | KNOWLEDGE, ADAPTABILITY | ⚠️ | — |
| `entities` | ✅ | ⚠️ blob only | OWNERSHIP only | ⚠️ | Legacy `AUTHENTICITY` was named for people/systems recall; now folds into OWNERSHIP, a narrower use |
| `facts` | ✅ | ✅ **Dedicated table** — `session_facts` | **None.** Feeds `consistency.py` only | N/A | The one signal type explicitly excluded from competence scoring by design (`CLAUDE.md`: consistency is session-level, applied once) |

**Missing signals:** nothing captures **risk reasoning** or **tradeoff
structure** as first-class signal types (Layer 2's gap, restated at the
signal level).

**Unused signals, precisely:** none of the eleven `AnswerSignals` fields is
fully unused — every one feeds at least one live UCF dimension except `facts`
(used elsewhere, by design). The six *legacy dimensions* that consumed some of
these same signals (`SPECIFICITY` from `quantities`+`entities`,
`TOOL_FAMILIARITY` from `tools`, `AUTHENTICITY` from `incident_markers`) are
what's unused — the signals themselves are all live, just under fewer,
consolidated dimension names than the legacy system used.

**A precision bug found while building this table:** `total_signals()`
(`signals.py:600-608`), the function underlying every "evidence yield" number
in `studies/evidence_yield/` and `studies/coverage_and_yield/`, sums only
**seven** of the eleven fields — `quantities + process_steps + causal_links +
tools + metric_definitions + incident_markers + entities`. It omits
`decisions`, `constraints`, `boundaries`, and `concept_explanations`
entirely, despite all four feeding live dimension scores (JUDGMENT,
OWNERSHIP, KNOWLEDGE respectively). **Every ΔE and "signals_found" number in
this project's yield studies is undercounting.** This does not invalidate
their relative comparisons (all rows undercount the same way), but it means
"average evidence per response" as reported anywhere is a floor, not the true
count.

**Additional signals found, undocumented in the architecture docs:**
none beyond the eleven above — the search for a hidden twelfth field in
`AnswerSignals` or a shadow signal type elsewhere in `api/engine/` came up
empty.

---

## Layer 4 — Evidence Nodes

**None of the five requested node types is a distinct persisted entity.**
The only tables in the 16-table schema that hold anything resembling
per-answer evidence are `evidence` (dimension-level aggregates) and
`session_facts` (consistency memory). There is no `decisions`, `incidents`,
or `outcomes`-as-evidence table.

| Evidence Node | Exists | Persisted | Linked to claims | Linked to dimensions | Linked to jobs | Notes |
|---|---|---|---|---|---|---|
| **Facts** | ✅ `ExtractedFact` (schema) | ✅ **`session_facts` table**, dedicated | ⚠️ Via `session_id`, not `claim_id` — facts are session-scoped, not claim-scoped | ❌ — facts feed consistency, not dimension scoring, by design | ❌ | The one node type with a real table |
| **Quotes** | ✅ Every signal type carries a `quote` field | ✅ `evidence.quotes_json` (a JSON array column, not rows) | ✅ via `evidence.claim_id` | ✅ via `evidence.dimension` | ❌ | Quotes are the one thing verified verbatim (`enforce_verbatim()`); still not individually queryable — a JSON blob in a column, no index into its content |
| **Decisions** | ✅ `DecisionSignal` type | ❌ **Only inside `responses.signals_json`.** No `decisions` table, no dedicated row | ⚠️ Only by re-parsing the parent response's blob | ❌ directly — contributes to `evidence.score` for JUDGMENT/OWNERSHIP/ADAPTABILITY, but the decision itself isn't a queryable row | ❌ | Same story for `IncidentMarker`, `ConstraintSignal`, `OwnershipBoundary`, `CausalLink` — every typed signal is trapped in one response's JSON, not promoted to its own table |
| **Incidents** | ✅ `IncidentMarker` type | ❌ blob only | ⚠️ | ❌ directly | ❌ | — |
| **Outcomes** | ⚠️ Two unrelated meanings collide under this name: (a) `CausalLink.outcome`, a signal sub-field, blob-only; (b) `CandidateOutcome`, a **real, dedicated, append-only table** — but that's the *hiring decision* (rejected/shortlisted/hired), not an evidence node | (a) ❌ (b) ✅ | (a) ⚠️ (b) via `candidate_id`, not `claim_id` | (a) ❌ (b) ❌ — hiring decisions aren't linked to dimension scores at all yet | (a) ❌ (b) ✅ via `role_id` | **Naming collision worth fixing before it causes a real bug**: "outcome" means two different things in this codebase depending on which file you're in |

**Evidence structures currently captured but unused:** none outright unused —
every typed signal feeds scoring. What's captured-but-**unqueryable** is the
real finding: `decisions`, `incidents`, `constraints`, `boundaries` and
`causal_links` all exist as rich typed Pydantic objects with verified quotes,
and all of them are serialized into one JSON text column
(`responses.signals_json`) and never promoted to their own rows. This is the
same finding `docs/DEEP_DIVE.md` §1.3 made about the `evidence` table's
indexing — restated here at the signal-node level: **the data model has
typed nodes in its schemas.py but not in its models.py.**

**Evidence structures missing entirely:** a `RiskSignal` and a
`TradeoffSignal` (Layer 2/3's gap), and any structure representing "outcome"
unambiguously (the naming collision above).

---

## Layer 5 — Evidence Graph

**Schema:** no dedicated graph tables (no `nodes`, `edges`, or
`evidence_nodes` table — confirmed absent, and `models.py:459-461` states the
absence is deliberate: *"There is no signals blob, no copied quotes and no
`evidence_nodes` table"* on `Evaluation`, to avoid a second source of truth).
`graph.build_candidate_graph()` (`graph.py:265-490`) assembles a
`CandidateGraph` **Pydantic response object** at request time from `select()`
queries — it is a read-model, not a persisted or indexed graph.

**Node types (as they exist today):** `CandidateGraph` → `ClaimGraph` (one
per claim, carries `.qa` turns and `.claim_score`) → dimension profile
entries. That's the full node vocabulary. No `EvidenceNode` row exists in the
database despite `schemas.py:304` declaring an `EvidenceNode` **Pydantic**
type — it's a response shape, assembled on the fly from `evidence` table
rows, never itself stored.

**Edge types:** foreign keys only — `claim_id`, `response_id`, `candidate_id`.
No edge has a type, a weight, or a direction beyond what a foreign key
implies. There is no traversal API; every "traversal" is a `JOIN` written
fresh in whichever function needs it.

**Scoring propagation:** real and correct — `evidence.score` (per
answer×claim×dimension) → `score_claim()` (union over a claim's answers) →
`scoring.claim_score()` (weighted, with the operational-evidence bonus) →
`graph.recompute_profile()` (aggregate across claims) → `evaluation.
competence_score`. This chain is well-tested (532 passing tests touch most of
it) and is the strongest layer in this whole audit.

**Confidence propagation:** exists as `probed` / `role_coverage`, not as a
numeric confidence score per node. `DimensionScore.probed` is boolean, not
graded — a dimension probed once with weak evidence and one probed five times
with strong evidence both read `probed: true`.

**Recruiter-facing outputs:** `why_ranked` (per `CLAUDE.md`, on every ranked
row) and the `dimension_profile` with `basis` strings — these are real and
are the strongest explainability artifact in the product.

### Desired vs. current state, the four-hop chain

| Hop | Desired | Current state |
|---|---|---|
| Claim → Evidence | ✅ | **Fully exists.** `evidence.claim_id` FK, one row per answer×claim×dimension, with verified quotes |
| Evidence → Dimension | ✅ | **Fully exists.** `evidence.dimension` column, aggregated by `score_claim()` |
| Dimension → Job Requirement | ⚠️ | **Exists, but shallow for one of two requirement categories** — see Layer 6. A 9-entry lookup table (`COMPETENCY_MAP`) for `COMPETENCY`-category requirements; for `SKILL`/`DOMAIN`-category requirements, this hop does not use dimensions at all (see below) |
| Job Requirement → Candidate Match | ✅ arithmetic, ⚠️ input quality | `calculate_job_fit()` produces a real, deterministic, LLM-free score. Its inputs are only as good as the two hops above it |

**The chain is real end to end.** The gap is not "does it exist" — it does —
the gap is that hop 3 quietly forks into two different mechanisms, and one of
them abandons the graph entirely. That fork is Layer 6.

---

## Layer 6 — Job Matching

**Can matching use the six UCF dimensions? Yes, for one of the two
requirement categories.** `job_fit.verify_requirement_coverage()`
(`job_fit.py:87-186`) branches on `req.category`:

**Case A — `COMPETENCY`** (`job_fit.py:95-129`): deterministic, dimension-based,
no LLM, no keyword matching. `_map_competency_to_dimensions()` maps a
requirement name to 1–2 `Dimension` values via a **9-entry** lookup table
(`ownership`, `problem solving`, `execution`, `judgment`, `knowledge`,
`adaptability`, `system design`, `troubleshooting`, `leadership`), falling
back to `[EXECUTION, PROBLEM_SOLVING]` for anything unrecognised
(`job_fit.py:85`, already flagged in `docs/DEEP_DIVE.md`). This branch reads
the evidence graph correctly and is the mechanism the master context
describes.

**Case B — `SKILL` or `DOMAIN`** (`job_fit.py:131-186`): **plain substring
text search.**

```python
claim_text_lower = claim_text_val.lower()
has_text_mention = req_name_lower in claim_text_lower
...
if req_name_lower in (qa.answer or "").lower() or req_name_lower in (qa.question or "").lower():
    has_qa_mention = True
```

**This is exactly the keyword matching Evident exists to replace**, running
inside the same function that Case A does correctly. It does not touch
`Dimension`, `EvidenceCategory`, or any typed signal — it checks whether a
requirement's name appears as a literal substring in claim text or in a
question/answer pair, then grades `VERIFIED` if that substring also
co-occurred with a `claim_score >= 50`.

**Consequence, concretely:** a JD requirement extracted as
`{"name": "Kubernetes", "category": "SKILL"}` is verified by whether the word
"Kubernetes" literally appears somewhere in the candidate's claim text or
Q&A transcript — not by whether any evidence node, dimension score, or
signal relates to it. A candidate who discussed container orchestration in
different words (or whose extractor spelled it "K8s") gets `MISSING` — the
same false-negative failure mode resume keyword matching has always had.

**Can matching use evidence categories or nodes?** No — neither branch reads
`EvidenceCategory`, `DecisionSignal`, `IncidentMarker`, or any other typed
signal object directly. Case A reads dimension *scores* (an aggregate);
Case B reads raw text.

**Can matching use graph relationships?** Only the FK-shallow relationships
already described in Layer 5 (`claim.qa`, `claim.claim_score`) — there is no
traversal beyond one claim's own attached data; nothing crosses claims, and
nothing crosses candidates (confirmed in `docs/DEEP_DIVE.md`'s indexing
finding).

**Bug found in the process of tracing this** (previously reported in
`docs/DEEP_DIVE.md`, re-confirmed here from the Case A code path):
`job_fit.py:107` — `dp.score if dp.probed or dp.gate_open else 0` —
`DimensionScore` has no `gate_open` attribute
(`schemas.py:292-301`); it's a `signals.py`-internal scoring parameter that
never reached the schema. Reachable whenever any `COMPETENCY` requirement
maps to a dimension with `probed=False` — i.e., routinely, given Layer 1's
finding that `JUDGMENT` is unprobed in 75% of local evaluations. **Both
`POST /api/job-fit` and `POST /api/job-fit/rank` 500 on this input.** Still
unfixed as of this audit.

---

# Section A — Current Architecture

```
                          RESUME
                             │
                    ingest/parse.py
                             │
                 engine/extract.py  [LLM #1]
                (typed claims, ranked, MAX_CLAIMS kept —
                 rejected-at-extraction list is LOGGED, NEVER PERSISTED)
                             │
                             ▼
                     ┌───────────────┐
                     │    claims     │  (table)
                     └───────┬───────┘
                             │
              orchestrator.plan_next()   PURE PYTHON
         qpol_3 (live, default) ── Move enum, 9 members
         qpol_2 (fallback)      ── ProbeLevel enum, 6 members
         v2 EvidenceCategory     ── DORMANT (EVIDENCE_PLANNER_V2=false)
                             │
                    engine/question.py  [LLM #2]
                  wording only → validate() → regenerate → fallback
                             │
                             ▼
                     ┌───────────────┐
                     │   responses   │  raw_text, signals_json (BLOB)
                     └───────┬───────┘
                             │
                    engine/evidence.py  [LLM #3]
              AnswerSignals: 11 typed fields + facts, ALL VERBATIM-VERIFIED
              ── decisions, incidents, constraints, boundaries, causal_links
                 NEVER PROMOTED OUT OF THE BLOB into their own rows ──
                             │
              ┌──────────────┴───────────────┐
              ▼                               ▼
     engine/signals.py                engine/consistency.py
     score_answer() — 6 UCF          session_facts (dedicated table)
     dims ONLY. 6 legacy dims               │
     declared, scored-function-        contradictions (dedicated table)
     written, NEVER CALLED
              │
              ▼
     ┌───────────────┐
     │   evidence    │  (table) — one row per answer × claim × dimension
     │  score, basis,│    quotes_json is a JSON BLOB COLUMN, unindexed
     │  quotes_json  │    beyond (claim_id, dimension)
     └───────┬───────┘
              │
     engine/scoring.py — weights, consistency multiplier
              │
              ▼
     ┌───────────────┐
     │  claim_scores │ ──► graph.recompute_profile() ──► evaluations
     └───────────────┘         (dimension_profile_json,
                                 competence_score, badge)
              │
              ▼
     graph.build_candidate_graph()  — ASSEMBLED AT REQUEST TIME,
     CandidateGraph (Pydantic)        NOT A PERSISTED GRAPH.
                                       No edge table, no node table.
              │
              ▼
     job_fit.verify_requirement_coverage()
        ├─ Case A: COMPETENCY  → Dimension lookup (9 entries)   [graph-based]
        └─ Case B: SKILL/DOMAIN → substring text search          [KEYWORD-BASED]
              │
              ▼
     job_fit.calculate_job_fit()  →  JobFitResult  →  recruiter dashboard

     candidate_outcomes (table, real, append-only, 0 rows in every
     environment measured so far) — collected, NEVER READ BACK into
     scoring. The feedback loop in the master context's Phase 4 vision
     has an inlet and no outlet.
```

---

# Section B — Gap Analysis

| Component | Status | Explanation |
|---|---|---|
| Claim extraction → typed claims | **Complete** | Ranked, typed, verbatim-sourced. Rejected-at-extraction list is computed but not persisted (logged only) |
| Question planning (qpol_3, live) | **Complete** | Pure Python, deterministic, well-tested |
| Evidence Category system (v2) | **Missing (in effect)** | Fully coded, off by default, one category permanently excluded even when on |
| Signal extraction (`AnswerSignals`) | **Complete** | 11 typed fields, verbatim-enforced, all feed live scoring |
| Signal persistence as queryable nodes | **Missing** | Every typed signal lives inside one JSON blob column; none is its own row |
| UCF dimension scoring | **Complete** | Six dimensions, pure functions, well-tested, matches master context exactly |
| Legacy dimension system | **Dead — should be removed, not fixed** | Declared, scored-function-written, zero callers, zero test coverage |
| Evidence Yield instrumentation (`total_signals`) | **Partial** | Undercounts 4 of 11 signal types; relative comparisons still valid, absolute counts are not |
| Evidence Graph — Claim→Evidence→Dimension | **Complete** | The strongest layer in the audit |
| Evidence Graph — persisted/indexed/cross-candidate | **Missing** | Assembled per-request; no search, no traversal beyond one candidate |
| Job matching — competency requirements | **Complete** (shallow lookup table) | Deterministic, graph-based, correctly LLM-free |
| Job matching — skill/domain requirements | **Missing in spirit, present in code** | Substring keyword search — the exact failure mode Evident exists to replace |
| Outcome feedback loop | **Missing** | Table and endpoint exist; 0 rows recorded anywhere; nothing reads it back into scoring |
| Job-fit endpoint reliability | **Broken** | `AttributeError` on any un-probed dimension in a `COMPETENCY` requirement — both job-fit endpoints 500 |

---

# Section C — Recommended Additions

Ordered by priority; complexity and rationale stated for each, per the
instruction to recommend only where a demonstrated gap exists, the addition
improves hiring signal quality, and it preserves evidence-first hiring.

### C1 — Fix `job_fit.py:107`'s `gate_open` crash
- **Why:** two public endpoints 500 on the majority case (any un-probed
  dimension), which per Layer 1's coverage finding is common
- **Problem solved:** restores job matching to working order at all
- **Complexity:** Low (one line + one test)
- **Priority:** **P0**

### C2 — Populate `candidate.seniority` at extraction time
- **Why:** `docs/STATE_MACHINES.md`'s coverage audit traced JUDGMENT's 75%
  non-probe rate to this field being `None` for every candidate measured —
  `Move.AUTHORITY` (the only JUDGMENT-opening move) requires `mid`/`senior`
  and null is blocked, not defaulted open
- **Problem solved:** one-sixth of the Universal Competence Framework is
  currently unreachable for any candidate this pipeline has produced
- **Complexity:** Low–Medium (the classifier output already exists per
  `extract.classify_role`; the gap is wiring it into the stored `Candidate`
  row for sessions that bypass full extraction)
- **Priority:** **P0**

### C3 — Replace Case B's substring search with dimension/signal-based matching
- **Why:** this is the single largest violation of evidence-first hiring
  found in this audit — a live, reachable code path that matches on resume
  keyword presence, inside the product whose reason to exist is "we don't do
  that"
- **Problem solved:** SKILL/DOMAIN requirements (the majority of a typical
  JD's line items — specific tools, technologies, domain terms) currently get
  worse matching than COMPETENCY requirements, for no principled reason
- **Complexity:** Medium — the signal layer already has `tools`
  (`ToolMention`, with a `usage` field distinguishing named-but-unused from
  actually-used) and `concept_explanations`; a SKILL requirement could check
  for a matching `ToolMention.tool` with non-null `usage`, and a DOMAIN
  requirement could check `concept_explanations` instead of raw text
- **Priority:** **P0** — this is the credibility risk, not just a quality gap

### C4 — Promote typed signals out of `responses.signals_json` into their own rows
- **Why:** Layer 4's finding — every `DecisionSignal`, `IncidentMarker`,
  `ConstraintSignal`, `OwnershipBoundary`, `CausalLink` is a real, verified,
  quoted object that is currently unqueryable except by re-parsing a JSON blob
  per response
- **Problem solved:** this is the actual prerequisite for the master
  context's Phase 2 (Evidence-Based Search) and Phase 3 (graph-to-graph
  matching) — "find candidates who personally solved X" cannot be built while
  every "X" lives inside an opaque blob column
- **Complexity:** High — new tables (or a denormalised search index),
  migration path (no Alembic per `CLAUDE.md` rule 7, so this is a
  `create_all()`-compatible additive schema change plus a backfill script),
  and a decision on whether `evidence` absorbs these or a new table set does
- **Priority:** **P1** — high value, but only worth doing once C3 exists to
  consume it, or it's schema built for a query nobody can run yet

### C5 — Fix `total_signals()` to count all eleven `AnswerSignals` fields
- **Why:** every evidence-yield measurement in this project (`studies/
  evidence_yield/`, `studies/coverage_and_yield/`) is built on a function
  that silently drops `decisions`, `constraints`, `boundaries`, and
  `concept_explanations`
- **Problem solved:** makes "evidence yield" mean what its name says;
  currently a documented undercount with no warning anywhere it's used
- **Complexity:** Low (one function, but re-run every study that depended on
  the old number to see if any conclusion moves)
- **Priority:** **P1**

### C6 — A `RiskSignal` type, only if a product owner confirms it's wanted
- **Why:** named explicitly in the requested audit as a target category;
  genuinely absent, not merely dormant like Decision/Incident/Constraint
- **Problem solved:** if risk-awareness is meant to be part of Judgment or
  Adaptability, it currently contributes nothing distinguishable from a
  generic decision or constraint
- **Complexity:** Low if modeled as one more `AnswerSignals` field (same
  pattern as the existing eleven); the actual work is prompt and rubric design
  for what "risk reasoning" should mean, which is a product decision, not an
  engineering one
- **Priority:** **P2** — no evidence this is costing hiring signal quality
  today; it's a gap only in the sense of "the requested category doesn't
  exist," not "candidates are being mis-scored for lack of it"

### C7 — Retire the six legacy `Dimension` members and their dead scoring functions
- **Why:** zero callers, zero test coverage, and they occupy half the enum a
  new reader has to parse before understanding which six actually matter
- **Problem solved:** removes a specific, traceable source of the exact
  confusion this audit was commissioned to resolve
- **Complexity:** Low (delete six functions, six enum members, and their
  entries in `GAP_HINTS`/`MOVE_DIMENSIONS`/`PROBE_LEVEL_DIMENSIONS`) —
  **but touches `api/schemas.py`, which `CLAUDE.md` rule 2 says is frozen and
  any change is "a conversation, not a solo decision."** This is a removal,
  not an addition, and is flagged here only because Layer 1 surfaced it;
  it needs the same two-owner conversation any schema change does
- **Priority:** **P2** — real but purely a maintenance-cost fix, not a
  hiring-signal-quality fix

**What I am not recommending, and why:** a `TradeoffSignal` as a distinct
type from `DecisionSignal` — the keyword-weighted approach already in
`_is_strong_decision()` answers the same question ("was this a real
trade-off or a simple choice") without a new structure, and splitting it out
would be complexity without a demonstrated gap in signal quality.

---

# Section D — Final Verdict

**1. Are the six UCF dimensions sufficient?**
As a *taxonomy*, yes — nothing in this audit found a competence question the
six dimensions structurally cannot represent. As a *measured* system, no: one
of six (JUDGMENT) is unreachable for 75% of the local corpus for a data-flow
reason (C2), and a second (PROBLEM_SOLVING) is frequently zero for an
extraction-completeness reason. The dimensions are sufficient; the pipeline
that fills them is not yet reliably doing so.

**2. Are evidence categories sufficient?**
The ten in `EvidenceCategory` cover eight of the ten requested well
(Decision, Metric Definition, Constraint, Incident, Causal Chain, Ownership
Boundary are all real and mostly live through the parallel Move system; Cross
Claim Link exists but is triple-gated to non-functional). Tradeoff and Risk
are not represented as categories. More urgently: **the entire formal category
system is off by default**, so "sufficient" has to be answered against
what's actually running (the nine-member `Move` enum), which covers the same
ground under different names, adequately.

**3. Are signals sufficient?**
Broadly yes for what they're asked to measure — eleven typed, verbatim-quoted
fields covering quantities, process, causation, tools, metrics, incidents,
decisions, constraints, ownership, concepts, and entities is a reasonable
signal vocabulary. Two concrete defects: the yield-counting bug (C5) and the
complete absence of anything for risk reasoning (C6).

**4. Are evidence nodes sufficient?**
No — this is the weakest layer relative to what the master context claims for
it. The typed nodes exist in `schemas.py` but not in `models.py`. Everything
richer than a dimension-level score is trapped in a JSON blob per response.
"Sufficient for computing a competence score today" — yes. "Sufficient for
the evidence graph to be the company's IP, as the master context states" —
no, because IP that can't be queried, searched, or reused across candidates
isn't yet distinguishable from a very well-organized cache.

**5. Top 5 missing pieces preventing Evident from becoming an evidence-based hiring engine**, ranked by how directly each blocks the master context's own stated vision:

1. **Job matching for SKILL/DOMAIN requirements is keyword search** (C3).
   This is not a missing feature — it's a live contradiction of the product's
   core claim, sitting in the same function that does the graph-based
   version correctly.
2. **Evidence nodes have no persistence beyond a JSON blob** (C4). Blocks the
   master context's own Phase 2 (Evidence-Based Search) and Phase 3
   (graph-to-graph matching) outright — neither can be built against data
   that isn't queryable.
3. **The outcome feedback loop has an inlet and no outlet.** Collected,
   never read back. Blocks Phase 4 (Hiring Intelligence Layer) at the root —
   there is nothing to learn from yet, and nothing built to learn from it if
   there were.
4. **JUDGMENT is structurally unreachable for most candidates measured so
   far** (C2). A framework claiming universal competence measurement has one
   dimension that silently fails for a data-flow reason unrelated to the
   candidate.
5. **The job-fit endpoint crashes on the common case** (C1). Not
   architectural, but it means the matching layer — the "bridge between
   Evident and recruiter ROI," in the prior audit's own framing — does not
   currently work at all for a JUDGMENT-relevant requirement against a
   partially-probed candidate, which per finding #4 is most of them.

None of these require a new architectural layer. All five are fixes,
completions, or removals inside layers that already exist — which is
consistent with `docs/EXECUTION_STANDARD.md`'s standing rule that the
architecture is correct and the implementation should fit inside it.
