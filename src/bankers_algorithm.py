"""Banker's Algorithm — Safety Algorithm Implementation.

Implements the classic Dijkstra / Habermann Banker's Safety Algorithm
for deadlock avoidance. Validates state, maintains step-by-step trace of Work
and Finish vectors, and generates mathematically rigorous safe sequences.
"""

from typing import List, Dict, Any, Tuple
from copy import deepcopy
from src.validation import validate_system_state, calculate_need_matrix, ValidationError


def run_safety_algorithm(
    allocation: List[List[int]],
    maximum: List[List[int]],
    available: List[int],
) -> Dict[str, Any]:
    """Execute Banker's Safety Algorithm on the given system state.

    Args:
        allocation: Matrix of shape (n, m) with currently allocated resources.
        maximum: Matrix of shape (n, m) with maximum resource claims.
        available: Vector of length m with currently available resources.

    Returns:
        A dictionary containing:
            - is_safe (bool): True if system is in a safe state, False otherwise.
            - safe_sequence (List[int]): Complete order of process execution indices.
            - safe_sequence_names (List[str]): Formatted names (e.g. ['P1', 'P3', ...]).
            - safe_sequence_str (str): Human-readable sequence representation.
            - trace (List[Dict[str, Any]]): Step-by-step record of Work and Finish transitions.
            - work_initial (List[int]): Starting Work vector (copy of Available).
            - work_final (List[int]): Final Work vector.
            - finish_states (List[bool]): Final status of Finish array.
            - unfinished_processes (List[int]): List of process indices that could not finish.
            - need_matrix (List[List[int]]): Calculated remaining need matrix.
            - explanation (str): Academic, student-friendly explanation of findings.

    Raises:
        ValidationError: If inputs violate dimensions, types, or allocation <= maximum.
    """
    # 1. Validate the system state
    is_valid, err_msg, _ = validate_system_state(allocation, maximum, available)
    if not is_valid:
        raise ValidationError(f"Invalid system state for safety check: {err_msg}")

    n = len(allocation)
    m = len(available)

    # 2. Calculate remaining Need matrix
    need = calculate_need_matrix(allocation, maximum)

    # 3. Initialize Work = Available, Finish = [False] * n
    work = [int(v) for v in available]
    work_initial = list(work)
    finish = [False] * n

    safe_sequence: List[int] = []
    trace: List[Dict[str, Any]] = []
    step_num = 1

    # 4. Iteratively search for an unfinished process with Need[i] <= Work
    while True:
        found_process = False

        for i in range(n):
            if not finish[i]:
                # Check if Need[i][j] <= Work[j] for all resource types j
                can_proceed = all(need[i][j] <= work[j] for j in range(m))

                if can_proceed:
                    work_before = list(work)
                    released = [int(allocation[i][j]) for j in range(m)]

                    # Simulate process completion and resource release: Work = Work + Allocation[i]
                    for j in range(m):
                        work[j] += released[j]

                    finish[i] = True
                    safe_sequence.append(i)
                    found_process = True

                    trace.append({
                        "step": step_num,
                        "process_id": i,
                        "process_name": f"P{i}",
                        "work_before": work_before,
                        "need": list(need[i]),
                        "allocation_released": released,
                        "work_after": list(work),
                        "finish_state": list(finish),
                        "explanation": (
                            f"Step {step_num}: Process P{i}'s remaining Need {need[i]} <= Work {work_before}. "
                            f"P{i} executes to completion and releases its Allocation {released}. "
                            f"New Work = {work}."
                        ),
                    })

                    step_num += 1
                    # Break to restart search from process 0 for deterministic sequence
                    break

        if not found_process:
            break

    # 5. Evaluate final safety status
    is_safe = all(finish)
    safe_seq_names = [f"P{idx}" for idx in safe_sequence]
    safe_seq_str = " < " + " -> ".join(safe_seq_names) + " > " if is_safe else "None (No safe sequence exists)"

    unfinished = [i for i, f in enumerate(finish) if not f]

    if is_safe:
        explanation = (
            f"The system is in a SAFE STATE. A complete execution sequence exists: {safe_seq_str}. "
            f"All {n} processes can execute to completion without risk of deadlock, "
            f"and total available resources after completion will be {work}."
        )
    else:
        unfinished_str = ", ".join(f"P{idx}" for idx in unfinished)
        blocked_reasons = []
        for u in unfinished:
            deficits = [
                f"{chr(65+j)}: need {need[u][j]} > work {work[j]}"
                for j in range(m)
                if need[u][j] > work[j]
            ]
            blocked_reasons.append(f"P{u} is blocked because [{', '.join(deficits)}]")

        explanation = (
            f"The system is in an UNSAFE STATE. No complete safe sequence exists. "
            f"After completing processes {', '.join(safe_seq_names) if safe_seq_names else 'none'}, "
            f"the remaining Work vector is {work}. "
            f"The following {len(unfinished)} process(es) cannot proceed: {unfinished_str}. "
            + "; ".join(blocked_reasons) + ". "
            "Note: An unsafe state does NOT necessarily mean a deadlock currently exists; "
            "rather, it means the OS cannot guarantee avoiding one under maximum possible claims."
        )

    return {
        "is_safe": is_safe,
        "safe_sequence": safe_sequence,
        "safe_sequence_names": safe_seq_names,
        "safe_sequence_str": safe_seq_str,
        "trace": trace,
        "work_initial": work_initial,
        "work_final": list(work),
        "finish_states": list(finish),
        "unfinished_processes": unfinished,
        "need_matrix": need,
        "explanation": explanation,
    }
