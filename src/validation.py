"""Input validation module for OS Deadlock Analysis Dashboard.

Provides robust validation for process/resource configurations, matrices (Allocation,
Maximum, Need), vectors (Available, Total), and dynamic resource requests.
"""

from typing import List, Tuple, Dict, Any, Optional


class ValidationError(ValueError):
    """Custom exception raised when system input data is invalid."""
    pass


def is_non_negative_integer(val: Any) -> bool:
    """Check if value is a non-negative integer (including integer types)."""
    if isinstance(val, bool):
        return False
    if isinstance(val, int) and val >= 0:
        return True
    try:
        # Check if float is an exact integer
        if isinstance(val, float) and val.is_integer() and val >= 0:
            return True
        int_val = int(val)
        return int_val >= 0 and float(val) == int_val
    except (ValueError, TypeError):
        return False


def validate_dimensions(
    allocation: List[List[int]],
    maximum: List[List[int]],
    available: List[int],
    num_processes: Optional[int] = None,
    num_resources: Optional[int] = None,
) -> Tuple[bool, str]:
    """Validate that matrix and vector dimensions are consistent.

    Args:
        allocation: 2D list of shape (n, m)
        maximum: 2D list of shape (n, m)
        available: 1D list of length m
        num_processes: expected process count n (optional)
        num_resources: expected resource count m (optional)

    Returns:
        (is_valid, error_message)
    """
    if not allocation or not isinstance(allocation, list):
        return False, "Allocation matrix must be a non-empty list of lists."
    if not maximum or not isinstance(maximum, list):
        return False, "Maximum matrix must be a non-empty list of lists."
    if not available or not isinstance(available, list):
        return False, "Available vector must be a non-empty list."

    n = len(allocation)
    if n == 0:
        return False, "Number of processes must be at least 1."

    if len(maximum) != n:
        return False, f"Maximum matrix row count ({len(maximum)}) does not match Allocation row count ({n})."

    if num_processes is not None and n != num_processes:
        return False, f"Process count mismatch: expected {num_processes}, found {n} rows in Allocation."

    m = len(available)
    if m == 0:
        return False, "Number of resource types must be at least 1."

    if num_resources is not None and m != num_resources:
        return False, f"Resource count mismatch: expected {num_resources}, found {m} elements in Available."

    for i in range(n):
        if not isinstance(allocation[i], list):
            return False, f"Allocation row {i} (P{i}) is not a valid list."
        if len(allocation[i]) != m:
            return False, f"Allocation row {i} (P{i}) has {len(allocation[i])} columns; expected {m} resources."

        if not isinstance(maximum[i], list):
            return False, f"Maximum row {i} (P{i}) is not a valid list."
        if len(maximum[i]) != m:
            return False, f"Maximum row {i} (P{i}) has {len(maximum[i])} columns; expected {m} resources."

    return True, ""


def validate_system_state(
    allocation: List[List[int]],
    maximum: List[List[int]],
    available: List[int],
    total: Optional[List[int]] = None,
) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate all values and constraints in the system state.

    Checks:
    1. Dimension consistency.
    2. Non-negative integers for all matrix and vector cells.
    3. Allocation[i][j] <= Maximum[i][j] for all i, j.
    4. Total resource consistency (Total[j] == sum(Allocation[i][j]) + Available[j]) if Total provided.

    Returns:
        (is_valid, error_message, details_dict)
    """
    dim_ok, dim_err = validate_dimensions(allocation, maximum, available)
    if not dim_ok:
        return False, dim_err, {"error_type": "dimension_mismatch"}

    n = len(allocation)
    m = len(available)

    # 1. Validate Available vector elements
    for j, val in enumerate(available):
        if not is_non_negative_integer(val):
            return (
                False,
                f"Available vector at resource index {j} ('{chr(65+j)}') has invalid value '{val}'. Must be a non-negative integer.",
                {"error_type": "invalid_value", "location": f"Available[{j}]"},
            )

    # 2. Validate Allocation and Maximum matrix values
    for i in range(n):
        for j in range(m):
            alloc_val = allocation[i][j]
            max_val = maximum[i][j]
            res_name = chr(65 + j)

            if not is_non_negative_integer(alloc_val):
                return (
                    False,
                    f"Allocation[P{i}][{res_name}] has invalid value '{alloc_val}'. Must be a non-negative integer.",
                    {"error_type": "invalid_value", "location": f"Allocation[P{i}][{res_name}]"},
                )

            if not is_non_negative_integer(max_val):
                return (
                    False,
                    f"Maximum[P{i}][{res_name}] has invalid value '{max_val}'. Must be a non-negative integer.",
                    {"error_type": "invalid_value", "location": f"Maximum[P{i}][{res_name}]"},
                )

            # Check constraint: Allocation <= Maximum
            if int(alloc_val) > int(max_val):
                return (
                    False,
                    f"Constraint violation at Process P{i}, Resource {res_name}: "
                    f"Allocation ({alloc_val}) exceeds declared Maximum demand ({max_val}).",
                    {
                        "error_type": "allocation_exceeds_maximum",
                        "process": i,
                        "resource": j,
                        "allocation": alloc_val,
                        "maximum": max_val,
                    },
                )

    # 3. Validate Total vector if provided
    calculated_total = [
        sum(int(allocation[i][j]) for i in range(n)) + int(available[j])
        for j in range(m)
    ]

    if total is not None:
        if len(total) != m:
            return (
                False,
                f"Total vector length ({len(total)}) does not match resource count ({m}).",
                {"error_type": "dimension_mismatch", "location": "Total"},
            )
        for j in range(m):
            if not is_non_negative_integer(total[j]):
                return (
                    False,
                    f"Total vector at resource '{chr(65+j)}' has invalid value '{total[j]}'.",
                    {"error_type": "invalid_value", "location": f"Total[{j}]"},
                )
            if int(total[j]) != calculated_total[j]:
                return (
                    False,
                    f"Total resource mismatch for '{chr(65+j)}': Declared Total is {total[j]}, "
                    f"but sum of allocated ({sum(int(allocation[i][j]) for i in range(n))}) + "
                    f"available ({available[j]}) equals {calculated_total[j]}.",
                    {
                        "error_type": "total_mismatch",
                        "resource": j,
                        "declared": total[j],
                        "calculated": calculated_total[j],
                    },
                )

    return True, "System state is valid.", {
        "num_processes": n,
        "num_resources": m,
        "calculated_total": calculated_total,
    }


def calculate_need_matrix(
    allocation: List[List[int]],
    maximum: List[List[int]],
) -> List[List[int]]:
    """Calculate the remaining Need matrix: Need[i][j] = Maximum[i][j] - Allocation[i][j].

    Raises:
        ValidationError: if dimensions mismatch or Allocation > Maximum.
    """
    n = len(allocation)
    if n == 0 or len(maximum) != n:
        raise ValidationError(f"Dimension mismatch between Allocation ({n}) and Maximum ({len(maximum)}).")

    m = len(allocation[0])
    need = []
    for i in range(n):
        if len(allocation[i]) != m or len(maximum[i]) != m:
            raise ValidationError(f"Inconsistent column count at row {i}.")
        row = []
        for j in range(m):
            alloc_val = int(allocation[i][j])
            max_val = int(maximum[i][j])
            if alloc_val > max_val:
                raise ValidationError(
                    f"Allocation exceeds Maximum for P{i}, resource {chr(65+j)} ({alloc_val} > {max_val})."
                )
            row.append(max_val - alloc_val)
        need.append(row)
    return need


def validate_resource_request(
    process_id: int,
    request: List[int],
    allocation: List[List[int]],
    maximum: List[List[int]],
    available: List[int],
) -> Tuple[str, str, Dict[str, Any]]:
    """Validate a resource request following strict OS evaluation ordering.

    Evaluation Order:
    1. Validate process identifier (0 <= process_id < n).
    2. Reject negative or non-integer resource quantities.
    3. Check Request <= Need (Maximum claim check).
       - If violated -> 'INVALID_EXCEEDS_NEED'
    4. Check Request <= Available (Current availability check).
       - If violated -> 'WAITING_INSUFFICIENT_AVAILABLE'
    5. If both satisfied -> 'PROCEED_TO_SAFETY_CHECK'

    Returns:
        (status_code, explanation_message, details_dict)
    """
    # Step 1: Validate system state first
    sys_ok, sys_err, _ = validate_system_state(allocation, maximum, available)
    if not sys_ok:
        return "INVALID_SYSTEM_STATE", f"Cannot evaluate request: {sys_err}", {"error": sys_err}

    n = len(allocation)
    m = len(available)

    # Step 2: Validate process identifier
    if not isinstance(process_id, int) or process_id < 0 or process_id >= n:
        return (
            "INVALID_PROCESS_ID",
            f"Invalid process identifier '{process_id}'. Must be an integer between 0 and {n - 1} (P0 to P{n - 1}).",
            {"process_id": process_id, "valid_range": (0, n - 1)},
        )

    # Step 3: Validate request vector length and non-negative integers
    if not isinstance(request, list) or len(request) != m:
        return (
            "INVALID_REQUEST_DIMENSIONS",
            f"Request vector length ({len(request) if isinstance(request, list) else 0}) must match resource types count ({m}).",
            {"expected_length": m},
        )

    for j, val in enumerate(request):
        if not is_non_negative_integer(val):
            return (
                "INVALID_NEGATIVE_OR_TYPE",
                f"Request for resource {chr(65+j)} has invalid value '{val}'. Quantities must be non-negative integers.",
                {"resource": j, "val": val},
            )

    int_request = [int(v) for v in request]
    need = calculate_need_matrix(allocation, maximum)
    process_need = need[process_id]

    # Step 4: Check Request <= Need (OS Rule: Process must not exceed declared max claim)
    for j in range(m):
        if int_request[j] > process_need[j]:
            res_name = chr(65 + j)
            return (
                "INVALID_EXCEEDS_NEED",
                f"Error: Process P{process_id} requested {int_request[j]} of resource {res_name}, "
                f"which exceeds its declared remaining need of {process_need[j]}. (Maximum claim violation).",
                {
                    "process_id": process_id,
                    "resource": res_name,
                    "requested": int_request[j],
                    "remaining_need": process_need[j],
                },
            )

    # Step 5: Check Request <= Available (OS Rule: Can system allocate immediately?)
    for j in range(m):
        if int_request[j] > int(available[j]):
            res_name = chr(65 + j)
            return (
                "WAITING_INSUFFICIENT_AVAILABLE",
                f"Process P{process_id} must WAIT: Request for resource {res_name} ({int_request[j]}) "
                f"exceeds currently Available instances ({available[j]}). Request is valid but deferred.",
                {
                    "process_id": process_id,
                    "resource": res_name,
                    "requested": int_request[j],
                    "available": int(available[j]),
                },
            )

    # Step 6: Passed both checks
    return (
        "PROCEED_TO_SAFETY_CHECK",
        f"Request by Process P{process_id} satisfies both remaining Need and current Available checks. "
        "Tentative allocation may proceed to Banker's Safety evaluation.",
        {"process_id": process_id, "request": int_request, "remaining_need": process_need},
    )
