# Question generation — measured findings

**What this is.** One findings document assembled from seven audits that all
measured the same corpus. The audits are in [`archive/`](archive/); this file
carries the numbers and the conclusions, and cites where each was produced. It
follows `EXECUTION_STANDARD.md` C3 — cite, do not restate — so where an audit
holds a derivation, method or worked example, the pointer goes there rather
than the text being copied.

**The corpus, for every number below.** `studies/phase3/` — **519 generation
attempts, 395 questions actually asked, 68 interviews, 9 families, $3.67**,
joined to `studies/phase3/study.sqlite3` (395 responses, 1,508 evidence rows,
92 finalised claim scores). Classification is deterministic
(`studies/phase3/classify.py`, earliest-cue-wins, 99.2% coverage).

---

## ⚠️ Read this before acting on anything here

**Every measurement below was taken against the probe-brief generator
(`qpol_2`), and that is no longer the default path.**
`settings.forensic_questions` defaults to **`true`**
([api/config.py:96](../api/config.py#L96)), so live question generation now runs
the forensic Move ladder (`qpol_3`) selected at
[api/engine/orchestrator.py:1230](../api/engine/orchestrator.py#L1230).

That splits this document in two, and the split is the most useful thing in it:

| | |
|---|---|
| **§1–§2 — still load-bearing** | Findings about the *validator*, the *regeneration loop* and the *rubric*. None of them is specific to the generator that produced the question, so `qpol_3` inherits all of them unmeasured |
| **§3 — historical** | Findings about `PROBE_BRIEFS` and probe-level yield. These describe a path that only runs under `FORENSIC_QUESTIONS=false`. Kept because the *mechanism* they identify recurs, and because §3.3 is still live code |

**Nothing here has been re-measured against `qpol_3`.** That is the single
largest gap in the project's evaluation coverage and §4 says what it would cost.

---

## 1. Findings that survive the generator change

### 1.1 Regeneration by deletion — the loop actively degrades questions

**11 of 58 regenerations (19%) were "fixed" by deleting words and adding
nothing.** Verbatim from the corpus:

```
BEFORE (rejected: answer_leakage)   How long did you manage the team of 35 agents?
AFTER  (accepted)                   How long did you manage the team of agents?

BEFORE (rejected: answer_leakage)   What steps did you take each morning to manage your 60 accounts?
AFTER  (accepted)                   What steps did you take each morning to manage your accounts?
```

The first pair is not merely no better — it is **ungrammatical and strictly less
informative**, and the validator accepted it.

> The regeneration loop optimises for rule compliance, and compliance is
> orthogonal to evidence. A filter that can only subtract will, when pushed, be
> satisfied by subtraction.

**This is an argument that question value must be caused at generation and
cannot be recovered at validation** — not an argument for a better rule.
Source: `archive/PROBE_LEVEL_FORENSIC_AUDIT.md` §4b.

### 1.2 The validator has no rule for discriminative power

All seven rules test **structural validity**: does the question echo a figure,
repeat an earlier question, name two metrics, pose a hypothetical, invent a
number, drift scope, fail to anchor. **None asks whether the answer is worth
having.**

*"How long did the REST API integration project take?"* passes all seven.
**In the corpus this shape is 55 of 519 attempts — 10.6%.**
Source: `archive/PROBE_LEVEL_FORENSIC_AUDIT.md` §4a.

### 1.3 Where the regeneration budget actually goes

Path frequency, n = 395 asked:

| source | n | % |
|---|---:|---:|
| `model` — accepted first try | 304 | 77.0% |
| `regenerated` — accepted second try | 58 | 14.7% |
| `fallback` — both attempts rejected, or the call failed | 33 | 8.4% |

Attempt-1 reject rate **23.0%**; attempt-2 reject rate **36.3%**. So
**regeneration rescues 63.7% of rejected questions** and the remaining third
fall through to the fallback.

Rule fires across all 519 attempts (127 violations):

| rule | fires | % | attempt 1 | attempt 2 |
|---|---:|---:|---:|---:|
| `answer_leakage` | 55 | 43.3% | 45 | 10 |
| `duplicate_content` | 40 | 31.5% | 25 | 15 |
| `no_claim_anchor` | 14 | 11.0% | 10 | 4 |
| `multiple_fact_targets` | 9 | 7.1% | 8 | 1 |
| `scope_drift` | 5 | 3.9% | 3 | 2 |
| `unsupported_metric` | 4 | 3.1% | 2 | 2 |
| `hypothetical_misuse` | **0** | 0% | 0 | 0 |

Two things to carry forward:

- **`duplicate_content` gets relatively worse under regeneration** — 6.3% of
  attempt-1 drafts vs 16.5% of attempt-2 drafts. The retry hint *"this repeats
  an earlier question; ask something new"* is the least effective of the seven.
- **`hypothetical_misuse` fired zero times in 519 attempts.** That is evidence
  gpt-4o does not make the mistake, **not** evidence the rule is wrong.
  `docs/PHASE_3_VALIDATION_STUDY.md` §11 says why it stays.

### 1.4 The fallback is not a defect

Measured **no worse than generated questions — mildly better**. It has been
suspected of being the quality leak in three separate audits and has been
cleared in each. Source: `archive/QUESTION_GENERATION_AUDIT.md` §E3.

### 1.5 CAUSAL_REASONING has no owner, and no prompt change will reach it

Lowest dimension corpus-wide at **34.1 mean across 273 rows**. DECISION targets
it and scores 29.2; OUTCOME targets it and scores 28.0; the difference is
**−1.2, t = −0.25, CI [−10.5, 8.1]** — a confidence interval straddling zero.

**No question type in the corpus produces causal reasoning.** This is a rubric
or signal-extractor problem one layer below question generation. Flagged
explicitly so it is not mistaken for a prompt failure and chased with a prompt
change. Source: `archive/QUESTION_GENERATION_AUDIT.md` §D3.3,
`archive/PROBE_LEVEL_FORENSIC_AUDIT.md` §4c.

### 1.6 The definition-quiz class is empty, and that is the layer working

**Zero definition-quiz questions in 519 attempts.** No *"what is AHT"*, no
*"explain the difference between"*, no *"what's the formula for"*. The prompt
rule — *"never a definition quiz… we are testing whether they did the work, not
whether they memorised definitions"* — works perfectly.

**Do not touch it.** Source: `archive/PROBE_LEVEL_FORENSIC_AUDIT.md` §3.

### 1.7 Two structural rules tested and found neutral

| test | result |
|---|---|
| Compound ("and") vs single-ask questions | 5.94 vs 6.09 signals, t = −0.48. **No effect.** The prompt's "one answerable thing" rule is a UX/WhatsApp rule, not an evidence rule |
| Longer (>11 words) vs shorter questions | 6.26 vs 5.67, t = 2.15. Weak, marginal, not actionable |

---

## 2. The finding the whole cluster exists to state

**24.9% of all answers contain zero hard-to-invent evidence.** One turn in four
produces nothing a copier could not have fabricated.

And the corpus ranks probe levels differently depending on which product you
think you are building:

| level | total signals | rank | hard-to-invent | rank |
|---|---:|---:|---:|---:|
| OPERATIONAL | 7.44 | **1** | 0.90 | 4 |
| OUTCOME | 6.46 | 2 | 1.54 | 2 |
| INCIDENT | 6.23 | 3 | **1.77** | **1** |
| VALIDATION | 5.49 | 4 | 0.82 | 5 |
| DECISION | 5.04 | 5 | 1.06 | 3 |

> **skill lens:** OPERATIONAL > OUTCOME > INCIDENT > VALIDATION > DECISION
> **authorship lens:** INCIDENT > OUTCOME > DECISION > OPERATIONAL > VALIDATION

**The two best levels under one goal are 3rd and 4th under the other.** Choosing
authorship verification over skill assessment is not a matter of degree — it
reorders which probes are worth the budget. Source:
`archive/PROBE_LEVEL_FORENSIC_AUDIT.md` §2, `archive/PROBE_ARCHITECTURE_FACTUAL_AUDIT.md`.

This is the measurement the forensic generator was built on, and it is why
`FORENSIC_QUESTIONS` defaults to true.

---

## 3. Historical — the probe-brief generator (`FORENSIC_QUESTIONS=false` only)

### 3.1 Question type and probe level were the same variable

The category × level cross-tab was near-diagonal (n = 395): VALIDATION produced
86 of 92 metadata questions and **no other level leaked metadata at all**. Two
consequences, both still worth knowing: a brief fully determines its level's
question style, and no analysis on this corpus can separate "question type" from
"probe level" as causes.

### 3.2 Asking *how* a metric was produced beat asking *how big* it was, 2.1×

The best-powered result in the cluster:

| dimension | winner | loser | diff | t | 95% CI | n |
|---|---|---|---:|---:|---|---|
| METRIC_OWNERSHIP | metrics **53.6** | metadata 25.3 | +28.3 | 7.13 | [20.5, 36.1] | 60/67 |
| SPECIFICITY | metadata **54.3** | failure 30.4 | +23.9 | 6.64 | [16.8, 30.9] | 67/67 |
| PROCESS | process **93.6** | decision 70.7 | +22.9 | 5.10 | [14.1, 31.7] | 60/49 |

Metadata questions were not useless — they were **narrow**. Best source of
SPECIFICITY (54.3), worst of METRIC_OWNERSHIP (25.3), lowest signals/answer of
any non-decision category, and by far the shortest answers (271 chars vs
385–409).

### 3.3 The defect string is still in the code

`PROBE_BRIEFS[ProbeLevel.VALIDATION]` at
[api/engine/question.py:76-80](../api/engine/question.py#L76-L80) still reads
*"Ask for the shape of it: how many, how long, who else was involved, what the
numbers were"* — the exact instruction three audits identified as the primary
cause of metadata questions. The measured replacement is in
`archive/QUESTION_QUALITY_REVIEW.md` §6, with an ablation on the same two
claims:

| | shipped brief | proposed brief |
|---|---|---|
| First-attempt rejects | 13/16 (81%) | 7/16 (44%) |
| Fallbacks | 5/16 (31%) | **0/16 (0%)** |
| Questions asking how the figure was produced | 0/16 | **16/16** |

**It was never applied**, and the reason it now looks unimportant is that the
path is off by default — not that it was fixed. If `FORENSIC_QUESTIONS` is ever
flipped back, this is live again. One dict entry, one file, owner A.

### 3.4 Ruled out with numbers

Claim extraction and classification were investigated as the source of question
quality and **ruled out**: `archive/QUESTION_GENERATION_AUDIT.md` §B4, and the
addendum to `archive/QUESTION_QUALITY_REVIEW.md` which measured a proposed
extraction prompt as **worse** than the one already shipped.

### 3.5 Measured absences

- **EXCLUSION questions: 0 of 395.** **DEPENDENCY: 1. PEOPLE: 2.**
- **SEAM had no analogue** — no probe level cross-referenced two prior answers.
- **Contradiction detection was untested at this corpus size:** 16 repeat-key
  opportunities, 1 fire, 0 true positives.

---

## 4. What is not measured, and what it would cost

**The live generator has never been measured.** `qpol_3` ships on the strength
of §2 — an argument about which *probe levels* pay, made on data from a
different generator. Nothing establishes that the Move ladder realises that
argument in the questions it actually produces.

The instrument already exists: `scripts/interview_study.py` drives real
interviews and instruments generation from outside, and it wrote every number in
this file. Re-pointing it at `FORENSIC_QUESTIONS=true` reproduces the corpus for
roughly the same cost (**$3.67 for 519 questions**). The comparison that matters
is §2's hard-to-invent column and §1.1's deletion rate, `qpol_2` vs `qpol_3`.

**Two things that must not happen while that runs** — counter-metrics C6 and C7
of `PHASE_3_VALIDATION_STUDY.md`: do not add corpus entries reactively, and do
not tune `DUPLICATE_JACCARD` or the stopword lists. Both fit the model to the
test set while making the result look better.

---

## Source audits

All in [`archive/`](archive/), superseded by this file for findings but
authoritative for method, derivation and worked examples.

| Document | What only it has |
|---|---|
| `QUESTION_GENERATION_AUDIT.md` | The full cross-tab, the evidence matrix, §D's confounding argument, and the reproduction recipe |
| `PROBE_LEVEL_FORENSIC_AUDIT.md` | Ten verbatim corpus examples with per-question signal counts; the hard-to-invent instrument |
| `PROBE_ARCHITECTURE_FACTUAL_AUDIT.md` | Per-level factual measurements with no recommendations; the 10 strongest and 10 weakest question patterns |
| `QUESTION_GENERATION_DESIGN_AUDIT.md` | Stage-by-stage owns/should-own/leaking analysis; the minimum architectural change and why it is legitimate |
| `QUESTION_QUALITY_REVIEW.md` | The four-ablation forensic review on one real resume, and the extraction-prompt addendum |
| `QUESTION_SYSTEM_AUDIT.md` | Move inventory and seniority audit against real post-Demo-Mode logs |
| `QUESTION_DIVERSITY_AUDIT.md` | Where repetition comes from: the shared instruction line, the fixed fallback strings, and `duplicate_content`'s single-interview scope |

Still live, not archived, because code cites them:
[`QUESTION_EVAL_HARNESS_AND_LEVEL_MODEL.md`](QUESTION_EVAL_HARNESS_AND_LEVEL_MODEL.md)
(5 citations from `api/`) and [`QUESTIONING_PHILOSOPHY.md`](QUESTIONING_PHILOSOPHY.md),
which is the design argument these audits test.
