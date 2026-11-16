"""Unit tests for Deadlock Recovery (src/deadlock_recovery.py)."""

import pytest
from src.deadlock_recovery import suggest_victim_processes, recover_by_process_termination


def test_suggest_victim_processes():
    alloc = [
        [1, 0],  # P0 holds 1
        [3, 2],  # P1 holds 5
        [0, 1],  # P2 holds 1
    ]
    deadlocked = [0, 1, 2]
    suggestions = suggest_victim_processes(alloc, deadlocked)

    # Highest held should be first (P1 with 5)
    assert suggestions[0]["process_id"] == 1
    assert suggestions[0]["total_resources_held"] == 5


def test_recover_by_process_termination_successful():
    """System in deadlock resolved by terminating victim."""
    alloc = [
        [1, 0],  # P0 holds A
        [0, 1],  # P1 holds B
    ]
    req = [
        [0, 1],  # P0 wants B
        [1, 0],  # P1 wants A
    ]
    avail = [0, 0]

    # Terminate P0: releases [1, 0] to Available
    res = recover_by_process_termination(0, alloc, req, avail)

    assert res["victim_id"] == 0
    assert res["resources_reclaimed"] == [1, 0]
    assert res["state_after"]["available"] == [1, 0]
    assert res["state_after"]["allocation"][0] == [0, 0]
    # P1 now gets [1, 0], completes!
    assert res["is_fully_resolved"] is True
    assert res["remaining_deadlocked"] == []


def test_recover_by_process_termination_partial():
    """Terminating one victim increases resources, but not enough for all remaining."""
    alloc = [
        [1, 0],  # P0
        [0, 1],  # P1
        [0, 0],  # P2
    ]
    req = [
        [0, 2],  # P0 wants 2 of B
        [5, 0],  # P1 wants 5 of A
        [0, 0],
    ]
    avail = [0, 0]

    # Terminate P0: Available becomes [1, 0].
    # P1 still needs [5, 0] > [1, 0], so P1 remains in deadlock!
    res = recover_by_process_termination(0, alloc, req, avail)

    assert res["is_fully_resolved"] is False
    assert 1 in res["remaining_deadlocked"]
    assert "PARTIAL RECOVERY" in res["explanation"]


def test_recover_invalid_victim_id():
    alloc = [[1, 0]]
    req = [[0, 1]]
    avail = [0, 0]
    with pytest.raises(ValueError):
        recover_by_process_termination(99, alloc, req, avail)
