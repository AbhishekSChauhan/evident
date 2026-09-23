# Question Quality Audit — Wording Patterns Within the Six Highest/Lowest-Yield Moves

**Scope, strictly:** given the same move, what did the actual generated
question say, and does its specific wording correlate with strong or weak
evidence? No planner redesign, no implementation, no scoring mechanics —
those are covered in the three prior audits. This one reads the text.

**Dataset:** all 129 real questions (`llm_mode=live`) for the six moves named
in the brief, pulled from `studies/evidence_export_prod/00_full_dataset.json`
— `AUTHORITY` (14), `DEPENDENCY` (11), `OWNERSHIP_BOUNDARY` (6),
`OPERATING_CONTEXT` (52), `FAILURE` (43), `METRIC_DEFINITION` (3). Every
question below is quoted verbatim; "high-evidence" and "low-evidence" are
defined by the turn's actual stored `signals_found`, not by inference.

**One honesty check applied throughout:** a chunk of the lowest-signal turns
across every move are not wording failures at all — they're answers like
*"Hhhh"*, *"Fdr"*, *"Ufoufoy"*, *"Kktso"*, *"Obrigado."*, *"."* — disengaged
or garbled responses that no rewording would rescue. These are flagged
separately from genuine wording-caused low yield everywhere they appear, so
the pattern analysis below isn't crediting or blaming phrasing for noise it
didn't cause.

---

## AUTHORITY (n = 14)

**Dominant template:** *"What decisions could/were you able to make
independently, and which [ones] required input/approval from others?"* — a
paired two-clause structure, matching `MOVE_BRIEFS[AUTHORITY]`'s own
instruction to ask for both "decision rights and the escalation path."

**High-evidence cluster (sig 7–9):**
> *"On the work where you used Apache AGE on PostgreSQL, what decisions were
> you able to make independently, and which ones required input from
> others?"* (sig=9) → names the independent choice (Apache AGE over
> multi-join queries) **and** the boundary ("many layers of approval" for
> the financial-data change).
>
> *"On the work where you conducted code reviews, what decisions could you
> make independently, and which ones required input from others?"* (sig=8)
> → answer lists four concrete decision categories (error handling, naming,
> duplication, performance/security) as things owned outright.
>
> *"On the work where you integrated with various APIs, what decisions
> could you make independently..."* (sig=8) → clean split: schemas/stores
> owned, backend key coordination not.

**What these share:** the question names a **specific technical artifact
from the claim** ("Apache AGE on PostgreSQL," "code reviews," "various
APIs") rather than a generic "this work," and it always asks for **both
halves** — the decision *and* its boundary — in one sentence. Every
high-yield answer produces a decision-plus-constraint pair because the
question structurally demands both.

**Low-evidence cluster (sig 0):**
> *"On Used GPT, what could you decide yourself and what had to go to
> someone else?"* (sig=0) → answer: *"what do you mean"*. This is the
> literal fallback template (`MOVE_FALLBACKS[AUTHORITY]`) rendered against a
> claim whose extracted subject is just "Used GPT" — a two-word,
> content-free `$object`. The template's phrasing is identical in structure
> to the high performers above; the difference is that `$object` here
> carries no real anchor for the candidate to answer against.
>
> *"On the work where you delivered GenAI features at Shine.com, what
> decisions could you make independently, and what needed approval from
> others?"* (sig=0) → *"All with product approval."* Well-formed question,
> terse/low-effort answer — a candidate-engagement outcome, not a wording
> defect.
>
> One answer (sig=4, "audio and IoT projects... which required escalation?")
> is a **non-sequitur**: the candidate answered as if asked "what do you
> check every morning," ignoring the decision-rights question entirely.
> The question itself is fine; the candidate lost track of what was asked,
> most likely from earlier answers in the same thread bleeding together.

**Pattern:** AUTHORITY's template is structurally sound at every yield
level. What separates high from low is **how much the claim itself gives the
question to anchor on** — a thin, under-specified claim (`$object` = "Used
GPT") starves even a well-built template of anything to ask about.

---

## DEPENDENCY (n = 11)

**Dominant template:** *"Can you describe a moment when [waiting on /
integrating] [X] [delayed/blocked/affected] your [progress/work]?"*

**High-evidence cluster (sig 5–14):**
> *"Can you describe a moment when integrating Langfuse or mem0 was delayed
> or blocked by another dependency, and how that impacted your workflow?"*
> (sig=14, the single highest-yield turn across all six moves) → produces a
> full causal chain: MCP2 → wrong GPT version → auth-layer retries →
> fallback to an older model → degraded, slower responses.
>
> *"Can you describe a moment when you were waiting on another team or
> resource to complete your UX discovery work, and how that impacted your
> design of conversational flows?"* (sig=7) → names the exact workaround
> (built a flexible prototype while waiting, refined once inputs arrived).
>
> *"You mentioned deploying OpenSearch dashboards. Was there a moment when
> waiting on Pydantic schema validation blocked your progress?"* (sig=5) →
> names the specific blocking mechanism (schema validation → pipeline →
> dashboard refresh lag).

**What these share:** every high performer names the **specific blocking
artifact** (a named library, a named team's specific deliverable, a named
schema-validation step) *and* asks explicitly **"how did it impact
[something concrete]"** rather than leaving impact open-ended. This is the
same "name the thing, ask for the effect" shape that works for AUTHORITY and
OPERATING_CONTEXT.

**Low-evidence cluster (sig 0):**
> *"Can you describe a moment when the integration of multi-sensor satellite
> data was delayed or blocked by a dependency, and how that affected your
> work on the geoinformatic system?"* (sig=0) → *"Can't recall."* Well-formed,
> specific question; the claim's technical depth may simply have outrun this
> candidate's actual recall.
>
> *"On the work where you developed Slack and WhatsApp bots, was there a
> moment when a dependency delayed your progress?"* (sig=0) → *"We move to
> the next question"* — candidate declining outright, not a wording issue.

**Pattern:** DEPENDENCY has no clear low-evidence *wording* cluster — every
weak turn here pairs a specific, well-built question with a candidate who
either couldn't recall or declined. Its low overall selection rate
(established in the prior audit) is a planner problem, not a wording one;
this move's actual phrasing is consistently strong when it fires.

---

## OWNERSHIP_BOUNDARY (n = 6, small sample — read as illustrative, not conclusive)

**Dominant template:** *"What specific [part/tasks/components] did you
[handle/develop] in/for [X], and what happened [after/next]?"*

**High-evidence cluster (sig 5–7):**
> *"You mentioned identifying TDS and commission discrepancies. What
> specific part did you handle in renewing the merchant agreements?"*
> (sig=7) → answer is a clean, enumerable list of owned steps (review,
> discrepancy flagging, coordination, sign-off).
>
> *"What specific tasks did you handle when guiding and mentoring the QA
> team across different Fintech projects?"* (sig=5) → same list shape (task
> assignment, bandwidth management, automation design, mentoring, review).

**What these share:** "what specific [plural noun] did you handle **in
[named process]**" — the ownership question is anchored to a concrete,
already-established activity, not asked in the abstract.

**Low-evidence / off-target cluster:**
> *"After you developed the cinematic pacing and typography systems, what
> was the next step in the promotional creative process?"* (sig=1) → this
> is the one clear **wording-drift** case in the whole audit: the generated
> question drops the ownership-boundary clause entirely ("what part was
> yours") and instead asks a generic process-sequencing question ("what was
> the next step"). It is labeled `OWNERSHIP_BOUNDARY` but does not ask an
> ownership-boundary question. The answer it draws — *"Decrease the time
> for creating visual"* — is neither ownership evidence nor a real answer to
> what was asked.
>
> *"What specific server-side operations did you optimize... and what
> happened after your part was completed?"* (sig=0) → garbled answer
> ("I iptih4v4ece"), candidate noise, not a wording defect.

**Pattern:** when the generated question keeps both halves of the brief
("what part was yours" + a concrete named activity to anchor it to"), it
reliably produces ownership evidence. The one case where generation dropped
the ownership clause produced a question that no longer measures what its
own move name claims to measure.

---

## OPERATING_CONTEXT (n = 52, the largest sample)

**Dominant template:** *"What was the first [thing/indicator/report/data
source] you [checked/looked at/examined] to [know/ensure/identify] [X]?"*

**High-evidence cluster (sig 8–11):**
> *"You mentioned conducting market research and analyses. What specific
> reports or data sources did you first examine to identify potential
> organizations?"* (sig=11, highest in this move) → answer: a five-item list
> (industry reports, company databases, LinkedIn insights, hiring trends,
> sector reports).
>
> *"You mentioned building predictive risk models. What was the first
> report or alert you checked to see if something needed adjusting..."*
> (sig=8) → a full causal narrative: feature-importance check → leakage
> suspicion → traced to a funnel-stage field and a database type bug.
>
> *"You mentioned delivering executive-ready recommendations. What was the
> first report or data source you checked to understand the client's
> needs?"* (sig=8) → names the exact artifact (a 780-row Tally sales
> register) and a specific reconciliation step (₹5.25 crore matched).

**What these share:** two features recur across every top performer —
(1) **plural, enumerable framing**: "what reports **or** sources," "what
indicator **or** report," inviting a list rather than a single fact; and
(2) a **specific named claim subject** substituted into the question
("predictive risk models," "executive-ready recommendations," "Python,
FastAPI, and Django for microservices") rather than a bare "this work."

**Low-evidence cluster (sig 0, excluding candidate noise):**
> *"You mentioned managing a portfolio of requisitions. What was the first
> report or system you checked each day to ensure everything was on
> track?"* — "everything was on track" is the tell: several
> `OPERATING_CONTEXT` questions across *different, unrelated claims* share
> this identical closing clause almost verbatim ("day-to-day design
> activities," "audio and IoT projects," "portfolio of requisitions" all end
> "...to ensure everything was on track" / "...to track project progress or
> spot issues"). This is the one clearly templated, low-specificity closing
> pattern in the corpus — it does not name what "on track" means for *this*
> claim, unlike the top cluster's named artifacts.
>
> *"On the work where you built the multi-agent shopping assistant, what
> was the first thing you checked to know if the system needed attention?"*
> (sig=1) — singular "the first thing," no enumeration invited, no named
> artifact beyond the claim title itself; the answer ("I can't remember...")
> is a case where a thin question met a thin answer.
>
> The genuine dead-turn floor (`Ufoufoy`, `Fdr`, `Yes`, `.`, `Hhhh`, `Kktso`)
> is a substantial fraction of this move's zero-signal turns and is
> candidate noise, independent of wording.

**Pattern:** `OPERATING_CONTEXT`'s highest performers ask for **an
enumerable category** ("reports or sources," "indicator or alert") tied to a
**named, specific claim subject**; its weakest genuine (non-noise) performers
ask for **a single generic "first thing"** with a **stock closing clause**
that could be pasted onto almost any claim unchanged.

---

## FAILURE (n = 43)

**Dominant template:** *"Can you [describe/recall] a [specific]
instance/time when [X] didn't [perform/go/work] as expected, and what
[happened/you discovered/you did]?"*

**High-evidence cluster (sig 7–10):**
> *"...can you describe a specific instance where the predictive modeling
> didn't yield the expected results?"* (sig=10) → a genuine two-part causal
> chain: discrimination-vs-calibration diagnosis, then the fix (a
> calibration step) and re-validation.
>
> *"Can you recall a specific instance when the MCP server deployment on
> Hydra didn't perform as expected and what you discovered was the cause?"*
> (sig=10) → traced through a specific tool (Langfuse), to a span-level
> root cause (wrong model version), to the fix.
>
> *"You mentioned negotiating with banks to reduce merchant queries. Can you
> describe a specific instance where the negotiation didn't go as
> planned?"* (sig=8) → names the obstacle, the response, and the resolution.

**What these share:** every top performer's question explicitly asks not
just "what happened" but **"what you discovered was the cause"** or **"what
you did to address it"** — a diagnosis-seeking clause layered on top of the
bare failure-recall clause. This is the single clearest causal-chain-inducing
structure found in the whole audit: *recall the failure* + *name the cause*
+ *(often) name the fix*, in one question.

**Low-evidence cluster (sig 0, excluding candidate noise):**
> *"Can you describe a time when a tutoring session didn't go as planned and
> what specifically went wrong?"* → *"I don't know."*
> *"Can you tell me about a time when engaging with a startup founder didn't
> lead to a hiring mandate as expected?"* → *"I don't know."*
> *"On the work where you reduced P50 latency, describe a specific time when
> the optimization unexpectedly failed..."* → *"Can't remember."*

These three are structurally identical in quality to the high performers —
each names a specific claim subject and asks for cause/outcome — yet draw a
flat non-answer. The common thread is not the question's construction but
the **claim's own texture**: soft, one-line, non-technical claims
("tutoring," "engaging with a startup founder") give a candidate nothing
concrete enough to reconstruct a specific failure moment from, no matter how
well the FAILURE question is built around them. A meaningful separate share
of this move's zero-signal turns (`Obrigado.`, `Kktso`, `I don't know` used
as a reflex rather than a real memory gap, `Where are you getting these
questions from?`) is candidate disengagement, not a wording pattern.

**Pattern:** FAILURE's causal-chain yield is driven almost entirely by
whether the question asks for the **discovered cause**, not just the event —
and even a perfectly-built version of that question cannot manufacture a
specific memory the candidate's own claim never had the texture to support.

---

## METRIC_DEFINITION (n = 3 — too small to cluster, reported as-is)

All three instances follow the intended template exactly — *"How was the
[metric] metric [defined/derived/measured], including what data was counted
and the baseline used?"* — which already matches the move's own design brief
("ask how the metric was DERIVED... never what the value was,"
`MOVE_BRIEFS[METRIC_DEFINITION]`). Results:

> *"How was the performance metric defined and measured during the ReactJS
> and Redux implementation?"* (sig=1) → *"Basically measured on the time to
> load the pinch"* — a real but shallow answer: a metric name repeated, no
> baseline, no counting method.
> *"...how was the P50 latency metric derived, including what data was
> counted and the baseline used?"* (sig=0, the most fully-specified version
> in the whole sample) → *"I don't know."*
> *"...how did you derive the candidate search latency metric and what
> baseline did you compare it against?"* (sig=0) → *"From text based to
> vector based"* — answers a different question (what changed) than the one
> asked (how was it measured).

**Pattern, stated carefully given n=3:** the best-worded instance in this
set is also the one that got the flattest non-answer. There is no wording
variant left to try here that the corpus demonstrates would do better — the
questions already ask exactly what the move's own design intends. The
bottleneck this small sample points to is candidates not knowing their own
metric's provenance, not a phrasing gap.

---

## Cross-move comparison: what wording structures do which job

### Structures that consistently produce causal chains, decisions, constraints, or ownership evidence

1. **Ask for the diagnosis, not just the event.** "...and what you discovered
   was the cause" / "...and how that impacted [something concrete]" turns a
   bare recall question into a causal-chain question. This is the single
   strongest pattern in the audit, visible identically in `FAILURE`'s and
   `DEPENDENCY`'s top clusters.
2. **Ask for both halves of a boundary in one sentence.** `AUTHORITY`'s "what
   could you decide... and which required approval" reliably produces a
   decision-plus-constraint pair *because* the question demands both; no
   `AUTHORITY` question in this sample that kept both clauses failed to
   produce at least a partial boundary answer.
3. **Name a specific, concrete artifact from the claim inside the
   question**, not a pronoun. Every high-yield question across all six moves
   substitutes something specific ("Apache AGE on PostgreSQL," "Langfuse or
   mem0," "the merchant agreements," "predictive risk models") in place of
   "this work" or "the system." This is the one pattern common to every
   single move examined.
4. **Invite an enumerable answer with plural/"or" framing.** "What reports
   *or* data sources," "what specific tasks," "what specific part" —
   correlates with list-shaped, multi-signal answers in `OPERATING_CONTEXT`
   and `OWNERSHIP_BOUNDARY`'s top clusters specifically.

### Structures that consistently produce generic answers, definitions, shallow descriptions, or dead turns

1. **A thin `$object` fed into an otherwise-sound template.** `AUTHORITY`'s
   fallback rendered against "Used GPT" produced confusion ("what do you
   mean"), not because the template is weak but because the claim gave it
   nothing to anchor to — the same template scores 7–9 signals against a
   richer claim.
2. **Singular, non-enumerable "first thing" framing with no named
   artifact.** `OPERATING_CONTEXT`'s weakest genuine (non-noise) performers
   ask "what was the first thing you checked" with the claim referenced only
   by its title, not by any specific report, tool, or artifact.
3. **A stock closing clause reused near-verbatim across unrelated claims.**
   "...to ensure everything was on track" / "...to track project progress
   or spot issues" appears, almost unchanged, attached to claims about
   design work, IoT projects, and requisition management alike — the one
   template-reuse pattern visible in this sample, and it clusters with
   `OPERATING_CONTEXT`'s weaker end.
4. **Dropping the move's defining clause during generation.** The one
   `OWNERSHIP_BOUNDARY` question that omitted "what part was yours" and
   asked a generic process-sequencing question instead produced an answer
   that isn't ownership evidence — not because ownership evidence wasn't
   available, but because the question stopped asking for it.
5. **A well-built question against a claim with no texture to support an
   answer.** `FAILURE` and `METRIC_DEFINITION`'s flattest non-answers pair
   *good* questions with *thin* claims (a one-line "tutoring" or "startup
   engagement" claim, or a metric the candidate never actually derived
   themselves) — the wording is not the failure mode here, and no
   rephrasing demonstrated in this corpus fixes it.
6. **Candidate noise, independent of wording, present in every move's tail.**
   Garbled or disengaged answers ("Hhhh," "Fdr," "Ufoufoy," "Obrigado.")
   appear regardless of how the question was built and should not be
   attributed to question quality.

---

## Answer to the question asked

> Given the same move, what question patterns generate strong evidence and
> what patterns generate weak evidence?

Across all six moves, the same two-part recipe separates strong from weak
questions: **(1) name something specific and real from this candidate's own
claim, and (2) ask explicitly for the thing that's hard to fake** — the
discovered cause (`FAILURE`, `DEPENDENCY`), both halves of a decision
boundary (`AUTHORITY`), or a concrete, already-anchored activity
(`OWNERSHIP_BOUNDARY`, `OPERATING_CONTEXT`'s top cluster). Weak questions
either drop that second clause (asking only "what happened," only "what
could you decide," or drifting off the move's own topic entirely), or keep
the clause but have nothing concrete to substitute into it because the
underlying claim itself is thin. `METRIC_DEFINITION` is the one move in this
sample where even its best-available wording — which already matches its own
design brief exactly — could not be shown to help, suggesting its yield
ceiling here is set by what candidates actually know, not by anything a
different question structure would fix.
