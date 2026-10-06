"""
Phase 2B — the composite reporting layer.

`scoring.composite_profile()` is purely additive: it reads the six already-
computed `DimensionScore` entries and groups them into the three clusters
`docs/DIMENSION_VALIDITY_AUDIT.md` found distinguishable. It must not change
anything about how the six are computed, and it must distinguish "never
probed" (UNKNOWN, score=None) from "probed, nothing resulted"
(NOT_DEMONSTRATED, score=0) rather than collapsing both to a bare zero.
"""

from __future__ import annotations

from api.engine import scoring
from api.schemas import CompositeCluster, CoverageState, Dimension, DimensionScore


def _score(dimension: Dimension, score: int, probed: bool, quotes=None) -> DimensionScore:
    return DimensionScore(dimension=dimension, score=score, probed=probed, quotes=quotes or [])


def test_clusters_group_the_correct_member_dimensions():
    profile = scoring.composite_profile([])
    by_cluster = {c.cluster: c for c in profile}
    assert by_cluster[CompositeCluster.EXECUTION_KNOWLEDGE].member_dimensions == [
        Dimension.KNOWLEDGE, Dimension.EXECUTION,
    ]
    assert by_cluster[CompositeCluster.REASONING].member_dimensions == [
        Dimension.PROBLEM_SOLVING, Dimension.JUDGMENT, Dimension.ADAPTABILITY,
    ]
    assert by_cluster[CompositeCluster.OWNERSHIP].member_dimensions == [Dimension.OWNERSHIP]


def test_zero_probed_members_is_unknown_not_a_numeric_zero():
    dims = [
        _score(Dimension.KNOWLEDGE, 0, probed=False),
        _score(Dimension.EXECUTION, 0, probed=False),
    ]
    profile = scoring.composite_profile(dims)
    cluster = next(c for c in profile if c.cluster == CompositeCluster.EXECUTION_KNOWLEDGE)
    assert cluster.coverage_state == CoverageState.UNKNOWN
    assert cluster.score is None, "an unprobed cluster must not render as a numeric 0"


def test_probed_and_zero_is_not_demonstrated_distinct_from_unknown():
    dims = [
        _score(Dimension.KNOWLEDGE, 0, probed=True),
        _score(Dimension.EXECUTION, 0, probed=True),
    ]
    profile = scoring.composite_profile(dims)
    cluster = next(c for c in profile if c.cluster == CompositeCluster.EXECUTION_KNOWLEDGE)
    assert cluster.coverage_state == CoverageState.NOT_DEMONSTRATED
    assert cluster.score == 0, "a real, earned zero is still a number, unlike UNKNOWN"


def test_probed_with_real_content_is_demonstrated():
    dims = [
        _score(Dimension.KNOWLEDGE, 60, probed=True),
        _score(Dimension.EXECUTION, 40, probed=True),
    ]
    profile = scoring.composite_profile(dims)
    cluster = next(c for c in profile if c.cluster == CompositeCluster.EXECUTION_KNOWLEDGE)
    assert cluster.coverage_state == CoverageState.DEMONSTRATED
    assert cluster.score == 50


def test_renormalization_excludes_unprobed_members_from_both_sides():
    # Reasoning has 3 members. Only JUDGMENT is probed, scoring 90 -- an
    # unweighted average over "probed only" must be 90, not (90+0+0)/3=30,
    # which is exactly claim_score()'s total_weight defect this function
    # must not repeat.
    dims = [
        _score(Dimension.PROBLEM_SOLVING, 0, probed=False),
        _score(Dimension.JUDGMENT, 90, probed=True),
        _score(Dimension.ADAPTABILITY, 0, probed=False),
    ]
    profile = scoring.composite_profile(dims)
    cluster = next(c for c in profile if c.cluster == CompositeCluster.REASONING)
    assert cluster.score == 90
    assert cluster.coverage_state == CoverageState.DEMONSTRATED


def test_ownership_cluster_is_a_single_dimension_passthrough():
    dims = [_score(Dimension.OWNERSHIP, 73, probed=True, quotes=["I owned the rollout end to end"])]
    profile = scoring.composite_profile(dims)
    cluster = next(c for c in profile if c.cluster == CompositeCluster.OWNERSHIP)
    assert cluster.score == 73
    assert cluster.quotes == ["I owned the rollout end to end"]


def test_missing_dimension_entries_entirely_are_treated_as_unprobed():
    # candidate_dimension_profile() always returns all six entries in
    # practice, but composite_profile() must not assume that -- a partial
    # input (e.g. a claim-level dimensions dict with gaps) should not crash
    # and should not be silently treated as probed.
    profile = scoring.composite_profile([_score(Dimension.KNOWLEDGE, 80, probed=True)])
    cluster = next(c for c in profile if c.cluster == CompositeCluster.EXECUTION_KNOWLEDGE)
    assert cluster.score == 80  # only KNOWLEDGE counted; EXECUTION absent, not a 0
    assert cluster.coverage_state == CoverageState.DEMONSTRATED


def test_three_clusters_always_returned_in_stable_order():
    profile = scoring.composite_profile([])
    assert [c.cluster for c in profile] == [
        CompositeCluster.EXECUTION_KNOWLEDGE,
        CompositeCluster.REASONING,
        CompositeCluster.OWNERSHIP,
    ]
