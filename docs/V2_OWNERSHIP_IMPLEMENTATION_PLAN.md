# V2 Ownership Implementation Plan — Removing Archetype-Based Exclusion

**Status: plan only. No code changed by this document.**

**Scope discipline:** this plan covers ownership collection mechanics
only — which moves become eligible for which claims, and nothing else.
Scoring, the evidence graph, claim ranking, the recruiter UI, and the
broader gap-first V2 planner redesign (`V2_MINIMAL_METHODOLOGY_SYNTHESIS.md`,
`V2_OWNERSHIP_METHODOLOGY.md`) are explicitly out of scope here. This is a
narrow, backward-compatible patch to the *current* ladder architecture,
not a step toward replacing it.

---

## 1. Every place ownership opportunities are currently gated

Traced directly against the running code, not inferred:

| Gate | Where | What it does to ownership moves |
|---|---|---|
| **Archetype filter** | `question.py:1266-1287`, `ARCHETYPE_LADDER` | `Move.OWNERSHIP_BOUNDARY` appears **only** in `Archetype.OWNERSHIP`'s tuple (position 4 of 7). `Move.PEOPLE` appears in `Archetype.OWNERSHIP` (position 6) and `Archetype.VOLUME` (position 5). Neither appears in `Archetype.BUILD`, `Archetype.PROCESS`, or `Archetype.METRIC_MOVE`'s tuples at all — this is the **sole and complete** archetype gate. There is no separate "is this move allowed for this archetype" check anywhere else; the ladder dict *is* the gate. |
| **Move eligibility check** | `question.py:1459-1482`, `move_available()` | Has explicit preconditions for `METRIC_DEFINITION`, `EXCLUSION`, `COHERENCE`, `PERTURB`. **Falls through to `return True` for every other move**, `OWNERSHIP_BOUNDARY` and `PEOPLE` included. Confirmed by reading the function body directly: there is no runtime precondition on either ownership move today. |
| **Seniority restriction** | `question.py:1094-1098`, `LEVEL_RESTRICTED` | Contains exactly three entries: `AUTHORITY`, `EXCLUSION`, `PERTURB`. **`OWNERSHIP_BOUNDARY` and `PEOPLE` are not in this dict at all** — no seniority gate exists on either move today, at any candidate seniority, including `None`. |
| **Planner exclusion** | `orchestrator.py:340-373`, `ClaimState.forensic_moves_left()` | Builds its candidate list directly from `ARCHETYPE_LADDER[anatomy.archetype]` (line 350), then filters by `moves_used`, `move_available()`, and one further demo-mode seniority check — but that check's own tuple is `(Move.EXCLUSION, Move.AUTHORITY)` only (line 370). **Ownership moves pass through this function unfiltered beyond whatever the archetype ladder already handed it.** |

**Conclusion of the trace: there is exactly one gate, and it is the
archetype ladder dict itself.** Move eligibility and seniority restriction
both already treat ownership moves permissively; nothing downstream of the
archetype assignment adds a second exclusion.

---

## 2. Call graph: resume claim → archetype → planner eligibility → move selection

```
Claim.text, Claim.metric
        │
        ▼
anatomy_engine.analyse(claim.text, claim.metric)        [anatomy.py:308]
        │  internally calls _archetype(claim_text, metric_name, scope)
        │                                                [anatomy.py:294-305]
        │  a text-regex classifier — decided once, at extraction time,
        │  from the claim's own wording ("built/deployed" → BUILD,
        │  a bare metric → METRIC_MOVE, etc.)
        ▼
ClaimAnatomy.archetype  :  Archetype  (one of 5 enum values)
        │
        ▼
ClaimState.forensic_moves_left()                        [orchestrator.py:340]
        │  anatomy = self.anatomy                       (re-derived each call,
        │                                                 not stored — line 291-293)
        │  candidates = ARCHETYPE_LADDER[anatomy.archetype]   [question.py:1266]
        │       ─────────────────────────────────────────────────────────
        │       ███ THE GATE: if OWNERSHIP_BOUNDARY / PEOPLE are not in
        │       this archetype's tuple, they are never even considered
        │       past this line — nothing downstream can recover them ███
        │       ─────────────────────────────────────────────────────────
        │  filtered by: mv.value not in self.moves_used
        │           and move_available(mv, anatomy, ledger)   [question.py:1459]
        │           and not (demo_mode seniority check, EXCLUSION/AUTHORITY only)
        ▼
list[Move]  — the claim's currently-eligible moves this turn
        │
        ▼
plan_next_forensic(states, questions_asked)             [orchestrator.py, ~2217]
        │  breadth-first-then-depth scheduling across all claims in the
        │  session, choosing among each claim's forensic_moves_left()
        ▼
Move selected (or not) → generate_forensic_question()   [question.py:1700]
```

**The gate is a single data structure, read once per claim per turn, with
no secondary check anywhere in the chain.** This is what makes the
proposed change in §3 both correct and minimal: there is exactly one
place to change, and everything downstream of it (`move_available`,
`forensic_moves_left`, `plan_next_forensic`, question generation,
scoring, extraction, claim selection) already handles `OWNERSHIP_BOUNDARY`
exactly as it handles every other move — nothing downstream needs to
change to accommodate it appearing on more claims.

---

## 3. The minimal code change

**Edit `ARCHETYPE_LADDER` (`question.py:1266-1287`) to add
`Move.OWNERSHIP_BOUNDARY` to the `Archetype.BUILD`, `Archetype.PROCESS`,
and `Archetype.METRIC_MOVE` tuples.** Nothing else changes.

**`PEOPLE` is deliberately left out of this change.**
`V2_OWNERSHIP_METHODOLOGY.md` §8 already established, from measured
evidence across three independent audits, that `PEOPLE` is the weakest,
rarest, most reliably follow-up-substitutable ownership signal in the
system (lowest selection rate of any of the nine named moves at 9.5%,
weak on both occasions it was measured, and judged safely
follow-up-substitutable rather than slot-worthy). Adding it everywhere
would widen the change for a signal this series has no evidence is worth
a dedicated scheduled slot. If a future change wants it, that is a
separate, explicitly-justified decision — not bundled into this one.

**Where in each tuple to insert it:** immediately after `Move.PERTURB`,
matching its position in `Archetype.OWNERSHIP`'s own ladder (position 4
of 7 there). This preserves the existing breadth-first-then-depth
scheduling intent — `OPERATING_CONTEXT`, `FAILURE`, `PERTURB` remain the
first three moves tried on every claim regardless of archetype, exactly
as today — while giving ownership a ladder position before the
archetype-specific moves that currently occupy position 4 on `BUILD`
(`DEPENDENCY`), `PROCESS` (`AUTHORITY`), and `METRIC_MOVE`
(`METRIC_DEFINITION`), which shift to position 5.

**Why this is minimal and why it satisfies every stated requirement:**

- **Removes archetype-based ownership exclusion** — by construction: the
  one gate found in §1 is edited directly, nothing else is touched.
- **Preserves all other planner behavior** — `move_available()`,
  `LEVEL_RESTRICTED`, the demo-mode seniority filter, breadth-first
  scheduling order for the first three positions, and every other
  archetype's ladder (`OWNERSHIP`, `VOLUME`) are untouched. The existing
  moves on `BUILD`/`PROCESS`/`METRIC_MOVE` (`DEPENDENCY`, `EXCLUSION`,
  `COHERENCE`, `AUTHORITY`, `METRIC_DEFINITION`) are neither removed nor
  reordered relative to each other — only shifted one position later by
  the single insertion.
- **Does not change scoring** — `signals.py`/`scoring.py` are not part of
  this edit; they already score an `OWNERSHIP_BOUNDARY` answer identically
  regardless of which archetype the claim carries.
- **Does not change extraction** — `evidence.py`/the extraction prompts
  are not part of this edit; a question asked under this change is scored
  by the same, already-existing extraction path as any other
  `OWNERSHIP_BOUNDARY` question asked today.
- **Does not change claim selection** — `extract.py`'s claim-ranking
  functions never read `ARCHETYPE_LADDER`; archetype is assigned *after*
  a claim is already selected for interview, so this change cannot affect
  which claims get chosen, only what can be asked once a claim is already
  in play.

---

## 4. Before / after / expected coverage change

**Before:** `COVERAGE_REACHABILITY_AUDIT.md` measured the archetype
distribution directly across 100 real interviewed claims: `BUILD` 37%,
`PROCESS` 35%, `METRIC_MOVE` 7% — **79% of claims, structurally, can never
have `OWNERSHIP_BOUNDARY` offered**, decided by a text-regex classification
of the claim at extraction time, before any question is planned.
`OWNERSHIP` (11%) and `VOLUME` (10%) together are the only 21% of claims
where it is reachable at all.

**After:** every claim's ladder contains `Move.OWNERSHIP_BOUNDARY`
regardless of archetype. **Archetype-caused exclusion drops from 79% to
0%.** This is a change in *eligibility*, not a guarantee of being *asked*
— `move_available()` still returns `True` unconditionally for this move
(§1), so nothing new blocks it once eligible, but whether it is actually
selected still depends on `plan_next_forensic()`'s scheduling priority and
the remaining question budget, exactly as it does for every other move on
every claim today.

**Expected ownership coverage change:** the structural ceiling on
reachability rises from 21% of claims to 100% of claims. The *actual*
ask-rate increase this produces is not claimed here as a number — it
depends on scheduling and budget, which this change does not touch, and
should be re-measured directly rather than projected. The correct way to
measure it: re-run `DIMENSION_OPENING_AUDIT.md`'s exact methodology
(archetype distribution × in-ladder opportunities × selection rate) on
real post-change interviews, and confirm the "archetype exclusion" row in
its mechanism-breakdown table drops to zero while the "budget exhaustion"
and "planner choice" rows become the only remaining explanations for any
claim that still doesn't get asked.

---

## 5. Tests that must pass

**No existing test currently asserts archetype-based exclusion of
`OWNERSHIP_BOUNDARY`** — checked directly: nothing in `tests/` references
`ARCHETYPE_LADDER`, `OWNERSHIP_BOUNDARY`, or any of `Archetype.BUILD` /
`Archetype.PROCESS` / `Archetype.METRIC_MOVE` by name. This change has no
existing regression test to update; it needs new tests to lock in the
fix and guard against it silently regressing later.

**New tests required:**

1. `ARCHETYPE_LADDER[Archetype.BUILD]`, `ARCHETYPE_LADDER[Archetype.PROCESS]`,
   and `ARCHETYPE_LADDER[Archetype.METRIC_MOVE]` each contain
   `Move.OWNERSHIP_BOUNDARY`.
2. Each of those three tuples' *other* moves are unchanged in membership
   and relative order to each other — only the one insertion changed.
3. `ARCHETYPE_LADDER[Archetype.OWNERSHIP]` and
   `ARCHETYPE_LADDER[Archetype.VOLUME]` are byte-for-byte unchanged.
4. `move_available(Move.OWNERSHIP_BOUNDARY, anatomy, ledger)` returns
   `True` for a `BUILD`/`PROCESS`/`METRIC_MOVE`-archetype
   `ClaimAnatomy`, for at least one real example of each archetype.
5. `ClaimState.forensic_moves_left()` includes `Move.OWNERSHIP_BOUNDARY`
   for a fresh (no prior turns) claim of each of the three previously-excluded
   archetypes.
6. `Move.PEOPLE` is **not** present in `ARCHETYPE_LADDER[Archetype.BUILD]`,
   `[Archetype.PROCESS]`, or `[Archetype.METRIC_MOVE]` — an explicit
   negative test confirming the scoped decision in §3 was implemented as
   specified, not over-applied.
7. `LEVEL_RESTRICTED` is unchanged — `Move.OWNERSHIP_BOUNDARY` and
   `Move.PEOPLE` are still absent from it.
8. The full existing suite for `tests/test_policy.py` and
   `tests/test_final_fixes.py` (the two files that already exercise
   `ClaimState`, `plan_next_forensic`, and `move_available`) passes
   unmodified — confirming no existing planner behavior shifted.
9. The full existing scoring and extraction suites
   (`tests/test_scoring.py` and the extraction-path tests) pass unmodified
   — confirming §3's "does not change scoring" and "does not change
   extraction" claims hold in practice, not just by inspection.
10. The full existing claim-selection/extraction-ranking suite
    (`tests/test_extract.py`, `tests/test_taxonomy.py`) passes unmodified —
    confirming §3's "does not change claim selection" claim.
11. A live or simulated re-measurement (reusing
    `CLAIM_TYPE_ROI_VALIDATION_AUDIT.md`'s established simulated-interview
    methodology) confirming the archetype-exclusion row in
    `DIMENSION_OPENING_AUDIT.md`'s mechanism-breakdown table reads zero
    post-change, as predicted in §4 — the one test in this list that
    verifies the *intended effect*, not just the absence of regressions.
