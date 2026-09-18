# Coverage and Evidence Yield Audit

**2026-09-18.** Local `proofscreen.sqlite3`, seeded 2026-09-16, `2659f20`.
**8 sessions, 48 questions, 48 responses, `llm_mode: fixture` throughout** (no
`OPENAI_API_KEY` set — every number below is the heuristic extractor, not the
live model. See §4).

**Method.** Coverage is read from `evaluations.dimension_profile_json` (the
`probed` flag Python already computes, not re-derived) and cross-checked
against `evidence` rows. Evidence Yield reruns
`scripts/audit_evidence_yield.py`, whose output at
`studies/evidence_yield/evidence_yield_report.md` **has been overwritten** by
this run — the previous file was dated 2026-09-08, seven days before this
database was seeded, and its 4-candidate/23-turn sample is a strict subset of
what exists now (8 candidates/48 turns). If you need the Sep-8 numbers, they
are in git history.

---

## Part 1 — Coverage: which dimensions actually get probed

### 1.1 The headline finding

**JUDGMENT is never probed in 6 of 8 evaluations (75%), and this is not a
budget problem — it is a seniority gate that no candidate in this corpus can
pass.**

```
KNOWLEDGE        probed 7/8   never-probed 1/8   probed-but-scored-0 2/7
EXECUTION        probed 8/8   never-probed 0/8   probed-but-scored-0 0/8
PROBLEM_SOLVING  probed 8/8   never-probed 0/8   probed-but-scored-0 4/8
JUDGMENT         probed 2/8   never-probed 6/8   probed-but-scored-0 0/2
OWNERSHIP        probed 7/8   never-probed 1/8   probed-but-scored-0 3/7
ADAPTABILITY     probed 7/8   never-probed 1/8   probed-but-scored-0 1/7
```

### 1.2 Root cause, traced through the code

Under the live question policy (`qpol_3`, forensic moves), exactly one move is
tagged as JUDGMENT-targeting:

```python
# api/engine/question.py:1159
Move.AUTHORITY.value: (Dimension.CAUSAL_REASONING, Dimension.JUDGMENT),
```

`AUTHORITY` is the only door into JUDGMENT under the current policy. And:

```python
# api/engine/question.py:1094-1096
LEVEL_RESTRICTED: dict[Move, frozenset[str]] = {
    Move.AUTHORITY: frozenset({"mid", "senior"}),
    Move.EXCLUSION: frozenset({"senior"}),
    Move.PERTURB: frozenset({"senior"}),
}

# api/engine/question.py:1114-1115  (level_appropriate)
if seniority is None:
    return False
```

**Unknown seniority is blocked, not defaulted open** — a deliberate choice,
commented at `orchestrator.py:352-364`, made for good reasons (an honest "not
much was mine to decide" from a junior reads identically to evasion on
AUTHORITY specifically).

**Every candidate in this database has `candidate.seniority = None`** —
confirmed directly: `Counter({None: 8})` over all 8 rows. Nothing in the
current pipeline populates it from `extract.py`'s resume classification into
the `candidates` table for these sessions. The consequence: **the only
JUDGMENT-opening move is permanently locked for 100% of the candidates this
corpus has ever produced**, independent of interview length, claim quality, or
what the candidate actually says.

**This is a coverage defect masquerading as a scoring defect.** A recruiter
reading "JUDGMENT: 0, not probed" reasonably assumes the interview ran out of
turns before reaching it. It didn't reach it because it structurally *cannot*,
for any candidate whose seniority was never classified — which per
`extract._normalise_seniority` includes anyone the header classifier reads as
ambiguous or too thin, not just a deliberate "junior" case.

**Compare: `PERTURB` is also in `LEVEL_RESTRICTED` at `senior`-only, and it
still fired 7 times in this same corpus.** It is exempted through a separate
code path (`orchestrator.py`'s stall-branch handling, outside
`forensic_moves_left`'s demo-mode gate, which checks only `EXCLUSION` and
`AUTHORITY` — `orchestrator.py:369`). So the codebase already has a precedent
for "let this move through despite the seniority gate when a null seniority
would otherwise strand it." AUTHORITY has no equivalent exemption.

### 1.3 PROBLEM_SOLVING: probed everywhere, empty most places

```
17 of 23 PROBLEM_SOLVING evidence rows scored 0.
basis (every zero row, identical): "Capped at 45: no incident marker or
causal chain provided"
```

Unlike JUDGMENT this is not a reachability problem — every claim gets a shot at
PROBLEM_SOLVING (INCIDENT/FAILURE moves fire constantly, 8 FAILURE + 3 INCIDENT
in this corpus). It fails downstream: the gate requires an `incident_marker` or
a *complete* `causal_link` (cause + action + outcome, not partial), and
§2.2's fixture-mode extraction produces `causal_links` with `outcome: null`
more often than not (documented directly in
[DEEP_DIVE.md](../../docs/DEEP_DIVE.md) §2.1 on this exact corpus). **The
combination of §1.2 and §1.3 means two of six competence dimensions are
close to unreadable in this database for reasons that have nothing to do
with candidate quality**: JUDGMENT because it cannot be reached, PROBLEM_SOLVING
because the extractor rarely completes the chain that opens it.

### 1.4 Per-evaluation gap table

| Evaluation | Candidate | Competence | Role coverage | Never-probed | Probed-but-scored-0 |
|---|---|---:|---:|---|---|
| `ev_cd53a2e73d` | c_c04236 | 14 | 60% | JUDGMENT | KNOWLEDGE, PROBLEM_SOLVING, OWNERSHIP, ADAPTABILITY |
| `ev_941a381206` | c_66be86 | 15 | 55% | JUDGMENT, ADAPTABILITY | PROBLEM_SOLVING, OWNERSHIP |
| `ev_9fd012c2cf` | c_64b77a | 9 | 60% | KNOWLEDGE, JUDGMENT, OWNERSHIP | — |
| `ev_0fda8075e8` | c_1266f0 | 21 | 60% | JUDGMENT | KNOWLEDGE, OWNERSHIP |
| `ev_ea303895ff` | c_b90f6b | 24 | 60% | JUDGMENT | PROBLEM_SOLVING |
| `ev_a1cff52a1e` | c_602bd5 | 26 | 55% | JUDGMENT | PROBLEM_SOLVING |
| `ev_60eba57118` | c_d79878 | 14 | 60% | — | — |
| `ev_d660b32258` | c_2d266f | **38** | 60% | — | — |

**`role_coverage` (55–60% across the board) never reflects the JUDGMENT gap at
all** — it is computed from claim-type-to-role-requirement matching
(`job_fit.py`), which is a different notion of coverage from
"dimension actually probed." A recruiter reading 60% role coverage has no
signal that one-sixth of the competence framework was structurally
unreachable underneath that number.

**The two evaluations with no gaps** (`c_d79878`, `c_2d266f`) are not
better-covered by design — they are the two whose specific claim archetypes
and answer content happened to open every gate this interview reached. That is
a property of what was asked and answered, not of the candidate.

---

## Part 2 — Evidence Yield: which questions earn their turn

Rerun of `scripts/audit_evidence_yield.py` (ΔE = total signals after the turn
minus total signals before it, merged across all of that claim's answers so
far). Full turn-by-turn table:
[`studies/evidence_yield/evidence_yield_report.md`](../evidence_yield/evidence_yield_report.md).

### 2.1 By move (n = 48 turns, i.e. all responses in the corpus)

| Move | n | Avg ΔE | Max ΔE | Yield |
|---|---:|---:|---:|---|
| `OUTCOME` (probe level, no move) | 1 | 10.00 | 10 | HIGH |
| `METRIC_DEFINITION` | 5 | 5.20 | 8 | HIGH |
| `PEOPLE` | 6 | 4.83 | 10 | HIGH |
| `FAILURE` | 8 | 4.75 | 9 | HIGH |
| `INCIDENT` (probe level, no move) | 3 | 4.00 | 10 | HIGH |
| `OPERATING_CONTEXT` | 12 | 3.83 | 8 | HIGH |
| `PERTURB` | 7 | 3.43 | 10 | HIGH |
| `OPERATIONAL` | 6 | 2.00 | 5 | MODERATE |

### 2.2 By probe level — the same corpus, the other axis

| Probe level | n | Avg signals/answer |
|---|---:|---:|
| OUTCOME | 6 | 6.17 |
| INCIDENT | 17 | 4.88 |
| TRANSFER | 7 | 3.57 |
| OPERATIONAL | 18 | 3.28 |

**No probe level under-performs badly.** The worst average (OPERATIONAL, 3.28)
is still well above zero, and the earlier Phase 3 finding that OPERATIONAL is
"high volume, low forensic value" (many signals, low hard-to-invent share)
still applies — this corpus measures volume, not hard-to-invent-ness, which
`hard-to-invent` needs a separate instrument (`archive/PROBE_LEVEL_FORENSIC_AUDIT.md`).

### 2.3 Dead turns

**6 of 48 answers (12.5%) produced zero signals.** All six are the memory-exhaustion
pattern already documented in CLAUDE.md ("I don't remember the details...") —
correctly scored 0 without penalty rather than triggering a repair turn, per
`is_memory_exhausted_or_skip()`. This is the mechanism working as designed, not
a defect; flagged here only because it is the other half of "why some
dimensions read empty" alongside §1.2/§1.3.

### 2.4 A labeling gap in the audit script itself

`scripts/audit_evidence_yield.py` groups by `candidate.name`, and this seed has
**two candidates each named Maya Krishnan, Arjun Mehta, Priya Raghavan and
Rohit Verma** (re-seeded twice, distinct `candidate_id`s). The regenerated
report has duplicate-looking rows under identical names with different
`session_id`s. Not fixed here — flagged so it isn't misread as double-counted
data. The script should key its report by `candidate_id` (or `session_id`), not
by name.

---

## Part 3 — What this means, combined

1. **The JUDGMENT gap in §1.2 is the single highest-leverage fix in this
   audit.** It is not a prompt problem and not an evidence-extraction problem —
   it is a data-flow gap: `candidate.seniority` is never populated for any
   candidate this corpus has produced, which silently disables one-sixth of the
   Universal Competence Framework for the entire product. Populating it (or
   exempting `AUTHORITY` the same way `PERTURB` is already exempted) is a small,
   scoped change with a large coverage payoff.
2. **PROBLEM_SOLVING's emptiness is an evidence-extraction problem, and it will
   not be fixed by asking better questions** — FAILURE and INCIDENT already
   fire constantly. It needs either a more complete heuristic extractor or,
   more honestly, a live-model comparison (§4) before concluding anything about
   the *questions*.
3. **Nothing in Evidence Yield (Part 2) is broken.** Every move and every probe
   level clears the "HIGH" or "MODERATE" bar on volume. The product's yield
   problem, per the Phase 3 corpus, was never volume — it was **hard-to-invent
   share**, a different measurement this study does not make.

## 4. The caveat that applies to all of the above

**Every number in this document was produced by the heuristic fallback
extractor, not the live model.** `llm_mode: fixture` on all 8 evaluations,
confirmed by query. CLAUDE.md is explicit that fallbacks are "deliberately
more conservative than real extraction" — so §1.3's PROBLEM_SOLVING emptiness
and the ΔE magnitudes in Part 2 may both look different against `gpt-4o`
output. The JUDGMENT finding in §1.2 is different in kind: it is a
**seniority-field data-flow gap**, not an extraction-quality gap, so it holds
regardless of which extractor produced the answers.

## Reproducing

```bash
python scripts/audit_evidence_yield.py     # Part 2, ~instant, no model calls
```

Part 1 has no script yet — it was three direct SQL queries against
`evaluations.dimension_profile_json`, run inline for this report. Worth
promoting to a `scripts/audit_coverage.py` companion if this becomes a
recurring check (mirrors the existing `audit_evidence_yield.py` pattern).
