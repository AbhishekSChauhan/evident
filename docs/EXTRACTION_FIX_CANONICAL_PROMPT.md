# Extraction Fix — Canonical Bucket Definitions

## 1. Diff table

Every sentence/clause added in the proposed text, relative to
`EXTRACTION_FIX_SPECIFICATION.md` §1's exact text, classified.

### `decisions`

| Added text | Classification | Why |
|---|---|---|
| "Must contain both choice made and rationale." | **SAFE** | Restates the existing AND-gate rule already present two sentences later. No semantic change. |
| "'I chose Redis because latency was critical' is a decision." | **SAFE** | New positive example, same shape (choice + reason) as the two spec examples. |
| "'We used Redis' without a stated reason is not a decision." | **SAFE** | New negative example. Directly reinforces the AND-gate — strengthens disambiguation, doesn't loosen it. |

### `constraints`

| Added text | Classification | Why |
|---|---|---|
| "restriction" | **SAFE** | Synonym of "limitation," no new category. |
| "tradeoff" | **RISKY** | Not in spec. Creates a named collision with `concept_explanations` (which also gained this word) and with `decisions`' existing "instead of / rather than" framing. One sentence shape now has three plausible destinations. |
| "dependency" | **WRONG** | Redirects content away from its already-measured-good home. `MOVE_EVIDENCE_YIELD_AUDIT.md` found `DEPENDENCY`-move answers to be the corpus's single highest causal-density source, captured via `causal_links`. Instructing the model to route dependency-framed language into `constraints` changes the audited definition's intent, not just its wording. |
| "resource limitation," "performance limit," "organizational constraint" | **SAFE** | Redundant with "limitation"/"latency"/"headcount" already in spec — add length, not new overlap. |
| examples: "team size, deadlines, budget, latency requirements, compliance rules" | **SAFE** | Direct synonyms/restatements of spec's own list (headcount→team size, timeline→deadlines). |
| example: "infrastructure limits" | **SAFE** | A legitimate constraint kind present in the real corpus (e.g. the payload/rate-limit examples in `EXTRACTION_BUCKET_RECOVERY_AUDIT.md`), not a duplicate of any other bucket's definition. |
| `limitation` kind-list: added "infrastructure" | **SAFE** | Controlled-vocabulary addition inside the field itself, no cross-bucket effect. |

### `concept_explanations`

| Added text | Classification | Why |
|---|---|---|
| "mechanism, principle" | **SAFE** | Synonyms of "concept"/"process" already in spec. |
| "tradeoff" | **RISKY** | Same collision as above — now shared with `constraints`. |
| "architecture" | **SAFE** | No other bucket definition uses this word; explaining *why* an architecture works is distinct from naming it (`entities`/`tools`). |
| "technical reasoning" | **SAFE** | Reinforces "WHY," no new category. |
| examples: "feature leakage explanation, indexing, cache invalidation, model drift" | **SAFE** | Concrete, genuinely concept-shaped examples, consistent with real cases already found in `EXTRACTION_BUCKET_RECOVERY_AUDIT.md`. |
| "Not simple narration of actions." | **SAFE, valuable** | Exactly the kind of negative disambiguation against `process_steps` that `DECISION_CONSTRAINT_CONCEPT_EXTRACTION_PROMPT_AUDIT.md` §5 recommended — one-sided (only on this bucket), but a real improvement. |

### `boundaries`

| Added text | Classification | Why |
|---|---|---|
| "ownership" inserted before "boundary" | **SAFE** | Clarifying, reduces rather than increases overlap with `decisions`. |
| "Must identify what candidate owned, what candidate did not own, approval boundary, escalation boundary, or responsibility split" | **SAFE** | Elaborates `scope_held`/`scope_handed_off`, no new category. |
| examples: "I could deploy but architecture approval required my manager," "I owned backend services but DevOps handled infra" | **SAFE, valuable** | Both are clean, reason-free authority/scope splits — the exact shape that should NOT land in `decisions`. Directly useful for the decision-vs-boundary ambiguity. |

**Net count: 3 WRONG-or-RISKY items, both inside `constraints`'s and `concept_explanations`'s opening lists, both resolvable by deleting one word each ("dependency" from `constraints`; "tradeoff" from both).** Everything else proposed is safe to keep, and several additions (the `boundaries` examples, the `concept_explanations` negative clause, the `decisions` negative example) are net improvements over the literal specification text.

---

## 2. Risk analysis

**The contamination risk is concentrated in exactly one shared word and one redirected word, not in general over-elaboration.** Removing "tradeoff" from both `constraints` and `concept_explanations`, and removing "dependency" from `constraints`, eliminates every RISKY/WRONG item found. No other addition in either bucket creates a new cross-bucket collision — the rest is longer than the specification but not semantically different from it.

**One ambiguity survives even after those two removals, and it predates this implementation pass — it was present in the original specification text too:** a personal approval-authority threshold stated with a number attached (the vendor-purchase example: *"I could approve purchases up to 5 lakh, anything above needed director approval"*) is a legitimate `boundaries` match, but nothing in either the specification or the proposed text tells the model that an attached number doesn't make it a `constraints` match instead. This is not something Gemini introduced — it is a gap in the audited specification itself, now worth closing in the same pass since the bucket text is already being edited. The final definitions below add one short, targeted sentence to `constraints` and one example to `boundaries` to close it — the minimum addition that resolves the specific ambiguity named, nothing broader.

**No risk was found in `decisions` or in the structural parts of `boundaries`.** Both buckets' additions are safe as proposed; the final text below keeps nearly all of them.

---

## 3. Final approved bucket definitions

Drop-in replacement for the corresponding block in `extract_signals.txt`. Only these four bucket paragraphs change; `quantities`, `process_steps`, `causal_links`, `tools`, `metric_definitions`, `incident_markers`, `entities`, `facts`, `summary`, `HARD RULES`, and the JSON schema are untouched.

```
decisions          A choice they made AND why, when the answer states both
                   halves. `choice` = what they picked, adopted, or DELIBERATELY RETAINED /
                   OPTED NOT TO CHANGE (e.g., "did not change Redux Toolkit", "retained legacy auth").
                   `reason` = why, in their words (e.g., "data flow pipeline was correct").
                   Skip the whole item if the answer names a choice with no stated reason, or a reason
                   with no stated choice — a decision signal needs both halves present.
                   "I chose Redis because latency was critical" is a decision.
                   "We did not change Redux because the pipeline was correct" is a decision.
                   "We used synthetic data because production labels were sparse" is a decision.
                   "We used Redis" without a stated reason is not a decision.

constraints        A limitation that shaped the work, whatever the field: compliance,
                   budget, data availability, latency, headcount, timeline, or
                   infrastructure capacity (e.g., a payload limit, a rate limit, a
                   deadline, a headcount cap). `limitation` = the short kind of
                   constraint (compliance, data, budget, latency, timeline, headcount,
                   infrastructure, other). `effect` = what it stopped them from doing
                   or forced them to do instead, in their words.
                   A personal approval-authority threshold — what they could decide
                   alone versus what needed someone else's sign-off — is a `boundaries`
                   signal, not a constraint, even when a number is attached to it.

concept_explanations
                   An explanation of a domain concept, mechanism, principle, or
                   architecture that explains WHY it works or WHY it applies (e.g.,
                   a feature-leakage explanation, how an index speeds lookups, why
                   cache invalidation matters, what causes model drift). Not simple
                   narration of actions — a sentence that only describes what was
                   done, with no explanation of the underlying mechanism, belongs in
                   `process_steps` or `causal_links` instead.
                   `concept` = what they explained. `reasoning` = the explanation of why/how.

boundaries         An explicit boundary of personal responsibility vs. team or
                   manager scope — what was theirs to decide or do alone, and what
                   required someone else's sign-off or escalation (e.g., "I could
                   deploy but architecture approval required my manager", "I owned
                   backend services but DevOps handled infra", "I could approve
                   purchases up to a set limit, anything above needed director
                   approval"). A boundary does not need a stated reason to count —
                   unlike `decisions`, naming the split itself is sufficient.
                   `scope_held` = what was theirs to decide/do.
                   `scope_handed_off` = what went to others or required sign-off.
```
