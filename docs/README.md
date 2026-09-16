# ProofScreen — documentation index

Two developers share this repo and push to `main` hourly. These documents are
what keep that conflict-free, so the reading order below is not a suggestion:
`EXECUTION_STANDARD.md` §1 requires the frozen documents to be read *before*
proposing code, and both developer contracts declare themselves subordinate to
three of them.

`CLAUDE.md` and `README.md` stay at the repo root. Everything else is here.

---

## Read in this order

| # | Document | Why it is first |
|---|---|---|
| 1 | [EXECUTION_STANDARD.md](EXECUTION_STANDARD.md) | The binding process: architecture is sacred, plan before code, tests define acceptance. Every other document is subordinate to it |
| 2 | [ARCHITECTURE_LOCK_v1.md](ARCHITECTURE_LOCK_v1.md) | What is frozen, and the logged deviations from it |
| 3 | [EVALUATION_ARCHITECTURE_PRINCIPLES.md](EVALUATION_ARCHITECTURE_PRINCIPLES.md) | Why the model never scores, and what "evidence" means here |
| 4 | [PROOFSCREEN_DOMAIN_MODEL.md](PROOFSCREEN_DOMAIN_MODEL.md) | The vocabulary — claim, probe, signal, dimension, evidence |
| 5 | [PHASE_1_EXECUTION_PLAN.md](PHASE_1_EXECUTION_PLAN.md) | The active phase |
| 6 | [PHASE_1_TASKS.md](PHASE_1_TASKS.md) | P1-00 … P1-13: files, tests, migration, binary acceptance, dependency graph |
| 7 | [PHASE_1_SUCCESS_METRICS.md](PHASE_1_SUCCESS_METRICS.md) | M1–M5, guardrails, counter-metrics. All computable from stored data |

Then whichever of the two contracts applies to you:

- **Developer A** — [DEVELOPER_A_CONTRACT.md](DEVELOPER_A_CONTRACT.md). The
  intelligence path: routing, what gets asked, how an answer becomes evidence.
- **Developer B** — [DEVELOPER_B_CONTRACT.md](DEVELOPER_B_CONTRACT.md).
  Everything the recruiter reads.

Each contract carries its own ownership list, task order, branch names, and a
precondition to verify **before branching**. They are the authority on who may
edit what — see the ownership note below.

---

## Reference — read when the topic comes up

| Document | Read it when |
|---|---|
| [TRANSFER_DESIGN_AUDIT.md](TRANSFER_DESIGN_AUDIT.md) | Touching the TRANSFER probe. §3 is the family-invariance guarantee, §5 the brittleness table. Cited directly from `engine/signals.py` and `engine/question.py` |
| [FAMILY_TAXONOMY_REVIEW.md](FAMILY_TAXONOMY_REVIEW.md) | Touching `taxonomy.py`, `detect_family`, or `data/claim_taxonomy.json` |
| [CLAIM_INVENTORY.md](CLAIM_INVENTORY.md) | Recall-first extraction — the `CLAIM_INVENTORY` flag, blocked on `graph.py` |
| [EXTRACTION_ARCHITECTURE_REVIEW.md](EXTRACTION_ARCHITECTURE_REVIEW.md) | Extraction ranking/budget/typing defects (E1–E7), measured and mostly fixed |
| [CLASSIFICATION_PHASE2_REVIEW.md](CLASSIFICATION_PHASE2_REVIEW.md) | Touching `software_engineering`'s claim-type keywords — the fallback-collapse measurement, precision audit and what was deliberately not shipped |
| [QUESTION_GENERATION_FINDINGS.md](QUESTION_GENERATION_FINDINGS.md) | Touching question generation or the validator. Merges seven audits over the Phase 3 corpus (519 attempts). **§1 survives the forensic-generator switch, §3 does not** — read the warning at the top before acting on any number |
| [DEMO_RUNBOOK.md](DEMO_RUNBOOK.md) | Showing the product to anyone. Script, failure matrix, and what not to say. **Verify the scores against a fresh `seed.py --reset` first** — the ones it inherited are stale |
| [PRODUCTION_READINESS.md](PRODUCTION_READINESS.md) | Before deploying anything |
| [STATE_MACHINES.md](STATE_MACHINES.md) | Orienting in the control flow — the four nested state machines (session, question turn, evidence coverage, evaluation), every transition with the line that writes it, and the flags that change the shapes. **Derived from `api/` at `2659f20`, not from a plan** — if it disagrees with the code, the code wins |
| [REPO_STRUCTURE.md](REPO_STRUCTURE.md) | Orienting in the tree; the data-flow one-liners |
| [PLATFORM_ARCHITECTURE_REVIEW.md](PLATFORM_ARCHITECTURE_REVIEW.md) | Scaling questions — cohorts, families, multi-tenant |
| [PHASE_3_VALIDATION_STUDY.md](PHASE_3_VALIDATION_STUDY.md) | **Active.** Phase 3 — Real Interview Validation Study. Measures `question.validate()` against questions a live model actually generates, because the corpus reads 100% and can therefore only detect regression. Approved 2026-09-05 |
| [../studies/phase5/README.md](../studies/phase5/README.md) | **Phase 5 — `unsupported_premise` research.** Recommendation only; nothing implemented. Answers whether the largest measured defect class can be specified deterministically. It cannot, at κ = 0.477 — the finding, and the three decisions that follow from it, are in `studies/phase5/unsupported_premise_research.md` |
| [PHASE_4_TASKS.md](PHASE_4_TASKS.md) | **Active.** Phase 4 — Evaluation Integrity & Production Readiness. Task-level spec, execution log and acceptance report for D6–D10; the phase-level plan it is subordinate to is the "Phase 4" half of `PHASE_2_EXECUTION_PLAN.md`. Records two deviations under Rule 9: the entry condition was unmet, and `schemas.py` was edited additively |
| [PHASE_2_EXECUTION_PLAN.md](PHASE_2_EXECUTION_PLAN.md) | **Active.** Phase 1 exited 2026-09-05. Phase 2 is Question Quality Infrastructure; the previously-approved D6–D10 plan is preserved in the same file as **Phase 4** (renumbered from Phase 3 on 2026-09-05), still blocked on its own entry condition — M4a has produced a number. Task specs in [tasks/](tasks/) |

## Archive — history, not instructions

28 documents in [`archive/`](archive/) as of 2026-09-17: the superseded plans,
seven question audits now merged into `QUESTION_GENERATION_FINDINGS.md`, ten
design documents for two workstreams that have since shipped, and five one-off
investigations. The seven hackathon demo documents were **deleted** once
`DEMO_RUNBOOK.md` had taken what was still useful — `git show` recovers them.

**Do not take direction from anything in there.** Where it disagrees with the
numbered list above, the numbered list wins.
[`archive/README.md`](archive/README.md) says why each group moved, and which
six look archivable but are cited from code and must not be.

---

## Two things a new session gets wrong

**Ownership has three sources and they disagree.** The table in
`../README.md` assigns `engine/signals.py` to Developer B and `models.py` /
`ids.py` to A; both contracts say the opposite. **For Phase 1 the contracts
win** — they are per-file, explicit, and mutually consistent. `PHASE_1_TASKS.md`
P1-03 says why for `signals.py`: *"Owner A, **B reviews the `signals.py`
hunk**"* — A edits, B reviews. Do not re-litigate this per task.

The one interface between the two streams is **`FamilyMatch`**, the NamedTuple
A publishes from `taxonomy.py` in P1-06. B reads it in `graph.py` and calls
into A's modules for nothing else. Its shape must not change after B starts
P1-08b without telling them.

**The planning-to-code ratio is a known risk, already logged.** 28 documents
sit in this folder, down from 60. `EXECUTION_STANDARD.md` proposes C2 as the guardrail — *no
phase may add more planning documents than it merges implementation tasks* —
and notes Phase 1's documentation budget is already spent. Adding another
document here is a decision, not a default. Prefer editing one of these.

The 2026-09-17 triage cut `docs/` from 60 files to 28 by archiving 34 and
merging 14 into two. That bought room; it did not repeal C2.
