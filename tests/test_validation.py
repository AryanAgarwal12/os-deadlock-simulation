"""Unit tests for src/validation.py."""

import pytest
from src.validation import (
    is_non_negative_integer,
    validate_dimensions,
    validate_system_state,
    calculate_need_matrix,
    validate_resource_request,
    ValidationError,
)


def test_is_non_negative_integer():
    assert is_non_negative_integer(0) is True
    assert is_non_negative_integer(5) is True
    assert is_non_negative_integer("5") is True
    assert is_non_negative_integer(5.0) is True
    assert is_non_negative_integer(-1) is False
    assert is_non_negative_integer("-3") is False
    assert is_non_negative_integer(3.5) is False
    assert is_non_negative_integer("abc") is False
    assert is_non_negative_integer(True) is False
    assert is_non_negative_integer(False) is False
    assert is_non_negative_integer(None) is False


def test_validate_dimensions_valid():
    alloc = [[0, 1], [1, 0]]
    max_mat = [[1, 1], [1, 1]]
    avail = [1, 2]
    ok, err = validate_dimensions(alloc, max_mat, avail, 2, 2)
    assert ok is True
    assert err == ""


def test_validate_dimensions_mismatch():
    alloc = [[0, 1], [1, 0]]
    max_mat = [[1, 1]]  # Row mismatch
    avail = [1, 2]
    ok, err = validate_dimensions(alloc, max_mat, avail)
    assert ok is False
    assert "row count" in err.lower()

    # Column mismatch
    alloc2 = [[0, 1, 2], [1, 0]]
    max2 = [[1, 1, 1], [1, 1, 1]]
    avail2 = [1, 2, 3]
    ok2, err2 = validate_dimensions(alloc2, max2, avail2)
    assert ok2 is False
    assert "columns" in err2.lower()


def test_validate_system_state_allocation_exceeds_maximum():
    alloc = [[2, 1], [0, 0]]
    max_mat = [[1, 1], [1, 1]]  # Alloc[0][0]=2 > Max[0][0]=1
    avail = [1, 1]
    ok, err, details = validate_system_state(alloc, max_mat, avail)
    assert ok is False
    assert "exceeds declared Maximum" in err
    assert details["error_type"] == "allocation_exceeds_maximum"


def test_validate_system_state_total_mismatch():
    alloc = [[1, 0], [2, 1]]
    max_mat = [[2, 1], [3, 2]]
    avail = [1, 1]
    # Sum alloc = [3, 1], Avail = [1, 1] -> Calc Total = [4, 2]
    declared_total = [5, 2]  # Wrong for A
    ok, err, details = validate_system_state(alloc, max_mat, avail, declared_total)
    assert ok is False
    assert "Total resource mismatch" in err
    assert details["calculated"] == 4


def test_calculate_need_matrix_correctness():
    alloc = [[0, 1, 0], [2, 0, 0]]
    max_mat = [[7, 5, 3], [3, 2, 2]]
    need = calculate_need_matrix(alloc, max_mat)
    assert need == [[7, 4, 3], [1, 2, 2]]


def test_calculate_need_matrix_raises_on_violation():
    alloc = [[5, 0]]
    max_mat = [[2, 0]]
    with pytest.raises(ValidationError):
        calculate_need_matrix(alloc, max_mat)


def test_validate_resource_request_order():
    alloc = [[0, 1], [1, 0]]
    max_mat = [[2, 2], [2, 2]]
    avail = [1, 1]

    # 1. Invalid process id
    status, _, _ = validate_resource_request(5, [1, 0], alloc, max_mat, avail)
    assert status == "INVALID_PROCESS_ID"

    # 2. Negative quantity
    status, _, _ = validate_resource_request(0, [-1, 0], alloc, max_mat, avail)
    assert status == "INVALID_NEGATIVE_OR_TYPE"

    # 3. Exceeds need: P0 need is [2, 1]
    status, _, _ = validate_resource_request(0, [3, 0], alloc, max_mat, avail)
    assert status == "INVALID_EXCEEDS_NEED"

    # 4. Exceeds available: P0 need is [2, 1], Avail is [1, 1], request [2, 0]
    status, _, _ = validate_resource_request(0, [2, 0], alloc, max_mat, avail)
    assert status == "WAITING_INSUFFICIENT_AVAILABLE"

    # 5. OK
    status, _, _ = validate_resource_request(0, [1, 1], alloc, max_mat, avail)
    assert status == "PROCEED_TO_SAFETY_CHECK"
