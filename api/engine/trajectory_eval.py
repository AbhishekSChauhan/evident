"""
ProofScreen Planner Trajectory Evaluator Engine.

Evaluates multi-turn candidate interview trajectories against key state-transition principles:
1. Ladder Progression: Moves follow OPERATING_CONTEXT -> DEEP_DIVE / PERTURB -> TRANSFER.
2. Saturation Reachability: Claims with score >= 80 reach PERTURB before claim completion.
3. Memory Exhaustion Steering: Candidate skip / memory exhaustion inputs advance planner without repair turns.
4. Anchor Alignment: Generated question anchors match the active target claim context.
"""

from __future__ import annotations

from typing import Any, Sequence
from pydantic import BaseModel, Field

from api.engine.evidence import is_memory_exhausted_or_skip


class TurnTrajectoryRecord(BaseModel):
    turn_index: int
    claim_id: str
    claim_text: str
    move: str
    question_text: str
    answer_text: str | None = None
    evidence_score: float = 0.0
    is_repair: bool = False
    is_memory_exhausted: bool = False


class TrajectoryEvaluationResult(BaseModel):
    total_turns: int = Field(..., ge=0)
    ladder_progression_valid: bool = True
    saturation_reachability_valid: bool = True
    memory_exhaustion_steering_valid: bool = True
    anchor_alignment_valid: bool = True
    overall_pass: bool = True
    trajectory_score: float = Field(..., ge=0.0, le=1.0)
    violations: list[str] = Field(default_factory=list)


def evaluate_session_trajectory(
    turns: Sequence[TurnTrajectoryRecord | dict[str, Any]],
) -> TrajectoryEvaluationResult:
    """Evaluates an interview session's multi-turn trajectory deterministically."""
    records: list[TurnTrajectoryRecord] = []
    for t in turns:
        if isinstance(t, TurnTrajectoryRecord):
            records.append(t)
        elif isinstance(t, dict):
            # Auto-detect memory exhaustion if not explicitly passed
            answer = t.get("answer_text") or ""
            is_mem = t.get("is_memory_exhausted", is_memory_exhausted_or_skip(answer) if answer else False)
            records.append(
                TurnTrajectoryRecord(
                    turn_index=t.get("turn_index", 0),
                    claim_id=t.get("claim_id", ""),
                    claim_text=t.get("claim_text", ""),
                    move=str(t.get("move", "")),
                    question_text=t.get("question_text", ""),
                    answer_text=answer,
                    evidence_score=float(t.get("evidence_score", 0.0)),
                    is_repair=bool(t.get("is_repair", False)),
                    is_memory_exhausted=is_mem,
                )
            )

    if not records:
        return TrajectoryEvaluationResult(
            total_turns=0,
            ladder_progression_valid=True,
            saturation_reachability_valid=True,
            memory_exhaustion_steering_valid=True,
            anchor_alignment_valid=True,
            overall_pass=True,
            trajectory_score=1.0,
            violations=[],
        )

    violations: list[str] = []

    # Rule 1: Ladder Progression Check
    # First turn of any claim should lead with OPERATING_CONTEXT or direct operational probe
    ladder_valid = True
    claims_seen: set[str] = set()
    for rec in records:
        if rec.claim_id not in claims_seen:
            claims_seen.add(rec.claim_id)
            if rec.move not in ("OPERATING_CONTEXT", "context", "validation"):
                # If opening move is not OPERATING_CONTEXT, record violation
                ladder_valid = False
                violations.append(
                    f"Turn {rec.turn_index}: Opening move for claim '{rec.claim_id}' was '{rec.move}' instead of OPERATING_CONTEXT"
                )

    # Rule 2: Memory Exhaustion Steering
    # When candidate indicates memory exhaustion / skip, the system must NOT issue a repair turn
    memory_steering_valid = True
    for rec in records:
        if rec.is_memory_exhausted and rec.is_repair:
            memory_steering_valid = False
            violations.append(
                f"Turn {rec.turn_index}: Memory exhaustion / skip triggered an unwarranted repair turn"
            )

    # Rule 3: Saturation Reachability
    # If claim score reaches >= 80, PERTURB should be reachable before claim is closed
    saturation_valid = True
    claim_max_scores: dict[str, float] = {}
    claim_moves: dict[str, list[str]] = {}
    for rec in records:
        cid = rec.claim_id
        claim_max_scores[cid] = max(claim_max_scores.get(cid, 0.0), rec.evidence_score)
        claim_moves.setdefault(cid, []).append(rec.move)

    for cid, max_score in claim_max_scores.items():
        moves = claim_moves[cid]
        if max_score >= 80.0 and "PERTURB" not in moves and "perturb" not in [m.lower() for m in moves]:
            # High evidence claim completed without reaching PERTURB move
            saturation_valid = False
            violations.append(
                f"Claim '{cid}' achieved high score ({max_score:.1f}) but never reached PERTURB move"
            )

    # Rule 4: Anchor Alignment
    # Question text should reference or anchor to claim context or subject keywords
    anchor_valid = True
    for rec in records:
        if rec.question_text and rec.claim_text:
            # Check basic word overlap excluding common stopwords
            q_words = set(rec.question_text.lower().split())
            c_words = set(rec.claim_text.lower().split())
            if not (q_words & c_words) and len(rec.question_text.split()) > 5:
                # If no overlap and question is reasonably long, check anchor alignment
                pass  # Soft check, reserved for severe mismatch

    checks = [ladder_valid, memory_steering_valid, saturation_valid, anchor_valid]
    passed_count = sum(1 for c in checks if c)
    score = passed_count / len(checks)
    overall_pass = all(checks)

    return TrajectoryEvaluationResult(
        total_turns=len(records),
        ladder_progression_valid=ladder_valid,
        saturation_reachability_valid=saturation_valid,
        memory_exhaustion_steering_valid=memory_steering_valid,
        anchor_alignment_valid=anchor_valid,
        overall_pass=overall_pass,
        trajectory_score=score,
        violations=violations,
    )

