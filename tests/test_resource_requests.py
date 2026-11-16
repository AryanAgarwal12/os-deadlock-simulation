"""Unit tests for Resource Requests (src/resource_requests.py)."""

import pytest
from copy import deepcopy
from src.resource_requests import request_resources, RequestDecision


@pytest.fixture
def base_system():
    alloc = [
        [0, 1, 0],  # P0
        [2, 0, 0],  # P1
        [3, 0, 2],  # P2
        [2, 1, 1],  # P3
        [0, 0, 2],  # P4
    ]
    max_mat = [
        [7, 5, 3],  # P0 (Need [7, 4, 3])
        [3, 2, 2],  # P1 (Need [1, 2, 2])
        [9, 0, 2],  # P2 (Need [6, 0, 0])
        [2, 2, 2],  # P3 (Need [0, 1, 1])
        [4, 3, 3],  # P4 (Need [4, 3, 1])
    ]
    avail = [3, 3, 2]
    return alloc, max_mat, avail


def test_request_granted_safe(base_system):
    """P1 requests [1, 0, 2] <= Need [1, 2, 2] and <= Available [3, 3, 2].

    This is granted and the tentative state remains safe.
    """
    alloc, max_mat, avail = base_system
    res = request_resources(1, [1, 0, 2], alloc, max_mat, avail)

    assert res["decision"] == RequestDecision.GRANTED_SAFE
    assert res["is_granted"] is True
    assert res["is_waiting"] is False
    assert res["is_denied"] is False
    assert res["safety_result"]["is_safe"] is True

    # Check updated final state
    assert res["final_state"]["allocation"][1] == [3, 0, 2]
    assert res["final_state"]["available"] == [2, 3, 0]


def test_request_waiting_deferred(base_system):
    """P4 requests [4, 2, 0] <= Need [4, 3, 1], but > Available [3, 3, 2].

    Should be WAITING_DEFERRED and state must be completely untouched.
    """
    alloc, max_mat, avail = base_system
    orig_alloc = deepcopy(alloc)
    orig_avail = list(avail)

    res = request_resources(4, [4, 2, 0], alloc, max_mat, avail)

    assert res["decision"] == RequestDecision.WAITING_DEFERRED
    assert res["is_waiting"] is True
    assert res["is_granted"] is False
    assert res["final_state"]["allocation"] == orig_alloc
    assert res["final_state"]["available"] == orig_avail


def test_request_exceeds_need(base_system):
    """P0 requests [8, 0, 0] > remaining Need [7, 4, 3].

    Maximum claim violation -> INVALID_EXCEEDS_NEED.
    """
    alloc, max_mat, avail = base_system
    res = request_resources(0, [8, 0, 0], alloc, max_mat, avail)

    assert res["decision"] == RequestDecision.INVALID_EXCEEDS_NEED
    assert res["is_invalid"] is True
    assert res["is_granted"] is False


def test_request_denied_unsafe():
    """Request satisfies Need and Available, but tentative state has no safe sequence."""
    alloc = [[1, 1], [1, 0]]
    max_mat = [[2, 2], [3, 1]]
    avail = [1, 1]

    # P1 requests [1, 0] <= Need [2, 1] and <= Avail [1, 1]
    # Tentative Avail is [0, 1]. Neither P0 (need [1, 1]) nor P1 (need [1, 1]) can finish.
    res = request_resources(1, [1, 0], alloc, max_mat, avail)

    assert res["decision"] == RequestDecision.DENIED_UNSAFE
    assert res["is_denied"] is True
    assert res["is_granted"] is False
    # Original state preserved
    assert res["final_state"]["allocation"] == alloc
    assert res["final_state"]["available"] == avail


def test_request_invalid_inputs(base_system):
    """Test out-of-range process ID and negative request."""
    alloc, max_mat, avail = base_system

    # Negative process id
    res1 = request_resources(-1, [1, 0, 0], alloc, max_mat, avail)
    assert res1["decision"] == RequestDecision.INVALID_INPUT

    # Out of range process id
    res2 = request_resources(10, [1, 0, 0], alloc, max_mat, avail)
    assert res2["decision"] == RequestDecision.INVALID_INPUT

    # Negative request
    res3 = request_resources(0, [-1, 0, 0], alloc, max_mat, avail)
    assert res3["decision"] == RequestDecision.INVALID_INPUT
