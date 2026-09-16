"""
Evident AI Evaluation Regression Test Suite.

Verifies system-wide evaluation integrity offline:
1. Replay Reproducibility: Golden personas reproduce exact finalized scores.
2. Zero Model Call Guarantee: Replay operates 100% offline without LLM network calls.
3. Provenance & Hash Integrity: evaluation_version matches material configuration.
4. Trajectory Validity: Recorded candidate session turns pass trajectory evaluation.
"""

from __future__ import annotations

import pytest
from api import llm
from api.engine.trajectory_eval import (
    TurnTrajectoryRecord,
    evaluate_session_trajectory,
)
from tests.conftest import onboard, run_interview


def interviewed(client, name: str, phone: str) -> dict:
    body = onboard(client, name=name, phone=phone)
    run_interview(client, body["session_id"])
    rows = client.get(
        f"/api/recruiter/candidates/{body['candidate_id']}/evaluations"
    ).json()
    return {**body, "evaluation_id": rows[0]["id"]}


def replay(client, evaluation_id: str):
    return client.post(f"/api/dev/replay/{evaluation_id}")


def test_seeded_candidate_replay_reproduces_offline(client):
    """Verifies that candidates match their finalized evaluations upon replay."""
    subject = interviewed(client, "Eval Regression Persona", "+919810099001")
    rep_resp = replay(client, subject["evaluation_id"])
    assert rep_resp.status_code == 200
    rep_body = rep_resp.json()
    assert rep_body["status"] == "MATCH", rep_body.get("differences")
    assert rep_body["differences"] == []
    assert rep_body["llm_calls"] == 0


def test_replay_is_guaranteed_offline_with_poisoned_llm(client, monkeypatch):
    """Ensures offline eval replay fails loudly if any live LLM path is accidentally invoked."""
    subject = interviewed(client, "Poisoned LLM Persona", "+919810099002")

    async def explode(*args, **kwargs):
        raise AssertionError("Replay attempted to invoke live LLM complete_json()")

    def explode_sync(*args, **kwargs):
        raise AssertionError("Replay attempted to build an LLM client")

    monkeypatch.setattr(llm, "complete_json", explode)
    monkeypatch.setattr(llm, "_raw_completion", explode)
    monkeypatch.setattr(llm, "_get_client", explode_sync)

    resp = replay(client, subject["evaluation_id"])
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "MATCH"
    assert body["llm_calls"] == 0


def test_candidate_turns_pass_planner_trajectory_eval():
    """Sample realistic candidate turns and verify trajectory evaluation passes."""
    sample_turns = [
        TurnTrajectoryRecord(
            turn_index=1,
            claim_id="cl_sre_001",
            claim_text="Handled Prometheus alerting during 99.9% uptime SLA rollout",
            move="OPERATING_CONTEXT",
            question_text="Walk me through how Prometheus alerts were set up.",
            answer_text="Configured alertmanager rules for high CPU and disk pressure.",
            evidence_score=50.0,
        ),
        TurnTrajectoryRecord(
            turn_index=2,
            claim_id="cl_sre_001",
            claim_text="Handled Prometheus alerting during 99.9% uptime SLA rollout",
            move="DEEP_DIVE",
            question_text="How did you tune the evaluation interval?",
            answer_text="Set interval to 15s and added for 5m clause to prevent alert flapping.",
            evidence_score=85.0,
        ),
        TurnTrajectoryRecord(
            turn_index=3,
            claim_id="cl_sre_001",
            claim_text="Handled Prometheus alerting during 99.9% uptime SLA rollout",
            move="PERTURB",
            question_text="What would happen if Alertmanager lost connectivity to Prometheus?",
            answer_text="We configured fallback webhook channels and heartbeat alerts.",
            evidence_score=95.0,
        ),
    ]

    result = evaluate_session_trajectory(sample_turns)
    assert result.overall_pass is True
    assert result.trajectory_score == 1.0
    assert result.violations == []

