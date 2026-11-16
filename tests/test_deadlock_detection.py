"""Unit tests for Deadlock Detection (src/deadlock_detection.py)."""

import pytest
from src.deadlock_detection import detect_deadlock_multi_instance, analyze_resource_allocation_graph


def test_detection_multi_instance_deadlocked():
    """Verify deadlocked state detection with multiple instances."""
    alloc = [
        [1, 0],  # P0 holds A
        [0, 1],  # P1 holds B
        [1, 1],  # P2 holds A, B
    ]
    req = [
        [0, 1],  # P0 wants B
        [1, 0],  # P1 wants A
        [1, 0],  # P2 wants A
    ]
    avail = [0, 0]

    res = detect_deadlock_multi_instance(alloc, req, avail)

    assert res["is_deadlocked"] is True
    assert set(res["deadlocked_processes"]) == {0, 1, 2}
    assert res["resolution_order"] == []


def test_detection_multi_instance_no_deadlock():
    """Verify system where all requests can be resolved in sequence."""
    alloc = [
        [0, 1, 0],  # P0
        [2, 0, 0],  # P1
        [3, 0, 3],  # P2
    ]
    req = [
        [0, 0, 0],  # P0 needs 0
        [1, 0, 1],  # P1
        [0, 0, 1],  # P2
    ]
    avail = [0, 0, 1]

    res = detect_deadlock_multi_instance(alloc, req, avail)

    assert res["is_deadlocked"] is False
    assert res["deadlocked_processes"] == []
    assert len(res["resolution_order"]) == 3


def test_detection_zero_allocation_process():
    """A process with zero allocation holds no resources and cannot participate in deadlock."""
    alloc = [
        [0, 0],  # P0 holds nothing
        [1, 1],  # P1 holds A, B
    ]
    req = [
        [1, 0],  # P0 wants A
        [0, 1],  # P1 wants B
    ]
    avail = [0, 0]

    res = detect_deadlock_multi_instance(alloc, req, avail)

    # P0 is initially marked finish=True because alloc=[0, 0].
    # P1 is deadlocked because req [0, 1] > avail [0, 0].
    assert res["initial_finish"][0] is True
    assert res["initial_finish"][1] is False
    assert res["is_deadlocked"] is True
    assert res["deadlocked_processes"] == [1]


def test_rag_cycle_analysis_single_instance():
    """In single-instance resources, a cycle implies deadlock."""
    alloc = [[1, 0], [0, 1]]  # P0 has R0, P1 has R1
    req = [[0, 1], [1, 0]]    # P0 wants R1, P1 wants R0
    totals = [1, 1]           # Single instance

    rag = analyze_resource_allocation_graph(alloc, req, totals)

    assert rag["has_cycle"] is True
    assert rag["is_single_instance"] is True
    assert "NECESSARY AND SUFFICIENT FOR DEADLOCK" in rag["conclusion"]


def test_rag_cycle_analysis_multi_instance():
    """In multi-instance resources, a cycle is not sufficient for deadlock."""
    alloc = [[2, 0], [0, 2]]
    req = [[0, 1], [1, 0]]
    totals = [3, 3]

    rag = analyze_resource_allocation_graph(alloc, req, totals)

    assert rag["has_cycle"] is True
    assert rag["is_single_instance"] is False
    assert "NOT A SUFFICIENT condition" in rag["conclusion"]
