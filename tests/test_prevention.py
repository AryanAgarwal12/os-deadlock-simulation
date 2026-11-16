"""Unit tests for Deadlock Prevention (src/deadlock_prevention.py)."""

import pytest
from src.deadlock_prevention import (
    HierarchicalOrderingPolicy,
    HoldAndWaitPreventionPolicy,
    COFFMAN_CONDITIONS,
)


def test_hierarchical_ordering_allowed_ascending():
    """Process holds A (rank 1) and requests B (rank 2). Allowed under A < B < C."""
    policy = HierarchicalOrderingPolicy(["A", "B", "C"])
    held = [1, 0, 0]  # holds A
    req = [0, 1, 0]   # requests B

    res = policy.evaluate_request(0, held, req)
    assert res["allowed"] is True
    assert "POLICY COMPLIANT" in res["reason"]
    assert res["violated_condition"] == "Circular Wait"


def test_hierarchical_ordering_rejected_descending():
    """Process holds C (rank 3) and requests A (rank 1). Rejected to break Circular Wait."""
    policy = HierarchicalOrderingPolicy(["A", "B", "C"])
    held = [0, 0, 1]  # holds C (rank 3)
    req = [1, 0, 0]   # requests A (rank 1)

    res = policy.evaluate_request(0, held, req)
    assert res["allowed"] is False
    assert "POLICY VIOLATION" in res["reason"]
    assert res["violated_condition"] == "Circular Wait"


def test_hierarchical_ordering_initial_request():
    """Process holds zero resources. Can request any resource initially."""
    policy = HierarchicalOrderingPolicy(["A", "B", "C"])
    held = [0, 0, 0]
    req = [0, 0, 1]  # requests C

    res = policy.evaluate_request(0, held, req)
    assert res["allowed"] is True


def test_hold_and_wait_prevention_incremental_rejected():
    """Process holding resources cannot make incremental requests."""
    held = [1, 0]
    req = [0, 1]
    res = HoldAndWaitPreventionPolicy.evaluate_request(0, held, req, [1, 1], [1, 1])
    assert res["allowed"] is False
    assert "POLICY VIOLATION" in res["reason"]
    assert res["violated_condition"] == "Hold and Wait"


def test_hold_and_wait_prevention_bulk_allowed():
    """Process holding zero resources requesting all needed at once."""
    held = [0, 0]
    req = [1, 1]
    res = HoldAndWaitPreventionPolicy.evaluate_request(0, held, req, [1, 1], [2, 2])
    assert res["allowed"] is True
    assert "POLICY COMPLIANT" in res["reason"]


def test_coffman_conditions_definitions():
    """Ensure all four Coffman conditions are clearly defined."""
    assert "mutual_exclusion" in COFFMAN_CONDITIONS
    assert "hold_and_wait" in COFFMAN_CONDITIONS
    assert "no_preemption" in COFFMAN_CONDITIONS
    assert "circular_wait" in COFFMAN_CONDITIONS
