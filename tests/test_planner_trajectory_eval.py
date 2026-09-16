"""
Tests for api/engine/trajectory_eval.py (Planner Trajectory Evaluation Engine).
"""

from api.engine.trajectory_eval import (
    TurnTrajectoryRecord,
    evaluate_session_trajectory,
)


def test_valid_trajectory_passes_all_checks():
    turns = [
        TurnTrajectoryRecord(
            turn_index=1,
            claim_id="cl_001",
            claim_text="Optimized PostgreSQL queries reducing latency by 40%",
            move="OPERATING_CONTEXT",
            question_text="Walk me through the query optimization setup.",
            answer_text="I analyzed slow queries using EXPLAIN ANALYZE and created index on user_id.",
            evidence_score=45.0,
            is_repair=False,
            is_memory_exhausted=False,
        ),
        TurnTrajectoryRecord(
            turn_index=2,
            claim_id="cl_001",
            claim_text="Optimized PostgreSQL queries reducing latency by 40%",
            move="DEEP_DIVE",
            question_text="What execution plan trade-offs did you evaluate?",
            answer_text="I evaluated partial indexes vs composite indexes on high-cardinality columns.",
            evidence_score=85.0,
            is_repair=False,
            is_memory_exhausted=False,
        ),
        TurnTrajectoryRecord(
            turn_index=3,
            claim_id="cl_001",
            claim_text="Optimized PostgreSQL queries reducing latency by 40%",
            move="PERTURB",
            question_text="What would happen if table size doubled overnight?",
            answer_text="Memory buffer cache would spill to disk so we would need vacuum tuning.",
            evidence_score=95.0,
            is_repair=False,
            is_memory_exhausted=False,
        ),
    ]

    result = evaluate_session_trajectory(turns)
    assert result.overall_pass is True
    assert result.trajectory_score == 1.0
    assert result.ladder_progression_valid is True
    assert result.saturation_reachability_valid is True
    assert result.memory_exhaustion_steering_valid is True
    assert len(result.violations) == 0


def test_opening_move_not_operating_context_flags_violation():
    turns = [
        {
            "turn_index": 1,
            "claim_id": "cl_001",
            "claim_text": "Built Kubernetes deployment pipeline",
            "move": "PERTURB",  # Invalid opening move
            "question_text": "What if k8s cluster crashed?",
            "answer_text": "We would restore from backup.",
        }
    ]

    result = evaluate_session_trajectory(turns)
    assert result.ladder_progression_valid is False
    assert result.overall_pass is False
    assert any("OPERATING_CONTEXT" in v for v in result.violations)


def test_memory_exhaustion_repair_turn_flags_violation():
    turns = [
        {
            "turn_index": 1,
            "claim_id": "cl_001",
            "claim_text": "Configured Prometheus alerts",
            "move": "OPERATING_CONTEXT",
            "question_text": "Walk me through alert rules.",
            "answer_text": "I don't know, nothing else comes to mind.",
            "is_repair": True,
            "is_memory_exhausted": True,
        }
    ]

    result = evaluate_session_trajectory(turns)
    assert result.memory_exhaustion_steering_valid is False
    assert result.overall_pass is False
    assert any("Memory exhaustion" in v for v in result.violations)


def test_high_score_without_perturb_flags_saturation_violation():
    turns = [
        {
            "turn_index": 1,
            "claim_id": "cl_001",
            "claim_text": "Handled production outage",
            "move": "OPERATING_CONTEXT",
            "question_text": "Tell me about the outage.",
            "answer_text": "Database deadlocked so I restarted connections.",
            "evidence_score": 85.0,
        },
        {
            "turn_index": 2,
            "claim_id": "cl_001",
            "claim_text": "Handled production outage",
            "move": "DEEP_DIVE",
            "question_text": "What root cause was found?",
            "answer_text": "Unindexed foreign key.",
            "evidence_score": 90.0,
        },
    ]

    result = evaluate_session_trajectory(turns)
    assert result.saturation_reachability_valid is False
    assert result.overall_pass is False
    assert any("never reached PERTURB" in v for v in result.violations)

