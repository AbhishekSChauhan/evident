# Deep dive — schema, data shapes, one real trace, and priorities

**Companion to [CURRENT_STATE.md](CURRENT_STATE.md).** Everything here was read
out of the working tree at `2659f20` or queried from the local
`proofscreen.sqlite3`. The trace in §3 is a real candidate, not an illustration.

---

# 1. Database schema — the five entities that matter

16 tables. 15 carry `tenant_id`. IDs are short prefixed strings (`c_`, `cl_`,
`q_`, `r_`, `e_`, `ev_`), not UUIDs, because on demo day you read them aloud.

## 1.1 Candidate — `models.py:155`

```python
id           String(32) PK          # c_b90f6b
tenant_id    String     indexed
name         String(200)
phone        String(40) indexed     # the WhatsApp binding key
email        String(200)
role         String(200)            # free text off the resume
job_family   String(60) indexed     # routed by taxonomy.detect_family
seniority    String(20)             # junior/mid/senior, gates move selection
role_id      FK job_roles SET NULL  # the lens, not the job
created_at   datetime
```

**Scaling note.** `phone` is indexed and is the real identity key on the
WhatsApp path. There is **no unique constraint on `phone` or `email`**, so the
same person applying twice is two candidate rows with two evidence graphs.
Identity resolution does not exist. That is fine at 10 recruiters and is a
correctness problem at 1,000.

## 1.2 Claim — `models.py:217`

```python
id            String(32) PK         # cl_99ebd5
tenant_id     String
resume_id     FK resumes   CASCADE indexed
candidate_id  FK candidates CASCADE indexed
text          Text                  # the resume bullet, verbatim
claim_type    String(60) indexed    # typed against the taxonomy
metric        String(200)           # "78% -> 92%", or None
order_index   Integer               # interview order, strongest first
created_at    datetime
```

A claim is a **resume assertion**, not a fact. It is the thing evidence is
gathered *about*.

## 1.3 Evidence — `models.py:328` — the one that decides graph traversal cost

```python
id           String(32) PK
tenant_id    String
response_id  FK responses CASCADE indexed   # which answer produced it
claim_id     FK claims    CASCADE indexed   # which claim it supports
dimension    String(24)                     # one of the six
score        Integer                        # 0-100 for that dimension
basis        String(400)                    # "• Executed step: ..."
quotes_json  Text                           # verbatim, verified
probe_level  String(20)
created_at   datetime

Index("ix_evidence_claim_dimension", claim_id, dimension)
```

**Grain: one row per (answer × claim × dimension).** This is the right grain and
it is genuinely good design — `basis` and `quotes_json` together mean every
number on the dashboard can be traced to a sentence the candidate said, which is
the explainability commitment made concrete.

**Where it will hurt.** There is exactly one composite index, and it is
`(claim_id, dimension)`. Every access path in the product today starts from a
candidate and walks down. There is **no index that starts from `dimension`, from
`tenant_id`, or from the content of `quotes_json`**. So:

| Query | Today |
|---|---|
| "evidence for this candidate" | Fast — indexed, and what the product does |
| "all candidates with OWNERSHIP ≥ 70" | Full scan of `evidence` joined up to `candidates` |
| "who has personally solved scaling above 1M req/day" | **Impossible** — that lives in `quotes_json` as free text with no index |

Long-Term Vision Phase 2 (evidence search) is blocked on exactly this, and the
fix is additive: a denormalised search table or a tsvector/embedding index over
quotes, keyed by `(tenant_id, dimension)`. **No existing table needs to change.**

## 1.4 Evaluation — `models.py:446` — the immutable record

Three groups of columns:

**Result** — `resume_score`, `weighted_evidence_score`, `competence_score`,
`badge`, `consistency_score`, `contradiction_count`, `role_coverage`,
`claims_scored`, `questions_asked`, `dimension_profile_json`.

**Configuration it was produced under** — `claim_weights_json`,
`dimension_weights_json`, `taxonomy_version`, `taxonomy_hash`, `rubric_version`,
`scoring_version`, `question_policy_version`, `prompt_versions_json`,
`code_version`, `app_version`, `llm_mode`, `model_requested`, `model_returned`,
`feature_flags_json`, and `evaluation_version` (a hash of the material).

**Pointers** — `candidate_id`, `session_id` (UNIQUE), `role_id` (SET NULL).

Three decisions worth defending:

- **No evidence is copied in.** `session_id` and `candidate_id` address the
  graph that already exists. Copying evidence would create a second source of
  truth for the one thing this product cannot afford two answers about.
- **Weights ARE copied.** `role_id` is SET NULL on delete, so without the
  snapshot a deleted lens would make a finalized evaluation unexplainable.
- **`model_returned` is recorded and NOT hashed.** It is a per-process
  observation; hashing it would make an evaluation's identity depend on whether
  anyone made a live call in that process.

**Immutability is enforced at the ORM layer** by a `before_update` listener
(`models.py:623`), not in the service function — it catches a future callsite
that never heard of the service function. The listener tests the *old* value of
`finalized_at`, because the flush that performs finalization is itself an update.

## 1.5 CandidateOutcome — `models.py:551` — the row that makes the product falsifiable

```python
id                 String(32) PK
tenant_id          String
candidate_id       FK candidates CASCADE indexed
role_id            FK job_roles  SET NULL       # never CASCADE
decision           String(20) indexed           # ordinal, worst to best
evaluation_id      FK evaluations SET NULL indexed
previous_decision  String(20)
stage, decided_by, note, decided_at

Index(candidate_id, decided_at)
```

**Append-only by shape, not by comment.** There is deliberately no unique
constraint on `candidate_id` — a candidate moves shortlisted → interviewed →
offered and each step is a new row. `create_all()` cannot express a trigger, so
the guarantee is structural and pinned by `test_outcome_rows_are_append_only`.

`role_id` is SET NULL because deleting a scoring lens must not delete the record
that a person was rejected. The decision happened; the lens is only context.

**Rows in every environment today: 0.**

---

# 2. Evidence extraction — the actual data shape

## 2.1 `AnswerSignals` — LLM call #3 output. Counts in, no scores out.

Eleven signal lists plus facts. **Every one carries a `quote`**, and
`evidence.enforce_verbatim()` drops any signal whose quote is not literally
present in the answer text.

| Signal | Fields | Opens which gate |
|---|---|---|
| `quantities` | `value`, `refers_to`, `quote` | SPECIFICITY, METRIC_OWNERSHIP |
| `process_steps` | `step`, `quote` | EXECUTION, PROCESS |
| `causal_links` | `cause`, `action`, `outcome`, `quote` | CAUSAL_REASONING. **Partial chains score half** |
| `tools` | `tool`, `usage`, `quote` | TOOL_FAMILIARITY — usage, not certification |
| `metric_definitions` | `metric`, `how_measured`, `quote` | KNOWLEDGE, METRIC_OWNERSHIP |
| `incident_markers` | `detail`, `quote` | AUTHENTICITY, PROBLEM_SOLVING |
| `decisions` | `choice`, `reason`, `quote` | JUDGMENT |
| `constraints` | `limitation`, `effect`, `quote` | JUDGMENT |
| `boundaries` | `scope_held`, `scope_handed_off`, `quote` | OWNERSHIP |
| `concept_explanations` | `concept`, `explanation`, `quote` | KNOWLEDGE |
| `entities` | named people/systems | AUTHENTICITY |
| `facts` | `key`, `value_num`, `value_text`, `unit`, `quote` | **Not scored** — this is consistency memory |

**Note the shape you asked about does not exist.** There is no
`{signal_type, quote, dimension, weight}` record. The design is deliberately
different: **the model emits typed observations with no dimension and no
weight**, and `signals.py` decides which dimensions each type opens and what it
is worth. That is CLAUDE.md rule 1 made structural — if the model emitted a
`dimension` or a `weight`, it would be scoring.

The `{dimension, score, basis, quotes}` record you were expecting is the
**output** of that mapping: `DimensionScore` (`schemas.py:292`) and the
`evidence` table row.

## 2.2 Real payload — response `r_e32c6d`, heuristic extractor

Answer: *"Billing complaints were about 40% of our negative feedback, so we
redesigned the escalation workflow and introduced callback SLAs, and CSAT moved
from 78 to 92 over about eleven weeks."*

```json
{
  "quantities": [
    {"value": "40%",          "refers_to": "Billing complaints were about 40% of our negative feedb", "quote": "<full sentence>"},
    {"value": "78",           "refers_to": "uced callback SLAs, and CSAT moved from 78 to 92 over ",  "quote": "<full sentence>"},
    {"value": "92",           "refers_to": "allback SLAs, and CSAT moved from 78 to 92 over about ",  "quote": "<full sentence>"},
    {"value": "eleven weeks", "refers_to": "eleven weeks",                                            "quote": "<full sentence>"}
  ],
  "process_steps": [
    {"step": "Billing complaints were about 40% of our negative feedback, so we redesigned...", "quote": "<full sentence>"}
  ],
  "causal_links": [
    {"cause": "Billing complaints were about 40%...", "action": "Billing complaints were about 40%...", "outcome": null, "quote": "<full sentence>"}
  ]
}
```

**Read the quality, not just the shape.** This is the *heuristic* extractor
(`llm_mode: fixture`), and it is visibly shallow:

- `refers_to` is a truncated substring of the sentence, not the referent
- `process_steps.step` is the whole sentence rather than a step
- `causal_links.cause == action`, and `outcome` is `null` — so the chain is
  partial and scores half, on an answer that plainly contains a complete
  cause → action → outcome

That is the fallback working as designed — CLAUDE.md says heuristics are
deliberately more conservative than real extraction. **But every one of the 8
evaluations in the local database is `llm_mode: fixture`.** No evaluation
anywhere in this repo has been produced by the real extractor.

---

# 3. One real candidate, end to end

**Priya Raghavan — `c_b90f6b`, session `s_e2f6dbb136`, evaluation
`ev_ea303895ff`.** Fixture mode, `qpol_3`, 6 questions, COMPLETE.

## Resume (436 chars)

```
Priya Raghavan - Support Operations Team Lead, Bengaluru
EXPERIENCE  Team Lead, Northwind Services
- Managed a team of 35 agents across 4 pods with 4 senior associates reporting to me
- Improved CSAT from 78% to 92% in four quarters by redesigning the escalation workflow
- Reduced AHT from 480 seconds to 430 seconds by rewriting the call opening scripts
SKILLS  Escalation design, workforce planning, coaching, Genesys
```

## → Claims (`extract.py`, LLM #1; family routed to `bpo_operations`)

| id | claim_type | metric | text |
|---|---|---|---|
| `cl_2b31c5` | `team_handling` | `35` | Managed a team of 35 agents across 4 pods… |
| `cl_99ebd5` | `csat_improvement` | `78% -> 92%` | Improved CSAT from 78% to 92%… |
| `cl_68e8cc` | `aht_control` | **`480`** | Reduced AHT from 480 seconds to 430 seconds… |

> **The third metric is wrong, and it is a known bug caught in the wild.**
> It should read `480s -> 430s`. `extract._metric_of` has no seconds unit —
> `_UNIT` covers `ms` and `minutes` but not `s`/`sec`/`seconds` — so the range
> collapses to its first number. Seconds is the unit BPO measures AHT in.
> Documented in CLAUDE.md; here is a live instance.

## → Questions and answers

| # | claim | probe | move | source | answer (truncated) | signals |
|---|---|---|---|---|---|---|
| 0 | team | OPERATIONAL | OPERATING_CONTEXT | fallback | *"I had 35 agents in four pods… daily attendance tracking and a weekly calibration"* | 8 |
| 1 | team | OPERATIONAL | — | thread | *"Every morning I pulled the queue report, then a fifteen minute huddle, then reviewed escalations…"* | 5 |
| 2 | CSAT | INCIDENT | FAILURE | fallback | *"Billing complaints were about 40%… CSAT moved from 78 to 92 over about eleven weeks"* | 9 |
| 3 | CSAT | OUTCOME | METRIC_DEFINITION | fallback | *"CSAT is measured from the post-interaction survey, percentage of 4 and 5 ratings…"* | 5 |
| 4 | AHT | TRANSFER | PERTURB | fallback | *"AHT came down a bit… but I don't have the exact numbers in front of me now."* | **0** |
| 5 | AHT | INCIDENT | PEOPLE | fallback | *"I don't remember the details of how we measured it."* | **0** |

**Five of six questions came from the deterministic fallback** with
`violations_json = ["model_unavailable"]` — this run had no API key. Question 1
is a `thread` follow-up. The last two answers hit memory exhaustion and were
correctly scored 0 without a repair turn and without penalty.

## → Evidence rows (claim `cl_99ebd5`, CSAT)

| dimension | score | probe | basis | quote |
|---|---:|---|---|---|
| EXECUTION | 50 | INCIDENT | • Executed step: Billing complaints were about 40%… | ✓ |
| KNOWLEDGE | 13 | INCIDENT | • Domain process mechanics: … | ✓ |
| ADAPTABILITY | 30 | INCIDENT | • Prospective reasoning: … | ✓ |
| PROBLEM_SOLVING | **0** | INCIDENT | **• Capped at 45: no incident marker or causal chain provided** | — |
| EXECUTION | 40 | OUTCOME | • Executed step: I reviewed it in Zendesk every Monday… | ✓ |
| KNOWLEDGE | 30 | OUTCOME | • Defined metric computation: CSAT (…percentage of 4 and 5 ratings…) | ✓ |
| OWNERSHIP | 17 | OUTCOME | • Owned operational action: … | ✓ |

The `PROBLEM_SOLVING` row is the gate mechanism visible: the question was an
INCIDENT probe, the answer described a *fix* but named no incident and closed no
causal chain, so the gate stayed shut and the basis says exactly why.

## → Claim scores (union of answers, rubric run once)

| claim | score | probed_dimensions | answers |
|---|---:|---:|---:|
| `cl_2b31c5` team | 36 | 3 | 2 |
| `cl_99ebd5` CSAT | 27 | 5 | 2 |
| `cl_68e8cc` AHT | **0** | 2 | 2 |

## → Dimension profile and evaluation

| dimension | score | signals | probed |
|---|---:|---:|---|
| KNOWLEDGE | 26 | 5 | ✓ |
| EXECUTION | **67** | 5 | ✓ |
| PROBLEM_SOLVING | 0 | 0 | ✓ |
| JUDGMENT | 0 | 0 | **✗ never probed** |
| OWNERSHIP | 26 | 4 | ✓ |
| ADAPTABILITY | 10 | 1 | ✓ |

```
competence_score        24        evaluation_version  evx_6b9f91639f7340a5
weighted_evidence_score 24        taxonomy            tax_1 / ff71094e8670
resume_score            28        question_policy     qpol_3
consistency_score      100        code_version        2659f20ebe39
contradictions           0        llm_mode            fixture
role_coverage           60        status              finalized
```

> **The demo narrative does not survive this data.** Priya is the "worst resume,
> real competence" persona. Here she scores **competence 24 against resume 28** —
> the inversion runs the wrong way. In a 6-question interview two answers were
> memory-exhausted and `JUDGMENT` was never probed at all, so a third of the
> framework contributed zero. See [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md)'s warning.

## → Job fit — **this stage raises an unhandled exception**

Against a real JD (*"ownership of a support team, troubleshooting, escalation
design, judgment under load, Genesys, CSAT and AHT"*):

**Step 1 — requirement extraction (heuristic path) produced three requirements:**

```
'Ownership'        COMPETENCY w=0.33 -> ['OWNERSHIP']
'Problem Solving'  COMPETENCY w=0.33 -> ['PROBLEM_SOLVING']
'Judgment'         COMPETENCY w=0.33 -> ['JUDGMENT']
```

Genesys, escalation design, troubleshooting, CSAT and AHT were **all dropped**.
The heuristic extractor recognises only generic competency words and discards
the domain content of the JD.

**Step 2 — `calculate_job_fit(graph, reqs)` crashes:**

```
File "api/engine/job_fit.py", line 107, in verify_requirement_coverage
    dim_scores.append(dp.score if dp.probed or dp.gate_open else 0)
AttributeError: 'DimensionScore' object has no attribute 'gate_open'
```

**`DimensionScore` has no `gate_open` field.** It has `dimension`, `score`,
`signal_count`, `basis`, `quotes`, `probed` (`schemas.py:292`). `gate_open` is a
**local parameter inside `signals.py`** scoring helpers and never reaches the
model.

- **Trigger:** any COMPETENCY requirement whose mapped dimension has
  `probed=False`. Python short-circuits `or`, so a fully-probed candidate never
  evaluates the attribute — which is why this has not been seen.
- **Reachable from:** `POST /api/job-fit` (`routers/job_fit.py:95`) and
  `POST /api/job-fit/rank` (`:114`). Both return 500.
- **Why 7 tests pass:** `tests/test_job_fit.py:59` builds every `DimensionScore`
  with `probed=True` and line 89 sets `probed_dimensions=6`. **The un-probed
  branch is not covered by any test.**
- **Fix:** one line — drop ` or dp.gate_open`, or `getattr(dp, "gate_open", False)`
  if the gate reading is meant to be surfaced. Then add a test with an un-probed
  dimension.

Priya has `JUDGMENT probed=False` and the JD asks for judgment. **A real
recruiter with a real JD hits this immediately.**

---

# 4. Priorities — next 8 weeks

Brutally honest, as asked.

> **The frame that decides your question.** This is not an architecture problem.
> The architecture is good — arguably over-built for the stage. There are 532
> tests, ORM-level immutability, replay with zero model calls, provenance
> hashing, and multi-tenancy with AST tests. What there is **not** is a single
> real user, a single live model call in the stored data, a single outcome row,
> or a single deploy.
>
> **Help as a startup product advisor, not as an architect.** The next eight
> weeks should add almost no architecture.

## P0 — weeks 1–3. Without these there is no product, only a repo.

| # | Item | Why now | Est. |
|---|---|---|---|
| **P0.1** | **Fix the job-fit crash** (§3) | Two endpoints 500 on a normal input. It is one line plus one test | 1 h |
| **P0.2** | **Ship one real interview through Meta** | The candidate channel has never run against the real API. Template approval is an external clock — start it on day 1 | 3 d + waiting |
| **P0.3** | **Deploy, with `REQUIRE_API_KEY=true`** | Nothing has run outside a laptop. Auth defaults to off, so shipping without flipping it publishes an open endpoint | 2 d |
| **P0.4** | **Produce 10 evaluations with `llm_mode: live`** | Every stored evaluation is fixture-mode. You do not know what the real extractor produces at the end of the pipeline | 1 d |
| **P0.5** | **DPDP baseline** — consent record, retention, deletion | Legal exposure, and it gates every conversation with a real employer | 1 w |

## P1 — weeks 4–6. Without these it does not survive contact with a recruiter.

| # | Item | Why | Est. |
|---|---|---|---|
| **P1.1** | **Get 30 outcome rows** | `candidate_outcomes` is empty in every environment. Until it is not, "evidence beats resume screening" is an assertion. The table, endpoint and report all exist | usage, not build |
| **P1.2** | **Fix JD requirement extraction** | The heuristic path dropped 5 of 8 requirements and kept only generic competency words. Check whether the LLM path is materially better — nobody has looked | 3 d |
| **P1.3** | **Widen `COMPETENCY_MAP` past 9 entries** | Everything unmatched maps to `[EXECUTION, PROBLEM_SOLVING]`, so fit scores cluster and ranking stops discriminating | 2 d |
| **P1.4** | **Raise questions-per-interview, or fix coverage** | Priya's interview never probed JUDGMENT and burned 2 of 6 turns on exhausted memory. A third of the framework contributed zero | 2 d |
| **P1.5** | **Fix `_metric_of` seconds** | `480s -> 430s` becomes `480`. Seconds is the unit BPO measures AHT in, and BPO is the beachhead | 2 h |
| **P1.6** | **Update CLAUDE.md** | It says the dashboard is not done. It is. Stale context makes every session start wrong | 1 h |

## P2 — weeks 7–8. Start only if P0 and P1 are genuinely done.

| # | Item | Depends on |
|---|---|---|
| **P2.1** | Evidence search index — denormalised table keyed `(tenant_id, dimension)` over quotes | Nothing. Additive, no existing table changes |
| **P2.2** | Real auth: users, sessions, roles | Nothing. Required before any enterprise conversation |
| **P2.3** | Measure the live question generator (`qpol_3`) | Nothing. ≈$3.67 |
| **P2.4** | Candidate identity resolution on `phone` | Nothing. Cheap now, expensive later |

## Explicitly not in the next 8 weeks

- **Graph-to-graph matching.** Both sides need modelling as evidence; neither is.
- **Outcome-informed weight calibration.** At n = 0 it fits noise. At n = 30 it
  still does.
- **A second channel.** WhatsApp has not survived one live conversation.
- **Any new abstraction, module or layer.** `EXECUTION_STANDARD.md` §1 forbids it
  without approval, and nothing on this list needs one.
