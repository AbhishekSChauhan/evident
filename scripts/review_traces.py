#!/usr/bin/env python3
"""
Evident Error Analysis & Trace Review CLI.

Provides engineers and PMs with end-to-end trace inspection for error analysis:
- Candidate Resume -> Extracted Claims
- Questions Generated -> Pure Python Validations & Binary Quality Flags
- Candidate Answers -> Signals Extracted & Verbatim Enforcement Drops
- Final Dimension Scores & Provenance Evaluation Version

Usage:
    python scripts/review_traces.py [--candidate-id C_ID] [--limit 5]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.db import SessionLocal
from api.models import Candidate, Claim, Question, Response, Evaluation
from api.engine.question import validate as validate_question
from api.engine.question_eval import evaluate_question_quality_deterministic


async def review_candidate_trace(db: AsyncSession, candidate_id: str) -> None:
    cand = await db.get(Candidate, candidate_id)
    if not cand:
        print(f"Error: Candidate '{candidate_id}' not found.")
        return

    print("=" * 80)
    print(f"TRACE REVIEW FOR CANDIDATE: {cand.name} (ID: {cand.id}, Tenant: {cand.tenant_id})")
    print(f"Job Family: {getattr(cand, 'job_family', None) or 'Unclassified'}")
    print("=" * 80)

    # 1. Claims
    claims = (
        await db.execute(select(Claim).where(Claim.candidate_id == cand.id))
    ).scalars().all()

    print(f"\n--- EXTRACTED CLAIMS ({len(claims)}) ---")
    for idx, cl in enumerate(claims, 1):
        metric_str = f" [Metric: {cl.metric}]" if cl.metric else ""
        print(f"  [{idx}] ({cl.id}) [{cl.claim_type}]{metric_str}")
        print(f"      \"{cl.text}\"")

    claims_map = {c.id: c.text for c in claims}

    # 2. Questions & Responses
    evaluations = (
        await db.execute(
            select(Evaluation).where(Evaluation.candidate_id == cand.id).order_by(Evaluation.created_at.desc())
        )
    ).scalars().all()

    print(f"\n--- EVALUATION SESSIONS ({len(evaluations)}) ---")
    for ev in evaluations:
        print(f"  Session ID: {ev.session_id} | Status: {ev.status} | Eval Version: {ev.evaluation_version or 'N/A'}")
        
        q_rows = (
            await db.execute(
                select(Question, Response)
                .outerjoin(Response, Response.question_id == Question.id)
                .where(Question.session_id == ev.session_id)
                .order_by(Question.asked_at.asc())
            )
        ).all()

        print(f"  Turns ({len(q_rows)}):")
        for q, r in q_rows:
            move_str = q.move or q.probe_level
            print(f"    - Turn ID: {q.id} | Move: {move_str} | Target Claim: {q.claim_id}")
            print(f"      Question: \"{q.text}\"")

            # Validate question quality
            claim_text = claims_map.get(q.claim_id, "")
            valid, violations = validate_question(
                q.text, claim_text=claim_text, probe_level=q.probe_level, prior_questions=[]
            )
            q_eval = evaluate_question_quality_deterministic(q.text, claim_text)

            print(f"      Question Valid: {valid} | Quality Pass: {q_eval.binary_pass} (Score: {q_eval.question_quality_score}/100)")
            if violations:
                print(f"      Rule Violations: {', '.join(violations)}")
            print(f"      Binary Flags: anchor={q_eval.has_concrete_anchor}, single_ask={q_eval.is_single_ask}, jargon_free={q_eval.is_jargon_free}")

            if r:
                print(f"      Answer ({r.channel}): \"{r.answer_text or '[Voice/Media]'}\"")
                signals_data = json.loads(r.signals_json) if r.signals_json else {}
                sigs = signals_data.get("signals", [])
                quotes = signals_data.get("quotes", [])
                print(f"      Extracted Signals: {len(sigs)} | Verified Quotes: {len(quotes)}")
            else:
                print("      Answer: [Awaiting Response]")

        dim_json = getattr(ev, "dimension_profile_json", None) or getattr(ev, "dimension_scores_json", None)
        if dim_json:
            dims = json.loads(dim_json)
            print("  Final Dimension Scores:")
            if isinstance(dims, dict):
                for d_name, d_val in dims.items():
                    print(f"    - {d_name}: {d_val}")
            elif isinstance(dims, list):
                for item in dims:
                    if isinstance(item, dict):
                        d_name = item.get("dimension") or item.get("name") or "dimension"
                        d_val = item.get("score", item)
                        print(f"    - {d_name}: {d_val}")
                    else:
                        print(f"    - {item}")

    print("\n" + "=" * 80 + "\n")


async def main():
    parser = argparse.ArgumentParser(description="Evident Error Analysis & Trace Review CLI")
    parser.add_argument("--candidate-id", type=str, help="Specific Candidate ID to inspect")
    parser.add_argument("--limit", type=int, default=3, help="Max candidates to review if ID not specified")
    args = parser.parse_args()

    async with SessionLocal() as db:
        if args.candidate_id:
            await review_candidate_trace(db, args.candidate_id)
        else:
            candidates = (
                await db.execute(select(Candidate).limit(args.limit))
            ).scalars().all()
            if not candidates:
                print("No candidates found in database.")
                return
            for cand in candidates:
                await review_candidate_trace(db, cand.id)


if __name__ == "__main__":
    asyncio.run(main())
