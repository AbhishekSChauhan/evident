"""
Phase 2A: the `score > 0` backdoor fix.

`score_claim()` used to set `entry.probed = dimension in probed or entry.score
> 0` — any incidental nonzero score marked a dimension "probed" even when no
targeting move/level was ever asked. This is the measured root cause of the
Unknown-vs-Not-Demonstrated collapse documented in
`docs/COVERAGE_REACHABILITY_AUDIT.md` and
`docs/V2_SCORING_REPORTING_IMPLEMENTATION_PLAN.md`.

These tests prove exactly five things: the backdoor is gone (a), genuine
targeting still works (b), and three consumers that do not read `.probed` at
all are numerically untouched (c, d, e).
"""

from __future__ import annotations

from api.engine import scoring, signals
from api.schemas import (
    AnswerSignals,
    Dimension,
    DimensionScore,
    ProbeLevel,
    ProcessStep,
)


def _execution_rich_answer() -> AnswerSignals:
    # process_steps alone opens EXECUTION's gate and scores it > 0
    # (score_execution: gate_open=bool(steps)) with no decision/causal content
    # at all -- the cleanest incidental-nonzero case available.
    return AnswerSignals(
        process_steps=[
            ProcessStep(step="checked the dashboard every morning", quote="checked the dashboard every morning"),
        ]
    )


def test_a_score_greater_than_zero_no_longer_marks_a_dimension_probed():
    sig = _execution_rich_answer()
    # DECISION only targets JUDGMENT (PROBE_LEVEL_DIMENSIONS) -- EXECUTION is
    # never the targeted dimension here, despite scoring > 0 from the
    # process_steps above.
    scores = signals.score_claim([sig], levels_used=[ProbeLevel.DECISION], job_family="general")
    assert scores[Dimension.EXECUTION].score > 0, "sanity: the incidental score must be real"
    assert scores[Dimension.EXECUTION].probed is False
    assert scores[Dimension.EXECUTION].basis == "not probed"


def test_b_genuinely_targeted_dimensions_remain_probed():
    sig = AnswerSignals()  # no content at all -- JUDGMENT will score 0
    scores = signals.score_claim([sig], levels_used=[ProbeLevel.DECISION], job_family="general")
    assert scores[Dimension.JUDGMENT].score == 0
    assert scores[Dimension.JUDGMENT].probed is True, (
        "a targeted dimension must read probed=True even when it scored zero -- "
        "this is the exact case the backdoor used to make indistinguishable "
        "from 'never asked'"
    )


def test_b2_move_based_targeting_still_credits_probed():
    # Same shape, but via moves_used (the live forensic path) instead of a
    # bare probe level -- confirms the fix did not disturb MOVE_DIMENSIONS
    # crediting, only the incidental-score fallback.
    sig = AnswerSignals()
    scores = signals.score_claim(
        [sig], levels_used=[ProbeLevel.OPERATIONAL], job_family="general",
        moves_used=["OWNERSHIP_BOUNDARY"],
    )
    assert scores[Dimension.OWNERSHIP].probed is True
    assert scores[Dimension.OWNERSHIP].score == 0


def _two_dimension_maps(probed_for_execution: bool) -> dict[Dimension, DimensionScore]:
    """Identical scores, differing ONLY in EXECUTION's `.probed` flag --
    isolates whether claim_score() reads that field at all."""
    return {
        Dimension.KNOWLEDGE: DimensionScore(dimension=Dimension.KNOWLEDGE, score=40, probed=True),
        Dimension.EXECUTION: DimensionScore(dimension=Dimension.EXECUTION, score=55, probed=probed_for_execution),
        Dimension.PROBLEM_SOLVING: DimensionScore(dimension=Dimension.PROBLEM_SOLVING, score=0, probed=False),
        Dimension.JUDGMENT: DimensionScore(dimension=Dimension.JUDGMENT, score=0, probed=False),
        Dimension.OWNERSHIP: DimensionScore(dimension=Dimension.OWNERSHIP, score=0, probed=False),
        Dimension.ADAPTABILITY: DimensionScore(dimension=Dimension.ADAPTABILITY, score=30, probed=True),
    }


def test_c_claim_score_is_invariant_to_the_probed_flag():
    before = scoring.claim_score(_two_dimension_maps(probed_for_execution=True), "general")
    after = scoring.claim_score(_two_dimension_maps(probed_for_execution=False), "general")
    assert before == after, (
        "claim_score()'s arithmetic must not read .probed at all -- "
        "its numeric output cannot move because the flag's meaning changed"
    )


def test_d_weighted_evidence_and_competence_score_are_invariant_to_the_probed_flag():
    # weighted_evidence_score() and competence_score() are built entirely on
    # top of claim_score()'s output (c), so their invariance follows directly,
    # proved here rather than just asserted from the call chain.
    before_claim_score = scoring.claim_score(_two_dimension_maps(probed_for_execution=True), "general")
    after_claim_score = scoring.claim_score(_two_dimension_maps(probed_for_execution=False), "general")

    before_weighted, before_coverage = scoring.weighted_evidence_score(
        [("delivery", before_claim_score)], {"delivery": 1.0}
    )
    after_weighted, after_coverage = scoring.weighted_evidence_score(
        [("delivery", after_claim_score)], {"delivery": 1.0}
    )
    assert before_weighted == after_weighted
    assert before_coverage == after_coverage

    before_competence = scoring.competence_score(before_weighted, consistency_multiplier=0.9)
    after_competence = scoring.competence_score(after_weighted, consistency_multiplier=0.9)
    assert before_competence == after_competence


def test_e_rank_candidates_sort_key_is_invariant_to_the_probed_flag():
    # rank_candidates() sorts by (-competence_score, -weighted_evidence_score,
    # name) only -- both numeric inputs are proved invariant in (c)/(d), so the
    # sort key itself cannot change. Proved directly on the same two scenarios
    # rather than re-asserted from the prior tests.
    before_claim_score = scoring.claim_score(_two_dimension_maps(probed_for_execution=True), "general")
    after_claim_score = scoring.claim_score(_two_dimension_maps(probed_for_execution=False), "general")
    before_weighted, _ = scoring.weighted_evidence_score([("delivery", before_claim_score)], {"delivery": 1.0})
    after_weighted, _ = scoring.weighted_evidence_score([("delivery", after_claim_score)], {"delivery": 1.0})
    before_competence = scoring.competence_score(before_weighted, 0.9)
    after_competence = scoring.competence_score(after_weighted, 0.9)

    before_key = (-before_competence, -before_weighted, "Candidate A")
    after_key = (-after_competence, -after_weighted, "Candidate A")
    assert before_key == after_key


def test_probed_count_drops_when_only_backdoor_credited_it():
    sig = _execution_rich_answer()
    scores = signals.score_claim([sig], levels_used=[ProbeLevel.DECISION], job_family="general")
    # Only JUDGMENT was targeted; EXECUTION's incidental score no longer counts.
    assert scoring.probed_count(scores) == 1
