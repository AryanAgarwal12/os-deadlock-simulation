"""Deadlock Detection Module.

Implements deadlock detection algorithms for both multiple-instance resource systems
(vector/matrix reduction) and single-instance resource systems (Resource Allocation Graph
with cycle detection).

Crucial Academic Distinction:
In Deadlock Detection, the 'Request' matrix represents *current actual blocked requests*,
NOT future potential demands (Maximum - Allocation). Banker's Algorithm avoids deadlocks
using maximum claims; Detection discovers deadlocks that already exist using current requests.
"""

from typing import List, Dict, Any, Tuple, Optional
from copy import deepcopy


def detect_deadlock_multi_instance(
    allocation: List[List[int]],
    request_matrix: List[List[int]],
    available: List[int],
) -> Dict[str, Any]:
    """Execute Deadlock Detection algorithm for multiple-instance resource systems.

    Algorithm (Silberschatz / Galvin / Gagne):
    1. Work = Available vector copy.
    2. Finish[i] = True if Allocation[i] is all zeros, else False.
       (If a process currently holds no resources, it cannot be part of a deadlock).
    3. Find an index i such that Finish[i] == False and Request[i] <= Work.
    4. If found:
       - Work = Work + Allocation[i]
       - Finish[i] = True
       - Repeat step 3.
    5. If no such i exists:
       - Any process with Finish[i] == False is DEADLOCKED.

    Args:
        allocation: Currently allocated resources to each process (n, m).
        request_matrix: Outstanding, currently requested resources by each process (n, m).
        available: Currently available unallocated instances of each resource (m).

    Returns:
        Dict containing:
            - is_deadlocked (bool): True if one or more processes are deadlocked.
            - deadlocked_processes (List[int]): Indices of deadlocked processes.
            - deadlocked_process_names (List[str]): Names of deadlocked processes (e.g. ['P1', 'P2']).
            - resolution_order (List[int]): Sequence of processes that completed successfully.
            - trace (List[Dict[str, Any]]): Step-by-step progress trace.
            - initial_finish (List[bool]): Finish vector after zero-allocation initialization.
            - final_finish (List[bool]): Final Finish vector.
            - work_initial (List[int]): Initial Work vector.
            - work_final (List[int]): Final Work vector.
            - model_assumptions (str): Explicitly stated resource model assumptions.
            - explanation (str): Academic interpretation of findings.
            - limitations (str): Algorithmic constraints and overhead discussion.
    """
    n = len(allocation)
    m = len(available)

    work = [int(v) for v in available]
    work_initial = list(work)

    # Step 2: Initialize Finish vector
    # A process holding no resources cannot hold resources another process is waiting for.
    finish = [False] * n
    for i in range(n):
        if all(int(allocation[i][j]) == 0 for j in range(m)):
            finish[i] = True

    initial_finish = list(finish)
    resolution_order: List[int] = []
    trace: List[Dict[str, Any]] = []
    step_num = 1

    # Record any processes marked finished initially due to zero allocation
    init_completed = [i for i in range(n) if initial_finish[i]]
    if init_completed:
        trace.append({
            "step": 0,
            "process_id": -1,
            "process_name": "System Initialization",
            "work_before": list(work),
            "request": [0] * m,
            "allocation_released": [0] * m,
            "work_after": list(work),
            "finish_state": list(finish),
            "explanation": (
                f"Processes {[f'P{idx}' for idx in init_completed]} hold zero allocated resources "
                "and are marked Finish=True immediately (cannot participate in deadlock)."
            ),
        })

    # Step 3-4: Search for unfinished process whose request can be satisfied
    while True:
        found = False
        for i in range(n):
            if not finish[i]:
                can_satisfy = all(int(request_matrix[i][j]) <= work[j] for j in range(m))
                if can_satisfy:
                    work_before = list(work)
                    released = [int(allocation[i][j]) for j in range(m)]

                    for j in range(m):
                        work[j] += released[j]

                    finish[i] = True
                    resolution_order.append(i)
                    found = True

                    trace.append({
                        "step": step_num,
                        "process_id": i,
                        "process_name": f"P{i}",
                        "work_before": work_before,
                        "request": list(request_matrix[i]),
                        "allocation_released": released,
                        "work_after": list(work),
                        "finish_state": list(finish),
                        "explanation": (
                            f"Step {step_num}: Process P{i}'s outstanding Request {request_matrix[i]} "
                            f"<= Work {work_before}. P{i} can obtain its requested resources, "
                            f"execute, and release its Allocation {released}. New Work = {work}."
                        ),
                    })
                    step_num += 1
                    break

        if not found:
            break

    deadlocked_indices = [i for i, f in enumerate(finish) if not f]
    is_deadlocked = len(deadlocked_indices) > 0
    deadlocked_names = [f"P{idx}" for idx in deadlocked_indices]

    model_assumptions = (
        "Multiple-Instance Resource Model Assumptions:\n"
        "1. Processes do not voluntarily release resources before obtaining all requested items.\n"
        "2. Outstanding Request matrix represents active blocked requests, not future potential needs.\n"
        "3. Once a process's request is satisfied, it completes and releases all currently held resources.\n"
        "4. Processes holding 0 resources cannot block others and cannot be part of a deadlock."
    )

    limitations = (
        "Limitations of Multiple-Instance Deadlock Detection:\n"
        "1. Detection Overhead: Invoking the algorithm incurs O(m * n^2) computational cost.\n"
        "2. Frequency Dilemma: If invoked too frequently, CPU cycles are wasted; if invoked rarely, "
        "deadlocked processes remain frozen, wasting resources and degrading throughput.\n"
        "3. Non-preemption Assumption: Assumes processes cannot be suspended or forced to yield resources."
    )

    if is_deadlocked:
        explanation = (
            f"DEADLOCK DETECTED! The system contains {len(deadlocked_indices)} deadlocked process(es): "
            f"{', '.join(deadlocked_names)}. "
            f"After satisfying resolvable processes ({[f'P{x}' for x in resolution_order]}), "
            f"available Work is {work}. "
            f"None of the remaining processes can proceed because each process's request exceeds remaining Work, "
            "forming an unresolvable waiting dependency."
        )
    else:
        explanation = (
            f"NO DEADLOCK DETECTED. All processes can successfully acquire their outstanding requests "
            f"and terminate. A feasible completion order is: "
            f"{' -> '.join(f'P{idx}' for idx in resolution_order) if resolution_order else 'All finished initially'}."
        )

    return {
        "is_deadlocked": is_deadlocked,
        "deadlocked_processes": deadlocked_indices,
        "deadlocked_process_names": deadlocked_names,
        "resolution_order": resolution_order,
        "trace": trace,
        "initial_finish": initial_finish,
        "final_finish": list(finish),
        "work_initial": work_initial,
        "work_final": list(work),
        "model_assumptions": model_assumptions,
        "explanation": explanation,
        "limitations": limitations,
    }


def find_graph_cycles(adj_list: Dict[str, List[str]]) -> List[List[str]]:
    """Find simple cycles in a directed graph using DFS.

    Args:
        adj_list: Dictionary mapping node_name to list of outgoing neighbor node_names.

    Returns:
        List of cycles, where each cycle is a list of node names forming a closed loop.
    """
    cycles: List[List[str]] = []
    visited: set = set()
    rec_stack: List[str] = []

    def dfs(node: str):
        visited.add(node)
        rec_stack.append(node)

        for neighbor in adj_list.get(node, []):
            if neighbor not in visited:
                dfs(neighbor)
            elif neighbor in rec_stack:
                # Cycle found from neighbor to current node
                cycle_start_idx = rec_stack.index(neighbor)
                cycle = rec_stack[cycle_start_idx:] + [neighbor]
                # Normalize cycle to avoid duplicates
                cycles.append(cycle)

        rec_stack.pop()

    for n in list(adj_list.keys()):
        if n not in visited:
            dfs(n)

    return cycles


def analyze_resource_allocation_graph(
    allocation: List[List[int]],
    request_matrix: List[List[int]],
    total_resources: List[int],
) -> Dict[str, Any]:
    """Construct and analyze a Resource Allocation Graph (RAG).

    Constructs:
    - Assignment edges: R_j -> P_i for each unit of R_j allocated to P_i.
    - Request edges: P_i -> R_j for each unit of R_j requested by P_i.
    - Evaluates cycle presence.
    - Explains single-instance vs multiple-instance deadlock implications.
    """
    n = len(allocation)
    m = len(total_resources)

    nodes = [f"P{i}" for i in range(n)] + [f"R{chr(65+j)}" for j in range(m)]
    edges = []
    adj_list: Dict[str, List[str]] = {node: [] for node in nodes}

    # Assignment edges: Resource -> Process
    for i in range(n):
        for j in range(m):
            if int(allocation[i][j]) > 0:
                res_node = f"R{chr(65+j)}"
                proc_node = f"P{i}"
                edges.append({
                    "from": res_node,
                    "to": proc_node,
                    "type": "assignment",
                    "count": int(allocation[i][j]),
                    "label": f"Assigned ({allocation[i][j]})",
                })
                adj_list[res_node].append(proc_node)

    # Request edges: Process -> Resource
    for i in range(n):
        for j in range(m):
            if int(request_matrix[i][j]) > 0:
                proc_node = f"P{i}"
                res_node = f"R{chr(65+j)}"
                edges.append({
                    "from": proc_node,
                    "to": res_node,
                    "type": "request",
                    "count": int(request_matrix[i][j]),
                    "label": f"Requests ({request_matrix[i][j]})",
                })
                adj_list[proc_node].append(res_node)

    cycles = find_graph_cycles(adj_list)
    has_cycle = len(cycles) > 0
    is_single_instance = all(int(t) == 1 for t in total_resources)

    if is_single_instance:
        if has_cycle:
            rag_conclusion = (
                "CYCLE DETECTED IN SINGLE-INSTANCE SYSTEM: "
                "Because every resource type contains exactly 1 instance, "
                "the detected cycle is BOTH NECESSARY AND SUFFICIENT FOR DEADLOCK. "
                f"Deadlock exists along cycle: {' -> '.join(cycles[0])}."
            )
        else:
            rag_conclusion = (
                "NO CYCLE IN SINGLE-INSTANCE SYSTEM: "
                "In a single-instance resource system, absence of cycles guarantees no deadlock."
            )
    else:
        if has_cycle:
            rag_conclusion = (
                "CYCLE DETECTED IN MULTIPLE-INSTANCE SYSTEM: "
                "In systems with multiple resource instances, a cycle is a NECESSARY condition, "
                "but NOT A SUFFICIENT condition for deadlock. "
                "Processes outside the cycle may finish and release instances, breaking the wait."
            )
        else:
            rag_conclusion = (
                "NO CYCLE DETECTED: No circular dependency exists among processes and resources."
            )

    return {
        "nodes": nodes,
        "edges": edges,
        "cycles": cycles,
        "has_cycle": has_cycle,
        "is_single_instance": is_single_instance,
        "conclusion": rag_conclusion,
    }
