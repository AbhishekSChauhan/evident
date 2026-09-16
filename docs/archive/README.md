# Archive — history, not instructions

**Do not take direction from anything in this folder.** Where a document here
disagrees with `../README.md`'s reading order, the reading order wins. These are
kept because the reasoning and the measurements are worth having, and because
deleting a measured number nobody will re-measure is a bad trade.

28 documents, ~9,400 lines. `docs/` went from 60 files to 28 in the 2026-09-17
triage: 34 archived here, 14 merged into two, and the seven hackathon demo
documents then deleted once their content had been extracted. Everything else
is one `git mv` from where it was, and the deleted seven are one `git show`
away.

---

## Why each group moved

### Two workstreams shipped, and their design docs still said they hadn't

This was the decisive finding of the triage. Ten documents opened with wording
like *"design specification. No code written."* or *"Nothing in this document is
wired to anything"* — describing code that is now live. That is exactly the
drift `EXECUTION_STANDARD.md` C3 exists to prevent.

**Forensic question generation — shipped.** `api/engine/anatomy.py` exists,
`api/prompts/forensic_question.txt` is in the prompt set, and
`settings.forensic_questions` defaults to **`true`**, so it is the live
generator (`qpol_3`).

- `FORENSIC_GENERATOR_DESIGN.md` · `FORENSIC_GENERATOR_SPEC.md` ·
  `FORENSIC_IMPLEMENTATION_READINESS.md` · `FORENSIC_MIGRATION_DELETIONS.md` ·
  `GENERATOR_ARTIFACTS_ANSWERS.md`

**Universal Competence Framework — shipped.** `KNOWLEDGE`, `EXECUTION`,
`PROBLEM_SOLVING`, `JUDGMENT`, `OWNERSHIP` and `ADAPTABILITY` are members of
`Dimension` in `api/schemas.py` with rubrics in `engine/signals.py`.
Candidate-level awareness shipped too — `ClaimState.candidate_seniority` gates
move selection.

- `UNIVERSAL_COMPETENCE_FRAMEWORK.md` · `COMPETENCE_FRAMEWORK_AUDIT.md` ·
  `COMPETENCE_MIGRATION_MINIMAL.md` · `CANDIDATE_LEVEL_AUDIT.md` ·
  `CANDIDATE_LEVEL_IMPLEMENTATION_AUDIT.md`

### Merged into one findings document

Seven audits measured the same corpus (`studies/phase3/`, 519 generation
attempts) and were consolidated into
[`../QUESTION_GENERATION_FINDINGS.md`](../QUESTION_GENERATION_FINDINGS.md),
which separates the findings that survive the generator change from the ones
that describe `qpol_2` only. Each audit remains authoritative for its own
method, derivations and worked examples.

- `QUESTION_GENERATION_AUDIT.md` · `QUESTION_GENERATION_DESIGN_AUDIT.md` ·
  `QUESTION_SYSTEM_AUDIT.md` · `QUESTION_DIVERSITY_AUDIT.md` ·
  `QUESTION_QUALITY_REVIEW.md` · `PROBE_LEVEL_FORENSIC_AUDIT.md` ·
  `PROBE_ARCHITECTURE_FACTUAL_AUDIT.md`

### Merged into one runbook, then deleted

Seven demo documents, ~4,900 lines, for a hackathon that ran 10–11 Sep 2026.
The presentable parts are in [`../DEMO_RUNBOOK.md`](../DEMO_RUNBOOK.md) and two
durable WhatsApp findings went into `CLAUDE.md`'s gotchas. **The sources
themselves were deleted on 2026-09-17** — see that runbook's Provenance section
for the `git show` commands that recover them.

### Superseded plans

Already declared superseded in `../README.md`'s own table before this move; they
were simply still sitting in the same folder as the live documents.

- `IMPLEMENTATION_PLAN.md` → `PHASE_1_TASKS.md`
- `EXECUTION_PLAN.md` · `SHIP_PLAN.md` → `PHASE_1_EXECUTION_PLAN.md`
- `PLAN_REVIEW.md` → critique of the above; conclusions folded into `EXECUTION_STANDARD.md`
- `ARCHITECTURE_AUDIT.md` → `ARCHITECTURE_LOCK_v1.md`

### One-off investigations and snapshots

Written to settle one question at one moment. The questions are settled.

| Document | What it settled |
|---|---|
| `PARSE_EXTRACT_MERGE_REVIEW.md` | **A rejected proposal.** Merging claim extraction into parsing — rejected, with the cost named: determinism, offline seeding, one of the two ingest paths, and failure isolation. Worth reading before anyone proposes it again |
| `CLAIM_EXTRACTION_RANKING_INVESTIGATION.md` | Why business-metric claims beat engineering-depth claims on one real resume |
| `PLANNER_ALIGNMENT_AUDIT.md` | Whether the planner suits a 6-question interview, against three real transcripts |
| `LIVE_INTERVIEW_QUALITY_AUDIT.md` | First quality read on the forensic generator — two real WhatsApp interviews, live `gpt-4o`, voice answers |
| `SYSTEM_FLOW_AND_MODULE_REPORT.md` | A PM-audience module-by-module snapshot at `4db6c6f`. Overlaps `../REPO_STRUCTURE.md` and `../STATE_MACHINES.md`, both of which are maintained |

`RESUME_PIPELINE_TRACE.md` did **not** come here — it is raw pipeline output, so
it moved to [`../../studies/RESUME_PIPELINE_TRACE.md`](../../studies/RESUME_PIPELINE_TRACE.md)
with the other measured artifacts.

---

## What stayed out of the archive, and why

Six documents that read like the ones here are still live because **a comment in
`api/`, `scripts/` or `tests/` cites them by path.** Archiving one breaks a
pointer that C3 put there deliberately.

| Document | Citations from code |
|---|---:|
| `EXTRACTION_ARCHITECTURE_REVIEW.md` | 9 |
| `QUESTION_EVAL_HARNESS_AND_LEVEL_MODEL.md` | 5 |
| `TRANSFER_DESIGN_AUDIT.md` | 3 |
| `CLASSIFICATION_PHASE2_REVIEW.md` | 2 |
| `ROLE_ROUTING_PROPOSAL.md` | 1 |
| `CLAIM_INVENTORY.md` | 1 |

`QUESTION_EVAL_HARNESS_AND_LEVEL_MODEL.md` is the trap: it reads exactly like
the seven merged question audits. Cluster-based cleanup kills it. Re-run the
check before archiving anything else:

```bash
grep -rhoE "docs/[A-Z0-9_]+\.md" --include=*.py api/ scripts/ tests/ | sort | uniq -c | sort -rn
```

## Link conventions in here

Links to live documents are `../NAME.md`; links between archived documents are
bare. Three files had pre-existing `docs/NAME.md` links that never resolved from
inside `docs/` — those were fixed in the same pass.
