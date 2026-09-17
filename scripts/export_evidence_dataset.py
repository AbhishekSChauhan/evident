"""
Export the seven analysis datasets requested for external review of the
interview/evidence pipeline, plus the single combined dataset they all derive
from.

Read-only. Makes no model calls. Runs against whatever DATABASE_URL is set --
local sqlite for a dry run, the production Postgres for the real export:

    # local dry run (sqlite, whatever's in the working tree)
    python scripts/export_evidence_dataset.py

    # against production, from inside the API container or with the port
    # published to the host (docker-compose already publishes 5432)
    DATABASE_URL="postgresql+asyncpg://proofscreen:<password>@localhost:5432/proofscreen" \\
        python scripts/export_evidence_dataset.py

Writes to studies/evidence_export/:

    00_full_dataset.json           every candidate with a finalized evaluation,
                                    full nested trace. THE dataset -- everything
                                    else below is a derived view of this file.
    01_traces_sample_20.json        20 traces selected for facet diversity
    01_selection_rationale.md       why each of the 20 was picked
    02_claim_prioritization.json    all_claims / selected_claims / never_interviewed
                                    per candidate, plus a note on what "rejected"
                                    can and can't mean (see the docstring on
                                    `build_claim_prioritization` below)
    03_evidence_yield_per_question.csv
    04_dimension_coverage_matrix.csv
    05_top_50_questions.csv
    06_top_50_evidence_records.csv
    07_coverage_statistics.md

Every number here is read from stored rows. Nothing is re-derived by calling
into engine/scoring.py or engine/signals.py -- if this script's counts disagree
with what the API reports for the same candidate, that is itself a finding
worth having, not a bug in this script.
"""

from __future__ import annotations

import asyncio
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from api.db import SessionLocal  # noqa: E402
from api.models import (  # noqa: E402
    Candidate,
    Claim,
    ClaimScore,
    Evaluation,
    Evidence,
    Question,
    Resume,
    Response,
)

OUT_DIR = ROOT / "studies" / "evidence_export"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DIMS = ["KNOWLEDGE", "EXECUTION", "PROBLEM_SOLVING", "JUDGMENT", "OWNERSHIP", "ADAPTABILITY"]
DIM_INITIAL = {"KNOWLEDGE": "K", "EXECUTION": "E", "PROBLEM_SOLVING": "PS",
               "JUDGMENT": "J", "OWNERSHIP": "O", "ADAPTABILITY": "A"}

LEADERSHIP_HINT = re.compile(r"\b(lead|leader|manager|head|director|principal|chief|vp)\b", re.I)


# ---------------------------------------------------------------------------
# One full trace per candidate with a finalized evaluation
# ---------------------------------------------------------------------------

@dataclass
class Trace:
    candidate_id: str
    candidate_name: str
    job_family: str
    role_text: str | None
    seniority: str | None
    resume_excerpt: str
    claims: list[dict] = field(default_factory=list)
    evaluation: dict | None = None


async def fetch_all_traces(db: AsyncSession) -> list[Trace]:
    """One Trace per (candidate, finalized evaluation). A candidate re-seeded
    or re-interviewed more than once yields one trace per finalized
    evaluation, keyed by session -- matching `evaluations.session_id UNIQUE`."""
    evaluations = (
        (await db.execute(select(Evaluation).where(Evaluation.status == "finalized")))
        .scalars()
        .all()
    )

    traces: list[Trace] = []
    for ev in evaluations:
        candidate = await db.get(Candidate, ev.candidate_id)
        if candidate is None:
            continue

        resume = (
            (await db.execute(select(Resume).where(Resume.candidate_id == candidate.id)))
            .scalars()
            .first()
        )
        claims = (
            (
                await db.execute(
                    select(Claim)
                    .where(Claim.candidate_id == candidate.id)
                    .order_by(Claim.order_index)
                )
            )
            .scalars()
            .all()
        )

        claim_dicts = []
        for cl in claims:
            qa_rows = (
                await db.execute(
                    select(Question, Response)
                    .join(Response, Response.question_id == Question.id)
                    .where(Question.claim_id == cl.id, Question.session_id == ev.session_id)
                    .order_by(Question.order_index)
                )
            ).all()

            turns = []
            for q, r in qa_rows:
                ev_rows = (
                    (await db.execute(select(Evidence).where(Evidence.response_id == r.id)))
                    .scalars()
                    .all()
                )
                turns.append({
                    "question_id": q.id,
                    "order_index": q.order_index,
                    "probe_level": q.probe_level,
                    "move": q.move,
                    "source": q.source,
                    "is_repair": q.is_repair,
                    "question_text": q.text,
                    "answer_text": r.answer_text,
                    "answered_by": r.answered_by,
                    "signals_found": r.signals_found,
                    "answer_score": r.answer_score,
                    "evidence": [
                        {
                            "dimension": e.dimension,
                            "score": e.score,
                            "basis": e.basis,
                            "quotes": json.loads(e.quotes_json or "[]"),
                        }
                        for e in ev_rows
                    ],
                })

            score_row = (
                (await db.execute(select(ClaimScore).where(ClaimScore.claim_id == cl.id)))
                .scalars()
                .first()
            )
            claim_dicts.append({
                "claim_id": cl.id,
                "order_index": cl.order_index,
                "claim_type": cl.claim_type,
                "metric": cl.metric,
                "text": cl.text,
                "interviewed": len(turns) > 0,
                "turns": turns,
                "claim_score": score_row.score if score_row else None,
                "probed_dimensions": score_row.probed_dimensions if score_row else None,
                "answers_count": score_row.answers_count if score_row else None,
            })

        traces.append(Trace(
            candidate_id=candidate.id,
            candidate_name=candidate.name,
            job_family=candidate.job_family,
            role_text=candidate.role,
            seniority=candidate.seniority,
            resume_excerpt=(resume.raw_text[:600] if resume else ""),
            claims=claim_dicts,
            evaluation={
                "evaluation_id": ev.id,
                "session_id": ev.session_id,
                "resume_score": ev.resume_score,
                "weighted_evidence_score": ev.weighted_evidence_score,
                "competence_score": ev.competence_score,
                "badge": ev.badge,
                "consistency_score": ev.consistency_score,
                "contradiction_count": ev.contradiction_count,
                "role_coverage": ev.role_coverage,
                "claims_scored": ev.claims_scored,
                "questions_asked": ev.questions_asked,
                "dimension_profile": json.loads(ev.dimension_profile_json or "[]"),
                "llm_mode": ev.llm_mode,
                "evaluation_version": ev.evaluation_version,
            },
        ))
    return traces


def trace_to_dict(t: Trace) -> dict:
    return {
        "candidate_id": t.candidate_id,
        "candidate_name": t.candidate_name,
        "job_family": t.job_family,
        "role_text": t.role_text,
        "seniority": t.seniority,
        "resume_excerpt": t.resume_excerpt,
        "claims": t.claims,
        "evaluation": t.evaluation,
    }


# ---------------------------------------------------------------------------
# Priority 1 -- 20 candidates selected for facet diversity
# ---------------------------------------------------------------------------

def select_20(traces: list[Trace]) -> tuple[list[Trace], list[str]]:
    """Greedy facet-coverage pick, not random and not a top-N slice. Facets:
    strength tertile (by competence_score), job_family, and a leadership
    proxy read off the free-text `role` field (there is no leadership family
    in the taxonomy and no reliable seniority field -- see the coverage
    audit's JUDGMENT finding for why `seniority` can't be used as a facet).
    """
    if len(traces) <= 20:
        return list(traces), [f"Only {len(traces)} finalized evaluations exist; took all of them."]

    scored = sorted(traces, key=lambda t: t.evaluation["competence_score"])
    n = len(scored)
    tertile = n // 3
    strength = {}
    for i, t in enumerate(scored):
        strength[t.candidate_id] = "weak" if i < tertile else ("strong" if i >= 2 * tertile else "mid")

    def facets(t: Trace) -> set[str]:
        f = {f"strength:{strength[t.candidate_id]}", f"family:{t.job_family}"}
        if t.role_text and LEADERSHIP_HINT.search(t.role_text):
            f.add("leadership")
        return f

    remaining = list(traces)
    picked: list[Trace] = []
    rationale: list[str] = []
    covered: set[str] = set()

    while remaining and len(picked) < 20:
        remaining.sort(key=lambda t: -len(facets(t) - covered))
        best = remaining.pop(0)
        new_facets = facets(best) - covered
        rationale.append(
            f"{best.candidate_id} ({best.candidate_name}): picked for "
            f"{sorted(new_facets) if new_facets else sorted(facets(best))}"
            f"{' -- no new facet, filling quota' if not new_facets else ''}"
        )
        covered |= facets(best)
        picked.append(best)

    return picked, rationale


# ---------------------------------------------------------------------------
# Priority 2 -- claim prioritization
# ---------------------------------------------------------------------------

def build_claim_prioritization(traces: list[Trace]) -> dict:
    """`all_claims` is every row in the `claims` table for that candidate --
    which is already the KEPT list after extraction ranks candidates by
    `claim_type` weight + `claim_strength_bonus` and truncates to
    `settings.max_claims` (`extract.py:501-507`).

    `rejected_claims`, in the sense of "claims the model proposed but the
    ranker discarded before storage," CANNOT be reconstructed from the
    database. `extract_claims` computes that list (`extract.py:657` on) and
    LOGS it (`extract.py:756-760`) but never returns or persists it -- the
    function signature is `-> tuple[job_family, claims, seniority]`, full
    stop. Unless application logs from the original extraction call were
    retained, that data no longer exists. If this is worth having going
    forward, the fix is one field: persist `rejected` as a JSON column on
    the resume or session row at the point `extract_claims` returns.

    What IS answerable from stored data, and is reported here instead:
    `selected_claims` (>=1 question actually asked against it) vs
    `never_interviewed` (stored, but the question budget never reached it).
    """
    out = {}
    for t in traces:
        selected = [c for c in t.claims if c["interviewed"]]
        never = [c for c in t.claims if not c["interviewed"]]
        out[t.candidate_id] = {
            "candidate_name": t.candidate_name,
            "all_claims": [
                {"claim_id": c["claim_id"], "order_index": c["order_index"],
                 "claim_type": c["claim_type"], "metric": c["metric"], "text": c["text"]}
                for c in t.claims
            ],
            "selected_claims": [c["claim_id"] for c in selected],
            "never_interviewed": [c["claim_id"] for c in never],
            "rejected_at_extraction": (
                "NOT RECOVERABLE from the database -- see docstring; "
                "extract.py logs but never persists this list"
            ),
        }
    return out


# ---------------------------------------------------------------------------
# Priority 3 -- evidence yield per question
# ---------------------------------------------------------------------------

def build_evidence_yield_csv(traces: list[Trace], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "claim_id", "claim_type", "question_id",
                    "order_index", "probe_level", "move", "source",
                    "question_text", "answer_text", "signals_found", "answer_score"])
        for t in traces:
            for c in t.claims:
                for turn in c["turns"]:
                    w.writerow([
                        t.candidate_id, c["claim_id"], c["claim_type"],
                        turn["question_id"], turn["order_index"], turn["probe_level"],
                        turn["move"], turn["source"], turn["question_text"],
                        turn["answer_text"], turn["signals_found"], turn["answer_score"],
                    ])


# ---------------------------------------------------------------------------
# Priority 4 -- dimension coverage matrix
# ---------------------------------------------------------------------------

def build_coverage_matrix_csv(traces: list[Trace], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "candidate_name"] + DIMS + ["competence_score", "role_coverage"])
        for t in traces:
            profile = {d["dimension"]: d for d in t.evaluation["dimension_profile"]}
            row = [t.candidate_id, t.candidate_name]
            for d in DIMS:
                entry = profile.get(d)
                if entry is None:
                    row.append("?")
                elif entry["probed"]:
                    row.append("check" if entry["score"] > 0 else "probed-zero")
                else:
                    row.append("x")
            row += [t.evaluation["competence_score"], t.evaluation["role_coverage"]]
            w.writerow(row)


# ---------------------------------------------------------------------------
# Priority 5 -- top 50 questions by frequency (template collapse detector)
# ---------------------------------------------------------------------------

def build_top_questions_csv(traces: list[Trace], path: Path, n: int = 50) -> None:
    counter: Counter[tuple[str, str, str]] = Counter()
    for t in traces:
        for c in t.claims:
            for turn in c["turns"]:
                counter[(turn["question_text"], turn["probe_level"], c["claim_type"])] += 1

    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["frequency", "question_text", "probe_level", "claim_type"])
        for (text, probe, ctype), count in counter.most_common(n):
            w.writerow([count, text, probe, ctype])


# ---------------------------------------------------------------------------
# Priority 6 -- top 50 evidence records by score (quality spot-check)
# ---------------------------------------------------------------------------

def build_top_evidence_csv(traces: list[Trace], path: Path, n: int = 50) -> None:
    rows = []
    for t in traces:
        for c in t.claims:
            for turn in c["turns"]:
                for ev in turn["evidence"]:
                    rows.append({
                        "candidate_id": t.candidate_id,
                        "claim_text": c["text"][:120],
                        "question_text": turn["question_text"],
                        "answer_text": turn["answer_text"],
                        "dimension": ev["dimension"],
                        "score": ev["score"],
                        "basis": ev["basis"],
                        "quotes": " | ".join(ev["quotes"]),
                    })
    rows.sort(key=lambda r: -r["score"])
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["candidate_id", "claim_text", "question_text", "answer_text",
                    "dimension", "score", "basis", "quotes"])
        for r in rows[:n]:
            w.writerow([r["candidate_id"], r["claim_text"], r["question_text"],
                        r["answer_text"], r["dimension"], r["score"], r["basis"], r["quotes"]])
    return rows  # also handed to the stats section below


# ---------------------------------------------------------------------------
# Priority 7 -- coverage statistics
# ---------------------------------------------------------------------------

def build_stats_md(traces: list[Trace], all_evidence_rows: list[dict]) -> str:
    n_cand = len(traces)
    n_claims = sum(len(t.claims) for t in traces)
    n_questions = sum(len(c["turns"]) for t in traces for c in t.claims)
    n_responses = n_questions  # one response per asked question in this export
    n_evidence = sum(len(turn["evidence"]) for t in traces for c in t.claims for turn in c["turns"])

    dim_probed = Counter()
    dim_total = 0
    for t in traces:
        for d in t.evaluation["dimension_profile"]:
            dim_total += 1
            if d["probed"]:
                dim_probed[d["dimension"]] += 1

    zero_signal = sum(
        1 for t in traces for c in t.claims for turn in c["turns"] if turn["signals_found"] == 0
    )

    lines = [
        "# Coverage statistics",
        "",
        f"- Candidates (finalized evaluations): **{n_cand}**",
        f"- Claims: **{n_claims}** -- avg **{n_claims/n_cand:.2f}** per candidate" if n_cand else "",
        f"- Questions asked: **{n_questions}** -- avg **{n_questions/n_cand:.2f}** per candidate" if n_cand else "",
        f"- Evidence rows: **{n_evidence}** -- avg **{n_evidence/n_responses:.2f}** per response" if n_responses else "",
        f"- Zero-signal answers: **{zero_signal}/{n_responses}** ({100*zero_signal/n_responses:.1f}%)" if n_responses else "",
        "",
        "## Dimension probe rate across the corpus",
        "",
        "| Dimension | Probed | Total | Rate |",
        "|---|---:|---:|---:|",
    ]
    for d in DIMS:
        p = dim_probed[d]
        t_ = n_cand
        lines.append(f"| {d} | {p} | {t_} | {100*p/t_:.0f}% |" if t_ else f"| {d} | {p} | 0 | -- |")

    lines += [
        "",
        "Compare these against the numbers you already estimated from the CSV",
        "exports -- if they disagree, one of the two counting methods (this",
        "script's stored-row count vs. a spreadsheet formula over exported CSVs)",
        "has a bug, and that mismatch is worth finding before trusting either.",
    ]
    return "\n".join(l for l in lines if l is not None) + "\n"


# ---------------------------------------------------------------------------

async def main() -> int:
    async with SessionLocal() as db:
        traces = await fetch_all_traces(db)

    if not traces:
        print("No finalized evaluations found. Nothing to export.")
        return 1

    print(f"Found {len(traces)} finalized evaluations.")

    (OUT_DIR / "00_full_dataset.json").write_text(
        json.dumps([trace_to_dict(t) for t in traces], indent=2, default=str), encoding="utf-8"
    )

    sample, rationale = select_20(traces)
    (OUT_DIR / "01_traces_sample_20.json").write_text(
        json.dumps([trace_to_dict(t) for t in sample], indent=2, default=str), encoding="utf-8"
    )
    (OUT_DIR / "01_selection_rationale.md").write_text(
        "# Selection rationale -- Priority 1 sample\n\n" + "\n".join(f"- {r}" for r in rationale) + "\n",
        encoding="utf-8",
    )

    (OUT_DIR / "02_claim_prioritization.json").write_text(
        json.dumps(build_claim_prioritization(traces), indent=2, default=str), encoding="utf-8"
    )

    build_evidence_yield_csv(traces, OUT_DIR / "03_evidence_yield_per_question.csv")
    build_coverage_matrix_csv(traces, OUT_DIR / "04_dimension_coverage_matrix.csv")
    build_top_questions_csv(traces, OUT_DIR / "05_top_50_questions.csv")
    evidence_rows = build_top_evidence_csv(traces, OUT_DIR / "06_top_50_evidence_records.csv")

    (OUT_DIR / "07_coverage_statistics.md").write_text(
        build_stats_md(traces, evidence_rows), encoding="utf-8"
    )

    print(f"Wrote 9 files to {OUT_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
