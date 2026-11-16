"""Unit tests for Banker's Algorithm (src/bankers_algorithm.py)."""

import pytest
from copy import deepcopy
from src.bankers_algorithm import run_safety_algorithm
from src.validation import ValidationError


def test_bankers_standard_safe_state():
    """Verify classic Silberschatz textbook 5-process example."""
    alloc = [
        [0, 1, 0],  # P0
        [2, 0, 0],  # P1
        [3, 0, 2],  # P2
        [2, 1, 1],  # P3
        [0, 0, 2],  # P4
    ]
    max_mat = [
        [7, 5, 3],  # P0
        [3, 2, 2],  # P1
        [9, 0, 2],  # P2
        [2, 2, 2],  # P3
        [4, 3, 3],  # P4
    ]
    avail = [3, 3, 2]

    res = run_safety_algorithm(alloc, max_mat, avail)

    assert res["is_safe"] is True
    assert len(res["safe_sequence"]) == 5
    assert res["unfinished_processes"] == []
    # Total available after all processes release resources equals total system resources: [10, 5, 7]
    assert res["work_final"] == [10, 5, 7]
    # Check trace length equals number of processes
    assert len(res["trace"]) == 5


def test_bankers_unsafe_state():
    """Verify detection of an unsafe state where no complete sequence exists."""
    alloc = [
        [2, 0],
        [1, 2],
    ]
    max_mat = [
        [4, 2],  # Need [2, 2]
        [3, 3],  # Need [2, 1]
    ]
    avail = [1, 0]  # Neither P0 need [2, 2] nor P1 need [2, 1] <= [1, 0]

    res = run_safety_algorithm(alloc, max_mat, avail)

    assert res["is_safe"] is False
    assert res["safe_sequence"] == []
    assert set(res["unfinished_processes"]) == {0, 1}
    assert "UNSAFE STATE" in res["explanation"]


def test_bankers_work_vector_step_updates():
    """Verify Work vector correctly increases at each completed step."""
    alloc = [[1, 0], [0, 1]]
    max_mat = [[1, 0], [0, 1]]
    avail = [0, 0]

    res = run_safety_algorithm(alloc, max_mat, avail)
    assert res["is_safe"] is True
    assert len(res["trace"]) == 2
    # Step 1: Work becomes [0, 0] + [1, 0] = [1, 0]
    assert res["trace"][0]["work_after"] == [1, 0]
    # Step 2: Work becomes [1, 0] + [0, 1] = [1, 1]
    assert res["trace"][1]["work_after"] == [1, 1]


def test_bankers_zero_need_process():
    """A process whose Allocation equals Maximum has Need=0 and can finish immediately."""
    alloc = [[3, 2], [1, 1]]
    max_mat = [[3, 2], [5, 5]]  # P0 has Need [0, 0]
    avail = [0, 0]  # Avail is 0, but P0 needs 0

    res = run_safety_algorithm(alloc, max_mat, avail)
    # P0 finishes first and releases [3, 2], allowing P1 (Need [4, 4] > [3, 2]) to... wait:
    # After P0 releases [3, 2], Work becomes [3, 2].
    # P1 needs [4, 4] > [3, 2], so P1 cannot finish.
    # Result: P0 finishes, P1 unfinished -> Unsafe state overall
    assert res["is_safe"] is False
    assert res["safe_sequence"] == [0]
    assert res["unfinished_processes"] == [1]


def test_bankers_input_immutability():
    """Ensure run_safety_algorithm does not mutate input lists."""
    alloc = [[1, 0], [0, 1]]
    max_mat = [[2, 1], [1, 2]]
    avail = [1, 1]

    alloc_copy = deepcopy(alloc)
    max_copy = deepcopy(max_mat)
    avail_copy = list(avail)

    run_safety_algorithm(alloc, max_mat, avail)

    assert alloc == alloc_copy
    assert max_mat == max_copy
    assert avail == avail_copy
