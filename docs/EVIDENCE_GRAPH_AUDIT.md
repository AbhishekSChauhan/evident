# Evidence Graph Audit

**Source note before anything else:** the brief asked to read
`evidence_graph.md`, `scoring.md`, `recruiter_workflow.md`, and
`candidate_workflow.md`. None of these four files exist anywhere in this
repository — checked by direct filesystem search, not by scanning `docs/`
for something similar. The real files covering this ground are
`docs/PROOFSCREEN_DOMAIN_MODEL.md` (the vocabulary review, including the
domain model's own F5 finding that *"'Evidence Graph' [means] the whole
tree — claims, Q&A, dimensions, scores"*), `docs/DEVELOPER_B_CONTRACT.md`
(the actual recruiter-facing ownership contract), and, most directly,
**`docs/ARCHITECTURE_LAYER_AUDIT.md`**, a prior, independently-written,
code-cited audit whose Layers 4–6 already traced the evidence-node and
graph layers in detail. That document is cited below, not restated — this
audit adds the specific angles it didn't cover (production call sites,
which outputs depend on tree shape vs. flat rows, and the direct
essential/partial/decorative verdict) and verifies its claims against fresh
code reads rather than assuming them.

---

## What nodes exist

Traced from `api/schemas.py` and `api/engine/graph.py` directly:

- **`CandidateGraph`** (`schemas.py:434`) — the root. One per candidate,
  assembled per-request.
- **`ClaimGraph`** (`schemas.py:385`) — one per claim, nested inside
  `CandidateGraph.claims`. Carries its own `qa: list[QATurn]`,
  `dimensions: list[DimensionScore]`, and `claim_score`.
- **`QATurn`** (`schemas.py:374`) — one per question/answer pair, nested
  inside a `ClaimGraph`.
- **`DimensionScore`** (`schemas.py:292`) — nested at both the claim level
  (per-claim) and the candidate level (`CandidateGraph.dimension_profile`,
  the aggregate).
- **`EvidenceNode`** (`schemas.py:304`) — declared, and **never
  instantiated as part of `CandidateGraph` at all**. Confirmed by reading
  `build_candidate_graph()`'s full body (`graph.py:265–490`): it constructs
  `ClaimGraph` and `QATurn` objects directly from `Evidence` table rows: it
  never creates an `EvidenceNode`. `ARCHITECTURE_LAYER_AUDIT.md` Layer 5
  already flagged this precisely: *"No `EvidenceNode` row exists in the
  database despite `schemas.py:304` declaring an `EvidenceNode` Pydantic
  type — it's a response shape... never itself stored."* Fresh check here
  adds: it isn't just never stored, it isn't even *constructed* by the one
  function that builds the graph.

**The node vocabulary is a strict three-level tree: Candidate → Claim →
(QA turn | DimensionScore).** Nothing in `schemas.py` or `graph.py`
represents a node that can appear under more than one parent, and nothing
represents a relationship between two claims or two candidates.

## What edges exist

**Foreign keys only, and only ever in one direction (child points at
parent).** `models.py`: `Claim.candidate_id`, `Question.claim_id`,
`Response.question_id`, `Evidence.claim_id` + `Evidence.response_id`. Every
"edge" `build_candidate_graph()` walks is a `select()` filtered by one of
these columns (`graph.py:265–490`, confirmed by direct read: the function
body is a sequence of `await db.execute(select(...).where(...))` calls,
nested and re-grouped in Python — there is no adjacency structure, no edge
table, and (confirmed against `ARCHITECTURE_LAYER_AUDIT.md` Layer 5) no
edge carries a type, weight, or direction beyond what the foreign key
already implies.

## Which edges are inferred vs. observed

**All of them are observed — a foreign key written when a row was created.
None are inferred.** There is no similarity computation, no relationship
scoring, and no mechanism anywhere that looks at two claims, two answers, or
two candidates and decides they are related. The one feature that would
have been an inferred edge — `EvidenceCategory.CROSS_CLAIM_LINK` — is
confirmed dead three ways in `ARCHITECTURE_LAYER_AUDIT.md` Layer 2: gated
off by default (`EVIDENCE_PLANNER_V2=false`), explicitly excluded from
`PRIORITY_ORDER` even when the flag is on (`orchestrator.py:1191`), and
dependent on a prompt file (`api/prompts/claim_graph.txt`) that exists on
disk but is never loaded anywhere in `api/`. **This is the one place in the
whole codebase someone clearly intended a real, inferred, cross-node
relationship — a claim linked to a different claim by more than a shared
`candidate_id` — and it was never built past the name and an orphaned
prompt file.**

## Which graph operations are actually used in production

Every call site of `build_candidate_graph()`, found by direct grep, not
assumed:

| Caller | Purpose | What it actually reads from the result |
|---|---|---|
| `routers/recruiter.py:84` | `GET /api/recruiter/candidates/{id}` — the single-candidate detail page | The full nested tree (this is the one real consumer of tree shape — see next section) |
| `routers/job_fit.py:86` | `POST /api/job-fit` (single candidate) | `graph.dimension_profile` (flat aggregate) for Case A; `graph.claims[].text`/`.qa` as raw text for Case B's substring search — never the tree's nesting itself |
| `routers/job_fit.py:110` | `POST /api/job-fit/rank` — **rebuilds the full graph once per candidate being ranked**, inside a loop | Same two flat/text reads as above, repeated per candidate |
| `routers/dev.py:166` | Dev-tooling inspection endpoint | Whatever the dev tool renders — not a recruiter-facing path |
| `routers/whatsapp.py:363` | The final message sent to the **candidate** (not the recruiter) at interview close | Exactly two flat scalars: `graph.competence_score` and a count of `probed` dimensions in `graph.dimension_profile` — the entire nested claim/QA tree is fetched and discarded unused |
| `graph.py:493` (`recompute_profile`) | Writes the cached `profiles` row | Aggregates only — flattens the graph back down into scalar columns immediately after building it |

**`rank_candidates()` — the function behind the recruiter's main ranked
list — does not call `build_candidate_graph()` at all.** Verified by
reading its full body (`graph.py:700` onward): it queries `Candidate` and
`Profile` (the flat cache table) directly, joins in `JobRole` weights, and
recomputes the ranking arithmetic from those flat rows. The busiest,
highest-traffic recruiter output in the product does not touch the graph.

**No traversal function exists anywhere in the codebase.** There is no
"find related claims," "walk from this evidence node to its dimension," or
"find candidates who share evidence" function. Every "hop" mentioned in
`ARCHITECTURE_LAYER_AUDIT.md`'s Layer 5 chain (Claim → Evidence → Dimension
→ Job Requirement → Match) is a fresh JOIN written inline at the point of
use, not a graph API being called.

## Which recruiter-facing outputs depend on graph structure vs. flat rows

- **Ranked candidate list** — flat. Reads `Profile` rows directly (above).
- **Job-fit score, single or ranked** — flat. Reads `dimension_profile`
  (an aggregate list, not a traversal) and raw claim/QA text for keyword
  matching (`ARCHITECTURE_LAYER_AUDIT.md` Layer 6, Case B). Never touches
  claim-to-claim or QA-turn nesting.
- **The WhatsApp candidate summary message** — flat. Two scalars, as shown
  above.
- **The single-candidate detail page** — **this is the one output that
  genuinely renders the nested shape**: per-claim scores, and within each
  claim, the specific questions and answers that produced them. A recruiter
  clicking into one candidate to see "why does this claim score 62" needs
  exactly this nesting.

**One real dependency out of four production outputs.**

## Could the current recruiter output be generated entirely from claims, evidence rows, and claim scores, without constructing a graph?

**Yes, for three of the four outputs immediately — they already are.** The
ranked list, both job-fit paths, and the WhatsApp message all currently
consume either flat cached scores or raw text, never the tree.

**For the fourth (the single-candidate detail page), also yes, and the
reason is precise: `build_candidate_graph()`'s own implementation is
already nothing but a flat multi-table query, re-nested in Python.**
Read directly, its body is: select the candidate's claims, then for each
claim select its questions+responses+evidence rows, then group the results
into `ClaimGraph`/`QATurn` objects in application code
(`graph.py:265–490`). This is not a graph database query, a traversal, or
anything requiring node/edge semantics — it is a `SELECT ... WHERE
claim_id = ...` per claim, with the results grouped by hand. Producing the
identical detail-page response from `claims` + `evidence` + `claim_scores`
directly requires exactly the same three queries this function already
runs; the only thing "the graph" adds is that one shared function performs
the grouping once instead of four call sites each writing their own JOIN.
**That is real software-engineering value — a single tested assembly point,
correctly tenant-scoped (`TenantScope` is a required, non-defaulted
argument, `graph.py:14–18`) — but it is the value of a well-written service
function, not the value of a graph.**

## Which future capabilities genuinely require a graph

Distinguishing "needs better-indexed relational data" from "needs actual
graph traversal" against `EVIDENT_MASTER_CONTEXT.md`'s own stated roadmap:

- **Phase 2, "Evidence-Based Search"** (*"find backend engineers who have
  personally solved scaling issues above 1M requests/day"*) — this is a
  **search/index problem**: it needs typed signals promoted out of the
  `responses.signals_json` blob into queryable rows (already recommended,
  independently, as C4 in `ARCHITECTURE_LAYER_AUDIT.md`) so a query can
  filter on signal content. Nothing about answering that query requires
  walking edges between nodes — it requires an index, not a graph.
- **Phase 3, "graph-to-graph matching"** — taken literally, this would
  require a job's requirements and a candidate's evidence to each have
  internal relational structure that a matching algorithm traverses. Neither
  currently does: a job's requirements are a flat list
  (`job_fit.JobRequirement`), and a candidate's evidence, per this audit, is
  a flat three-level tree with no cross-claim edges. As specified today,
  "graph-to-graph matching" reduces to bipartite matching over two flat
  collections — a real capability gap, but not evidence that the *storage
  layer* needs to become a graph; the matching *algorithm* would, the data
  model underneath it doesn't have to.
- **The one capability that would be unambiguously, inherently
  graph-shaped** is exactly the dead one: claim-to-claim or candidate-to-
  candidate relationships (`CROSS_CLAIM_LINK`, or a hypothetical "candidates
  who share verified evidence of the same system"). This is the only future
  feature in the product's own stated vision that cannot be answered by a
  well-indexed relational table, because it is fundamentally a multi-hop,
  cross-node relationship question rather than a lookup or a filter.

## Is the graph currently essential, partially utilized, or decorative architecture?

**Decorative, with one real, non-graph-shaped exception.** "Essential"
would require some production behavior to break without it; nothing does —
the highest-traffic output (the ranked list) already bypasses it entirely,
and every other consumer reads flat scalars or raw text out of it rather
than its nesting. "Partially utilized" would require the *graph-specific*
capabilities (traversal, typed/weighted edges, cross-node relationships) to
be used at least some of the time; none of those capabilities exist to be
used, partially or otherwise. What genuinely exists and genuinely earns its
keep is a single, well-tested, correctly tenant-scoped **assembly function**
that several callers share — real value, but the value of a shared query
helper, not of a graph. Calling this artifact "the Evidence Graph" is, per
`PROOFSCREEN_DOMAIN_MODEL.md`'s own F5 finding, a vocabulary choice made
under exactly this kind of ambiguity — and per that same document's
recommended fix, the accurate name for what this code actually is would be
"the assembled read model," not a graph.

## What information is lost if the graph is removed

Almost none. Deleting `build_candidate_graph()` and inlining its three
queries at each of its four call sites would lose: (a) the convenience of
one shared, tested function instead of four separately-written ones, and
(b) nothing else — no traversal capability, no relationship data, no
inferred edge, and no query that is only expressible today because a graph
exists, because none of those things currently exist to lose. The single
real behavior change would be maintenance cost (four copies of the same
JOIN logic instead of one), which is a real cost, but it is the cost of
losing a shared function, not of losing a graph.

## What becomes possible only because the graph exists

**Nothing, at the capability level.** Every number, every quote, and every
ranking this audit traced back to `build_candidate_graph()` is
reconstructable, today, directly from `claims`, `evidence`, and
`claim_scores` with a query no more complex than the ones the function
already runs. The one thing that would be genuinely new — a cross-claim or
cross-candidate relationship a recruiter or a matching algorithm could
traverse — does not exist in the current implementation, gated or
otherwise; it exists only as a dead category name and an unloaded prompt
file.

---

## Direct answer

**Do we actually need an Evidence Graph, or do we merely have evidence
records stored in graph-shaped language?** The latter. What exists today is
a correctly-built, well-tested, tenant-safe **assembly function** over
ordinary relational rows, returned as a nested Pydantic tree because a
recruiter's detail page happens to want that shape. It has a node
vocabulary with no cross-links, edges that are entirely foreign keys with no
type or weight, zero inferred relationships, and its one dead attempt at a
genuine graph feature (`CROSS_CLAIM_LINK`) never got past an enum name and
an unused prompt file. The highest-traffic recruiter output bypasses it
entirely. Nothing currently produced by this system requires graph
traversal, and the master context's own future vision — evidence-based
search — is an indexing problem, not a graph problem. The name is doing
work the architecture is not.
