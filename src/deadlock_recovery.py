"""Deadlock Recovery Module.

Simulates recovery from a detected deadlock state via process termination and
resource preemption. Re-evaluates system state dynamically after recovery actions
to verify whether deadlock is genuinely resolved or persists among remaining processes.
"""

from typing import List, Dict, Any, Tuple, Optional
from copy import deepcopy
from src.deadlock_detection import detect_deadlock_multi_instance


def suggest_victim_processes(
    allocation: List[List[int]],
    deadlocked_indices: List[int],
) -> List[Dict[str, Any]]:
    """Rank deadlocked processes by victim selection heuristics.

    Heuristics:
    1. Maximum resources held: Aborting this process releases the most resources to unblock others.
    2. Minimum resources held: Aborting this process incurs the lowest computational penalty.
    """
    candidates = []
    for idx in deadlocked_indices:
        total_held = sum(allocation[idx])
        candidates.append({
            "process_id": idx,
            "process_name": f"P{idx}",
            "total_resources_held": total_held,
            "held_vector": list(allocation[idx]),
        })

    # Sort descending by total resources held (fastest unblocking heuristic)
    candidates_by_impact = sorted(candidates, key=lambda c: c["total_resources_held"], reverse=True)
    return candidates_by_impact


def recover_by_process_termination(
    victim_id: int,
    allocation: List[List[int]],
    request_matrix: List[List[int]],
    available: List[int],
) -> Dict[str, Any]:
    """Recover from deadlock by terminating a victim process and reclaiming its resources.

    Steps:
    1. Reclaim all resources held by victim_id:
       - Available[j] = Available[j] + Allocation[victim_id][j]
       - Allocation[victim_id][j] = 0
       - Request[victim_id][j] = 0
    2. Execute deadlock detection on the updated system state.
    3. Determine whether the deadlock is completely resolved or if additional processes remain blocked.

    Args:
        victim_id: Index of the process to terminate.
        allocation: Matrix of currently allocated resources (n, m).
        request_matrix: Matrix of outstanding requests (n, m).
        available: Currently available vector (m).

    Returns:
        Dict containing:
            - victim_id (int): Terminated process.
            - victim_name (str): Terminated process label (e.g. 'P1').
            - resources_reclaimed (List[int]): Vector of released resources.
            - state_before (Dict): State prior to termination.
            - state_after (Dict): State following termination and resource reclamation.
            - is_fully_resolved (bool): True if zero remaining processes are deadlocked.
            - remaining_deadlocked (List[int]): Indices of processes still in deadlock, if any.
            - post_recovery_detection (Dict): Result of detection on state_after.
            - explanation (str): Academic walkthrough of the recovery outcome.
            - recovery_costs (str): Trade-offs and costs of process termination.
    """
    n = len(allocation)
    m = len(available)

    if victim_id < 0 or victim_id >= n:
        raise ValueError(f"Invalid victim process index: {victim_id}")

    # Capture state before recovery
    state_before = {
        "allocation": deepcopy(allocation),
        "request": deepcopy(request_matrix),
        "available": list(available),
    }

    # Perform reclamation
    reclaimed = list(allocation[victim_id])
    new_allocation = deepcopy(allocation)
    new_request = deepcopy(request_matrix)
    new_available = list(available)

    for j in range(m):
        new_available[j] += reclaimed[j]
        new_allocation[victim_id][j] = 0
        new_request[victim_id][j] = 0

    state_after = {
        "allocation": new_allocation,
        "request": new_request,
        "available": new_available,
    }

    # Run detection on new state to verify whether deadlock is resolved
    post_detection = detect_deadlock_multi_instance(new_allocation, new_request, new_available)

    is_resolved = not post_detection["is_deadlocked"]
    remaining_deadlocked = post_detection["deadlocked_processes"]

    recovery_costs = (
        "Costs and Limitations of Process Termination:\n"
        "1. Lost Work: All computational progress made by the terminated process is lost.\n"
        "2. State Inconsistency: If the victim was modifying a shared file or database, "
        "partial state may be corrupted unless transactional rollback (checkpointing) is implemented.\n"
        "3. Cascading Aborts: If remaining processes cannot make progress, multiple victims may need to be aborted."
    )

    if is_resolved:
        explanation = (
            f"RECOVERY SUCCESSFUL! Process P{victim_id} was terminated, releasing its allocated resources: {reclaimed}. "
            f"Available resources increased from {state_before['available']} to {new_available}. "
            f"Re-running deadlock detection confirms: ALL remaining active processes "
            f"({[f'P{idx}' for idx in post_detection['resolution_order']]}) can now obtain their requested "
            "resources and complete execution. The deadlock is completely eliminated."
        )
    else:
        still_blocked_names = [f"P{idx}" for idx in remaining_deadlocked]
        explanation = (
            f"PARTIAL RECOVERY: Process P{victim_id} was terminated, releasing {reclaimed}. "
            f"Available resources increased to {new_available}. "
            f"However, re-running deadlock detection reveals that processes {', '.join(still_blocked_names)} "
            "ARE STILL IN DEADLOCK. Terminating P{victim_id} alone did not provide sufficient resources "
            "to satisfy their pending requests. An additional victim must be selected."
        )

    return {
        "victim_id": victim_id,
        "victim_name": f"P{victim_id}",
        "resources_reclaimed": reclaimed,
        "state_before": state_before,
        "state_after": state_after,
        "is_fully_resolved": is_resolved,
        "remaining_deadlocked": remaining_deadlocked,
        "post_recovery_detection": post_detection,
        "explanation": explanation,
        "recovery_costs": recovery_costs,
    }
