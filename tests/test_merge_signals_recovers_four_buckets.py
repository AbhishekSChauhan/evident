"""
Signal aggregation fix — `merge_signals()` previously enumerated exactly
eight of the twelve `AnswerSignals` buckets, silently dropping `decisions`,
`constraints`, `concept_explanations`, and `boundaries` before `score_claim`
ever saw them (docs/SIGNAL_AGGREGATION_AUDIT.md). This is the one function
that changed; these tests prove the four buckets now survive merging,
dedupe correctly, leave every other bucket untouched, and reach real
claim-level scoring end to end.
"""

from __future__ import annotations

from api.engine import signals as signal_rubrics
from api.schemas import (
    AnswerSignals,
    ConceptExplanation,
    ConstraintSignal,
    DecisionSignal,
    Dimension,
    OwnershipBoundary,
    ProbeLevel,
    ProcessStep,
)


def test_1_decisions_survive_merge():
    sig = AnswerSignals(decisions=[DecisionSignal(choice="used Redis", reason="latency was critical", quote="q")])
    merged = signal_rubrics.merge_signals([sig])
    assert len(merged.decisions) == 1
    assert merged.decisions[0].choice == "used Redis"


def test_2_constraints_survive_merge():
    sig = AnswerSignals(constraints=[ConstraintSignal(limitation="budget", effect="capped spend", quote="q")])
    merged = signal_rubrics.merge_signals([sig])
    assert len(merged.constraints) == 1
    assert merged.constraints[0].limitation == "budget"


def test_3_concept_explanations_survive_merge():
    sig = AnswerSignals(concept_explanations=[ConceptExplanation(concept="cache invalidation", reasoning="why it matters", quote="q")])
    merged = signal_rubrics.merge_signals([sig])
    assert len(merged.concept_explanations) == 1
    assert merged.concept_explanations[0].concept == "cache invalidation"


def test_4_boundaries_survive_merge():
    sig = AnswerSignals(boundaries=[OwnershipBoundary(scope_held="backend", scope_handed_off="infra", quote="q")])
    merged = signal_rubrics.merge_signals([sig])
    assert len(merged.boundaries) == 1
    assert merged.boundaries[0].scope_held == "backend"


def test_5_duplicate_signals_dedupe_for_all_four_buckets():
    a = AnswerSignals(
        decisions=[DecisionSignal(choice="used Redis", reason="latency", quote="q1")],
        constraints=[ConstraintSignal(limitation="budget", effect="capped", quote="q2")],
        concept_explanations=[ConceptExplanation(concept="leakage", reasoning="why", quote="q3")],
        boundaries=[OwnershipBoundary(scope_held="backend", scope_handed_off="infra", quote="q4")],
    )
    # Same content, repeated verbatim in a second answer -- one thing said twice.
    b = AnswerSignals(
        decisions=[DecisionSignal(choice="used Redis", reason="latency", quote="q1 again")],
        constraints=[ConstraintSignal(limitation="budget", effect="capped", quote="q2 again")],
        concept_explanations=[ConceptExplanation(concept="leakage", reasoning="why", quote="q3 again")],
        boundaries=[OwnershipBoundary(scope_held="backend", scope_handed_off="infra", quote="q4 again")],
    )
    merged = signal_rubrics.merge_signals([a, b])
    assert len(merged.decisions) == 1
    assert len(merged.constraints) == 1
    assert len(merged.concept_explanations) == 1
    assert len(merged.boundaries) == 1


def test_6_previously_working_buckets_remain_unchanged():
    a = AnswerSignals(process_steps=[ProcessStep(step="checked the dashboard", quote="checked the dashboard")])
    b = AnswerSignals(process_steps=[ProcessStep(step="checked the dashboard", quote="checked the dashboard")])
    merged = signal_rubrics.merge_signals([a, b])
    assert len(merged.process_steps) == 1, "existing dedup behavior must be untouched"


def test_7_score_claim_receives_the_recovered_signals_end_to_end():
    sig = AnswerSignals(decisions=[DecisionSignal(choice="used Redis", reason="latency was critical", quote="I used Redis because latency was critical")])
    scores = signal_rubrics.score_claim([sig], levels_used=[ProbeLevel.DECISION], job_family="general")
    assert scores[Dimension.JUDGMENT].score > 0, "the merge must no longer discard this before score_claim scores it"


def test_8_judgment_gains_decision_and_constraint_evidence():
    only_causal = AnswerSignals()
    with_decision = AnswerSignals(decisions=[DecisionSignal(choice="chose Redis", reason="latency critical", quote="q")])
    with_constraint = AnswerSignals(constraints=[ConstraintSignal(limitation="budget", effect="capped spend", quote="q")])

    base = signal_rubrics.score_claim([only_causal], [ProbeLevel.DECISION], "general")[Dimension.JUDGMENT].score
    with_dec = signal_rubrics.score_claim([with_decision], [ProbeLevel.DECISION], "general")[Dimension.JUDGMENT].score
    with_con = signal_rubrics.score_claim([with_constraint], [ProbeLevel.DECISION], "general")[Dimension.JUDGMENT].score

    assert with_dec > base
    assert with_con > base


def test_9_ownership_gains_boundary_evidence():
    empty = AnswerSignals()
    with_boundary = AnswerSignals(boundaries=[OwnershipBoundary(scope_held="backend", scope_handed_off="infra", quote="q")])

    base = signal_rubrics.score_claim([empty], [ProbeLevel.OUTCOME], "general")[Dimension.OWNERSHIP].score
    after = signal_rubrics.score_claim([with_boundary], [ProbeLevel.OUTCOME], "general")[Dimension.OWNERSHIP].score
    assert after > base
