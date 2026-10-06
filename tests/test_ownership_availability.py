"""
Phase 2 ownership-availability fix.

OWNERSHIP_BOUNDARY was absent from the BUILD, PROCESS, and METRIC_MOVE
archetype ladders, which is why 79% of real claims could never have it
asked (docs/DIMENSION_OPENING_AUDIT.md, docs/V2_OWNERSHIP_IMPLEMENTATION_PLAN.md).
These tests prove the fix landed exactly as scoped: the move is now
reachable on those three archetypes, in the right ladder position,
with no change to OWNERSHIP, VOLUME, seniority gating, or move
availability.
"""

from __future__ import annotations

from api.engine import anatomy as anatomy_engine
from api.engine.anatomy import Archetype
from api.engine.question import (
    ARCHETYPE_LADDER,
    LEVEL_RESTRICTED,
    Move,
    move_available,
)
from api.engine.orchestrator import ClaimState
from tests.test_policy import FakeClaim, state


def test_ownership_boundary_added_to_build_process_metric_move():
    for archetype in (Archetype.BUILD, Archetype.PROCESS, Archetype.METRIC_MOVE):
        assert Move.OWNERSHIP_BOUNDARY in ARCHETYPE_LADDER[archetype], archetype


def test_ownership_boundary_position_is_immediately_after_perturb():
    for archetype in (Archetype.BUILD, Archetype.PROCESS, Archetype.METRIC_MOVE):
        ladder = ARCHETYPE_LADDER[archetype]
        perturb_ix = ladder.index(Move.PERTURB)
        assert ladder[perturb_ix + 1] is Move.OWNERSHIP_BOUNDARY, archetype
        assert ladder[:perturb_ix + 1] == (
            Move.OPERATING_CONTEXT, Move.FAILURE, Move.PERTURB,
        ), "first three moves must be unchanged"


def test_ownership_boundary_precedes_downstream_moves_per_archetype():
    downstream = {
        Archetype.METRIC_MOVE: (Move.METRIC_DEFINITION, Move.EXCLUSION, Move.COHERENCE, Move.DEPENDENCY),
        Archetype.BUILD: (Move.DEPENDENCY, Move.EXCLUSION, Move.COHERENCE),
        Archetype.PROCESS: (Move.AUTHORITY, Move.EXCLUSION, Move.COHERENCE),
    }
    for archetype, later_moves in downstream.items():
        ladder = ARCHETYPE_LADDER[archetype]
        ob_ix = ladder.index(Move.OWNERSHIP_BOUNDARY)
        for mv in later_moves:
            assert ladder.index(mv) > ob_ix, (archetype, mv)


def test_other_moves_on_the_three_ladders_are_unchanged_in_relative_order():
    # Everything except the one inserted move must keep its original
    # relative order on each previously-excluded archetype's ladder.
    expected_without_insertion = {
        Archetype.METRIC_MOVE: (
            Move.OPERATING_CONTEXT, Move.FAILURE, Move.PERTURB,
            Move.METRIC_DEFINITION, Move.EXCLUSION, Move.COHERENCE, Move.DEPENDENCY,
        ),
        Archetype.BUILD: (
            Move.OPERATING_CONTEXT, Move.FAILURE, Move.PERTURB,
            Move.DEPENDENCY, Move.EXCLUSION, Move.COHERENCE,
        ),
        Archetype.PROCESS: (
            Move.OPERATING_CONTEXT, Move.FAILURE, Move.PERTURB,
            Move.AUTHORITY, Move.EXCLUSION, Move.COHERENCE,
        ),
    }
    for archetype, expected in expected_without_insertion.items():
        ladder = tuple(mv for mv in ARCHETYPE_LADDER[archetype] if mv is not Move.OWNERSHIP_BOUNDARY)
        assert ladder == expected, archetype


def test_legacy_ownership_archetype_ladder_unchanged():
    assert ARCHETYPE_LADDER[Archetype.OWNERSHIP] == (
        Move.OPERATING_CONTEXT, Move.FAILURE, Move.PERTURB,
        Move.OWNERSHIP_BOUNDARY, Move.AUTHORITY, Move.PEOPLE, Move.COHERENCE,
    )


def test_legacy_volume_archetype_ladder_unchanged():
    assert ARCHETYPE_LADDER[Archetype.VOLUME] == (
        Move.OPERATING_CONTEXT, Move.FAILURE, Move.PERTURB,
        Move.AUTHORITY, Move.PEOPLE, Move.COHERENCE,
    )
    assert Move.OWNERSHIP_BOUNDARY not in ARCHETYPE_LADDER[Archetype.VOLUME]


def test_people_move_not_added_to_any_previously_excluded_archetype():
    for archetype in (Archetype.BUILD, Archetype.PROCESS, Archetype.METRIC_MOVE):
        assert Move.PEOPLE not in ARCHETYPE_LADDER[archetype], archetype


def test_no_seniority_gate_introduced_on_ownership_boundary():
    assert Move.OWNERSHIP_BOUNDARY not in LEVEL_RESTRICTED
    assert Move.PEOPLE not in LEVEL_RESTRICTED


def test_move_available_still_unconditional_for_ownership_boundary():
    for text, metric in (
        ("Built a new customer onboarding pipeline", None),
        ("Coordinated handoffs between the support and billing teams", None),
        ("Reduced ticket backlog significantly", "45%"),
    ):
        anatomy = anatomy_engine.analyse(text, metric)
        assert move_available(Move.OWNERSHIP_BOUNDARY, anatomy, ())


def test_forensic_moves_left_includes_ownership_boundary_for_build_claim():
    anatomy = anatomy_engine.analyse("Built a new customer onboarding pipeline", None)
    assert anatomy.archetype is Archetype.BUILD
    s = state("c1", "delivery", 10.0)
    s.claim.text = "Built a new customer onboarding pipeline"
    assert Move.OWNERSHIP_BOUNDARY in s.forensic_moves_left()


def test_forensic_moves_left_includes_ownership_boundary_for_process_claim():
    anatomy = anatomy_engine.analyse(
        "Coordinated handoffs between the support and billing teams", None
    )
    assert anatomy.archetype is Archetype.PROCESS
    s = state("c1", "process_work", 10.0)
    s.claim.text = "Coordinated handoffs between the support and billing teams"
    assert Move.OWNERSHIP_BOUNDARY in s.forensic_moves_left()


def test_forensic_moves_left_includes_ownership_boundary_for_metric_move_claim():
    anatomy = anatomy_engine.analyse("Reduced ticket backlog significantly", "45%")
    assert anatomy.archetype is Archetype.METRIC_MOVE
    s = state("c1", "performance_work", 10.0)
    s.claim.text = "Reduced ticket backlog significantly"
    s.claim.metric = "45%"
    assert Move.OWNERSHIP_BOUNDARY in s.forensic_moves_left()


def test_forensic_moves_left_unchanged_for_ownership_archetype_claim():
    s = state("c1", "team_handling", 10.0)
    s.claim.text = "Owned the vendor relationship end to end"
    anatomy = anatomy_engine.analyse("Owned the vendor relationship end to end", None)
    assert anatomy.archetype is Archetype.OWNERSHIP
    moves = s.forensic_moves_left()
    assert Move.OWNERSHIP_BOUNDARY in moves
    # unchanged: still reachable exactly as before this fix, not newly added
    assert tuple(moves) == tuple(
        mv for mv in ARCHETYPE_LADDER[Archetype.OWNERSHIP]
        if move_available(mv, anatomy, ())
    )
