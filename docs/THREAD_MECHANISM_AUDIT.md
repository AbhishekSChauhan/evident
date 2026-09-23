# Thread Mechanism Audit

**Scope, strictly:** understand the phenomenon. No redesign, no
implementation proposal, no scoring critique — just what `thread` actually
does, on what it fires, what it produces, and why. This audit reads code and
all 30 real `thread` turns in the corpus directly; nothing here is inferred
from aggregate statistics alone.

**Dataset:** the same 39 real (`llm_mode=live`) candidates,
`studies/evidence_export_prod/00_full_dataset.json` — 30 `thread` turns
total, 14.2% of all 212 real questions. Every question/answer pair quoted
below is verbatim.

---

## 1. What exactly is thread following?

**The mechanism, read directly from code — it is simpler than its yield
suggests.** `_thread_plan()` (`orchestrator.py:2125-2172`) is, in its own
comment, **"Hackathon demo: planner priority 1 (answer threading), ahead of
everything `plan_next_forensic` does."** It fires only when
`settings.demo_mode` is on, only immediately after a claim's first answer
(`state.answers == 1`), and it does exactly one thing:

1. Takes the **previous answer's raw text** (the parent answer, no matter
   which move produced it).
2. Runs `detect_thread_entity()` (`question.py:804-821`) — a **word-boundary,
   case-insensitive regex scan against a fixed 17-word list**, checked in a
   **fixed priority order**:
   `approval, documentation, metric, dashboard, ticket, jira, release, api,
   customer, report, sdk, library, service, bug, meeting, team, manager`.
   The first word from this list that appears anywhere in the answer wins —
   not the most interesting word, not the most central one, the first one in
   this list that matches at all.
3. Looks that word up in `THREAD_ENTITY_QUESTIONS` (`question.py:783-801`) —
   a **fixed, hand-written, un-templated string per entity**. No model call,
   no interpolation beyond the literal question text. `manager` always
   produces exactly *"What decision authority did you hold versus what
   required your manager's sign-off?"*, verbatim, regardless of anything
   else the candidate said.

**So "what entity was chosen" has one honest answer: whichever of 17 fixed
words happened to appear in the answer, in a fixed priority order that has
nothing to do with that answer's content.** "Why it was chosen" is
positional, not semantic. "What it was trying to expand" is whatever that
one entity's hard-coded question asks for — fixed at authoring time, not
derived from the specific claim or answer.

**Entity distribution actually observed** (30 real firings):

| Entity | Count | Canned follow-up asks for... |
|---|---:|---|
| `report` | 5 | root cause + action taken |
| `api` | 5 | payload/rate-limit/latency constraint |
| `dashboard` | 5 | the specific anomaly that triggered intervention |
| `metric` | 4 | baseline threshold + verification method |
| `approval` | 4 | the criteria/threshold required |
| `team` | 3 | interface boundary / handoff contract |
| `manager` | 2 | decision authority vs. sign-off |
| `ticket` | 1 | boundary of responsibility vs. escalation |
| `customer` | 1 | the constraint/bottleneck presented |

`documentation`, `jira`, `release`, `sdk`, `library`, `service`, `bug`,
`meeting` — **8 of the 17 defined entities never fired once** in 212
questions. The vocabulary that actually matters in practice is a narrower
set of five or six work-artifact nouns (report, api, dashboard, metric,
approval, team).

---

## 2. What evidence types does thread produce, vs. move-generated evidence?

Regex-based content tagging (quantities, causal language, decision language,
constraint language, incident language, process-sequencing words, capitalized
named entities), applied identically to every answer in each group — the
same method, same patterns, no group given special treatment:

| Group | n | Avg words | Quantity (raw) | Causal (raw) | Constraint (raw) | Quantity /100w | Causal /100w | Constraint /100w |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `THREAD` | 30 | **57.7 (longest)** | 0.47 | 0.23 | **0.60 (highest)** | **1.33 (highest)** | 0.44 | **1.00 (highest)** |
| `DEPENDENCY` | 11 | 45.0 | 0.55 | **0.73 (highest)** | 0.00 | 0.33 | **1.05 (highest)** | 0.00 |
| `AUTHORITY` | 14 | 45.1 | 0.43 | 0.21 | 0.21 | 0.96 | 0.28 | 0.54 |
| `FAILURE` | 43 | 36.1 | 0.21 | 0.26 | 0.09 | 0.28 | 0.34 | 0.15 |
| `OPERATING_CONTEXT` | 52 | 29.0 | 0.08 | 0.12 | 0.10 | 0.06 | 0.17 | 0.12 |

Read against the example the brief gave (thread → tools/quantities/entities
vs. `FAILURE` → causal links/incident markers): the data says something more
specific than that split. **Thread does not out-produce `DEPENDENCY` or
`FAILURE` on causal density** — those two moves are still the real causal-chain
specialists, exactly as the prior move-yield audit found. What thread
actually dominates, even normalized for its longer answers, is **constraint
language (highest of any group, nearly double `AUTHORITY`) and quantity
density (highest of any group, ahead of `AUTHORITY`)**. That tracks the
entity vocabulary directly: `metric`, `api`, and `approval` questions are
*built* to ask for a threshold, a limit, or a criterion — constraint content
is what their canned wording is designed to pull, and it does.

(A raw capitalized-word "named entity" count also came out highest for
`OPERATING_CONTEXT`/`FAILURE`, but that is very likely an artifact of those
answers echoing proper nouns the question itself just fed them — e.g. "the
banking platform," "Python, FastAPI, and Django" — rather than a genuine
signal of thread being weaker here; it is reported for completeness, not
relied on.)

---

## 3. Why is thread yield so high?

Walking the top-yield turns (sig ≥ 7) against the six candidate explanations
in the brief:

| Turn | Sig | Specificity | Recency | Concrete entity | Follow-up context | Reduced cognitive load | Natural flow |
|---|---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Chandan KS, `metric` | 10 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Jyoti, `manager` | 9 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Jyoti, `report` | 9 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Jyoti, `dashboard` | 9 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Komal Sharma, `metric` | 9 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| `t`, `api` | 8 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

Every single high-yield turn checks every box **simultaneously**, and that
is the finding: this is not one mechanism among six candidates, it is one
*compound* mechanism that the six candidate explanations are all describing
facets of. Concretely: the thread question always (a) fires on the entity
the candidate **just, this turn, voluntarily said**, so it is maximally
recent; (b) that entity is by construction **concrete** (a named artifact —
report, dashboard, API, metric); (c) the question is explicit **follow-up**
framing ("that report," "that dashboard," "that metric" — deictic reference
back to what was just said); (d) because the candidate is still holding the
same scenario in working memory, answering costs **less retrieval effort**
than being asked to recall a *different* episode (which is what `FAILURE`
and `PERTURB` typically require); and (e) the whole exchange **reads like one
continuous conversation about one thing**, not a topic jump.

**What is not the explanation:** it is not the wording quality of the canned
question in isolation — §4's correlation finding below shows thread yield
tracks the *parent* answer's strength, meaning thread's apparent power is
partly borrowed, not self-generated.

---

## 4. What happens immediately before a successful thread?

**Parent move type and its own yield, by thread outcome:**

| Parent move | n | Avg thread signals that followed |
|---|---:|---:|
| `OWNERSHIP_BOUNDARY` | 1 | 5.00 |
| `OPERATING_CONTEXT` | 14 | 4.93 |
| `PERTURB` | 6 | 4.33 |
| `DEPENDENCY` | 1 | 3.00 |
| `FAILURE` | 4 | 3.25 |
| `AUTHORITY` | 4 | 1.75 |

**Parent answer strength predicts thread strength.** Correlation between the
parent turn's `signals_found` and the following thread turn's
`signals_found` across all 30 pairs: **r = 0.35** (moderate positive).
Bucketed: when the parent answer scored ≥ 5 signals, the thread that followed
averaged **5.05**; when the parent scored < 5, the thread averaged **2.2** —
more than double the yield when the candidate was already engaged.

**The recurring structural pattern, present in every single successful
thread without exception:** Question N asks about the claim in general terms
→ Answer N names one concrete artifact in passing (a report, a metric, an
API, a manager) as part of describing something else → Thread asks a
narrower question about *exactly that named artifact* → Answer N+1 elaborates
on the same artifact, still within the same mental scenario the candidate was
already in. **Thread never introduces a new subject.** Every move in the
formal ladder (`FAILURE`, `PERTURB`, `AUTHORITY` on a *different* claim
aspect) asks the candidate to open a new mental file; thread asks them to
keep reading the one already open.

---

## 5. Is thread collecting new evidence, or merely expanding evidence that already existed?

Close reading of all 30 pairs, classified by what the thread answer actually
added relative to its parent:

| Category | n | What it looks like |
|---|---:|---|
| **New evidence** | ~12 | A specific fact appears that was not stated or implied anywhere in the parent. Clearest case: `t`/`api` — parent says only "an external API"; thread reveals concrete numbers (1 MB payload limit, ~100 req/min, <500 ms) and a named mitigation (pagination, batching, backoff) that did not exist in the parent at all. |
| **Expanded/decompressed evidence** | ~8 | The parent already contained the substance; the thread mostly re-states it with modest added detail. Clearest case: Ayush/`report` — the parent already gave the full causal chain (feature-importance leak check → funnel-stage bug → database type bug); the thread answer restates the same chain, adding one further mechanism detail (silent string-vs-number comparison failures). |
| **Hedged / possibly invented** | ~4 | The candidate explicitly signals they are not recalling a real fact but constructing a plausible one on the spot: *"The exact threshold isn't specified in the project details. I would establish it as..."* (Chandan KS, sig=10 — one of the **highest-scoring turns in the whole set**); *"There wasn't a specific threshold mentioned in the role... depended on..."* (Renuka Malhotra). |
| **Dead / misfire** | ~6 | The keyword matched, but the follow-up doesn't fit what the parent was actually about. Manya/`process_work`, told to describe an `api` constraint after a parent answer about an *async race condition*, replies: *"You just asked me the same question."* Manvi/`performance_work`'s parent already said *"I mostly worked on the front end... I am not really aware of the back end architecture"* — the fixed template asks about API architecture constraints anyway, regardless of that disclaimer, and gets a restated "not aware." |

**The important, and slightly uncomfortable, finding is in the "hedged"
row.** Thread has no way to tell the difference between a candidate
recalling a real number and a candidate constructing a plausible-sounding one
under a confident, first-person, technically-fluent register — and the
scoring pipeline, per the earlier methodology audit's `EC1` finding, cannot
either. Chandan KS's highest-scoring thread turn in this entire sample is
built entirely from a sentence that opens by admitting the number isn't
real. That is not a defect unique to thread — it's the same fluent-confident-
answer gap found everywhere else in this system — but thread's design
(always asking for a *quantified threshold* the parent conversation never
established) may be structurally more likely to invite it than a move that
asks about something the candidate already stated happened.

**Net read:** thread does both. It is not "merely" expanding — 12 of 30 turns
introduce facts genuinely absent from the parent. But roughly a third of the
sample (expanded + hedged) is decompressing or embellishing content that was
already, in substance, on the table, and a further fifth is a keyword-match
misfire that produces no real evidence either way.

---

## 6. What dimensions would thread have opened, if dimensions were credited?

**Two different answers here, and the gap between them is itself a finding.**

**(a) What the canned question, by its content, is actually built to
elicit** — a clean, deterministic mapping, since each entity has exactly one
fixed question:

| Entity | Content it pulls | Dimension(s) it targets by design |
|---|---|---|
| `manager`, `approval` | decision rights vs. sign-off / criteria for approval | **JUDGMENT** (decision + constraint), OWNERSHIP |
| `report`, `dashboard` | root cause of an anomaly + the fix | **PROBLEM_SOLVING**, EXECUTION |
| `api`, `metric` | technical constraint / measurement baseline | **KNOWLEDGE**, EXECUTION |
| `team`, `ticket` | interface boundary / handoff contract | **OWNERSHIP** |

**(b) What actually gets persisted as evidence today**, from the real stored
per-response record: because `_thread_plan()` inherits `probe_level` from
the *parent* question (`orchestrator.py:2162-2167`: `probe_level =
ProbeLevel(question.probe_level)`) rather than deriving one from the thread
question's own content, and per the prior `Dimension Opening Audit`'s
finding that per-response evidence is persisted by `probe_level`, not by
move or content — the dimensions actually credited to these 30 turns are:

| Dimension credited (persisted) | Count (of 30 turns) |
|---|---:|
| EXECUTION | 20 |
| KNOWLEDGE | 19 |
| ADAPTABILITY | 16 |
| PROBLEM_SOLVING | 9 |
| JUDGMENT | 9 |
| OWNERSHIP | 7 |

This is a visible mismatch: a `manager`-entity thread question asking "what
decision authority did you hold versus your manager's sign-off" — content
that is JUDGMENT and OWNERSHIP by any human reading — gets persisted-credit
determined by whatever probe level its *parent* question happened to carry
(most often `OPERATIONAL`, inherited from an `OPERATING_CONTEXT` parent,
which routes to EXECUTION/KNOWLEDGE-flavored credit, not JUDGMENT). The
content and the credit are frequently talking about different dimensions.

**One further, structurally verified fact worth stating precisely:**
`detect_thread_entity()` and `_thread_plan()` contain **no seniority check
anywhere** — unlike `AUTHORITY` and `EXCLUSION`, which are explicitly
blocked for junior/unknown-seniority candidates via `LEVEL_RESTRICTED`. In
this 30-turn sample, junior candidates received 10 of the 30 thread turns
(33%) on other entities (`dashboard`, `report`, `customer`, `api`, `metric`),
demonstrating the mechanism does fire for junior candidates in general; no
junior candidate happened to trigger `manager` or `approval` specifically in
this sample, so the strongest version of this claim — that thread is already
delivering JUDGMENT-flavored evidence to candidates the seniority gate would
otherwise block from ever producing it — is **verified in the code, not yet
directly observed in this data.** It would take only one junior candidate
saying the word "manager" to trigger it, and nothing in the code would stop
that from happening.

---

## Final answer

> Is thread a hackathon shortcut that happens to work, or is it revealing a
> superior evidence collection strategy that the formal planner currently
> misses?

**Both, and they are not in tension.** The *mechanism* is unambiguously a
shortcut: a 17-word fixed vocabulary, a hand-written un-templated question
per word, zero model calls, zero semantic understanding, gated behind
`demo_mode`, given top planning priority "ahead of everything
`plan_next_forensic` does," and — per §4 and §5 — riding substantially on
whatever momentum the *parent* answer already had rather than generating
evidence from nothing. It is not solving the general problem in any deep
sense; it works only because its 17-word vocabulary happens to catch common,
concrete, work-artifact nouns.

But the *principle it stumbles into* is real, and the formal Move ladder does
not currently encode it as a first-class move. Every high-yield thread turn
is doing the same thing: stay on the exact topic the candidate just,
voluntarily, opened, and ask for the one specific hard-to-fake detail
(a threshold, a root cause, a boundary) that was implied but not yet stated —
with zero cost to switch context, because there is no context switch. The
closest analog in the formal system, `COHERENCE`, requires two *independent*
established facts and never fired once in 212 real questions
(`DIMENSION_OPENING_AUDIT.md` §1); nothing in the formal ladder currently
does "immediately deepen the thing you just said" as cheaply and reliably as
`thread` does by accident. Whether that principle is worth building
properly — with real dimension crediting, a seniority-aware design, and
guardrails against the hedged/invented-answer risk found in §5 — is a
question for the next audit, not this one; this one's job was only to
establish that the phenomenon is real, and that it is not the same
phenomenon as "the fallback path is fine," which is what its name suggests.
