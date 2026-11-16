"""Deadlock Prevention Module.

Demonstrates deadlock prevention by actively enforcing resource-allocation policies
that mathematically eliminate one of the four Coffman conditions (primarily Circular Wait
via Hierarchical Resource Ordering, and Hold & Wait via Conservative Allocation).
"""

from typing import List, Dict, Any, Tuple, Optional
from copy import deepcopy


COFFMAN_CONDITIONS = {
    "mutual_exclusion": {
        "name": "Mutual Exclusion",
        "description": "At least one resource must be held in a non-shareable mode (only one process can use it at a time).",
        "prevention_approach": "Make resources shareable where possible (e.g. read-only files, spooled printers). However, intrinsically non-shareable hardware (e.g. mutexes, tape drives) cannot eliminate this condition.",
    },
    "hold_and_wait": {
        "name": "Hold and Wait",
        "description": "A process must be holding at least one resource and waiting to acquire additional resources held by others.",
        "prevention_approach": "Conservative Allocation Policy: Require processes to request ALL needed resources at once before execution, or release all held resources before requesting new ones.",
    },
    "no_preemption": {
        "name": "No Preemption",
        "description": "Resources cannot be forcibly confiscated from a process; they can only be released voluntarily after task completion.",
        "prevention_approach": "Preemption Policy: If a process holding resources requests an unavailable resource, all its held resources are preempted (released) and it must wait until all can be reacquired.",
    },
    "circular_wait": {
        "name": "Circular Wait",
        "description": "A closed chain of processes exists such that each process holds at least one resource needed by the next process in the chain.",
        "prevention_approach": "Hierarchical Resource Ordering (Havender's Algorithm): Impose a total global ordering on all resource types (e.g. R0 < R1 < R2). Processes must request resources only in strictly increasing order.",
    },
}


class HierarchicalOrderingPolicy:
    """Enforces total global resource ordering: R0 < R1 < R2 < ... < Rm-1.

    Rule:
    A process holding resource R_k can only request resource R_j if order(R_j) > order(R_k).
    Alternatively, to request a lower-ranked resource R_j (j <= k), the process must first
    release all currently held resources with order >= j.

    Eliminates Coffman Condition #4: Circular Wait.
    Proof: If process Pi holds Ra and requests Rb, then order(Rb) > order(Ra).
    In a chain P0 -> P1 -> ... -> Pk -> P0, we would require order(R0) < order(R1) < ... < order(R0),
    which is an impossible contradiction for a strict total ordering.
    """

    def __init__(self, resource_names: Optional[List[str]] = None):
        self.resource_names = resource_names or ["A", "B", "C", "D", "E"]

    def evaluate_request(
        self,
        process_id: int,
        currently_held: List[int],
        requested_vector: List[int],
    ) -> Dict[str, Any]:
        """Evaluate whether a proposed resource acquisition complies with Hierarchical Ordering.

        Args:
            process_id: Process index (e.g. 0 for P0).
            currently_held: List of resource quantities currently held by this process.
            requested_vector: List of resource quantities requested in this transaction.

        Returns:
            Dict containing:
                - allowed (bool): True if request complies with ordering, False if rejected.
                - violated_condition (str): Name of Coffman condition addressed.
                - reason (str): Explanation of acceptance or violation.
                - max_held_rank (int): Highest resource rank currently held.
                - requested_ranks (List[int]): Ranks of resources requested.
                - trade_offs (str): Academic trade-offs of this policy.
        """
        m = len(currently_held)
        held_indices = [j for j in range(m) if currently_held[j] > 0]
        req_indices = [j for j in range(m) if requested_vector[j] > 0]

        trade_offs = (
            "Trade-offs of Hierarchical Resource Ordering:\n"
            "+ Eliminates Circular Wait completely and provably without runtime safety check overhead.\n"
            "- Reduced Flexibility: Programmers must anticipate resource needs and acquire them in order.\n"
            "- Potential Starvation/Lower Utilization: Resources acquired early to satisfy ordering may sit idle."
        )

        if not req_indices:
            return {
                "allowed": True,
                "violated_condition": "Circular Wait",
                "reason": "Empty request satisfies hierarchical ordering.",
                "max_held_rank": max(held_indices) if held_indices else -1,
                "requested_ranks": [],
                "trade_offs": trade_offs,
            }

        if not held_indices:
            # Process holds nothing yet; any initial request is valid under ordering
            return {
                "allowed": True,
                "violated_condition": "Circular Wait",
                "reason": f"Process P{process_id} currently holds no resources. Initial acquisition is valid.",
                "max_held_rank": -1,
                "requested_ranks": req_indices,
                "trade_offs": trade_offs,
            }

        max_held_rank = max(held_indices)
        min_requested_rank = min(req_indices)

        max_held_name = self.resource_names[max_held_rank] if max_held_rank < len(self.resource_names) else f"R{max_held_rank}"
        min_req_name = self.resource_names[min_requested_rank] if min_requested_rank < len(self.resource_names) else f"R{min_requested_rank}"

        if min_requested_rank <= max_held_rank:
            # Violation: Attempting to acquire equal or lower ranked resource while holding higher
            return {
                "allowed": False,
                "violated_condition": "Circular Wait",
                "reason": (
                    f"POLICY VIOLATION (Circular Wait Prevention): Process P{process_id} holds "
                    f"higher-ranked resource '{max_held_name}' (rank {max_held_rank + 1}) "
                    f"and attempted to request lower/equal-ranked resource '{min_req_name}' (rank {min_requested_rank + 1}). "
                    f"Under Hierarchical Ordering ({' < '.join(self.resource_names[:m])}), "
                    f"a process cannot request lower-ranked resources while holding higher-ranked ones. "
                    f"Action: Request REJECTED. P{process_id} must release '{max_held_name}' before requesting '{min_req_name}'."
                ),
                "max_held_rank": max_held_rank,
                "requested_ranks": req_indices,
                "trade_offs": trade_offs,
            }

        return {
            "allowed": True,
            "violated_condition": "Circular Wait",
            "reason": (
                f"POLICY COMPLIANT: Process P{process_id} holds '{max_held_name}' (rank {max_held_rank + 1}) "
                f"and requests '{min_req_name}' (rank {min_requested_rank + 1}). "
                f"Since {min_requested_rank + 1} > {max_held_rank + 1}, strict ascending order is preserved. "
                "Request PERMITTED under prevention policy."
            ),
            "max_held_rank": max_held_rank,
            "requested_ranks": req_indices,
            "trade_offs": trade_offs,
        }


class HoldAndWaitPreventionPolicy:
    """Enforces Hold-and-Wait prevention (Conservative Allocation).

    Rule:
    A process must request ALL needed resources at once before beginning execution.
    If even one requested resource cannot be satisfied, NONE are allocated,
    and the process holds nothing while waiting.
    """

    @staticmethod
    def evaluate_request(
        process_id: int,
        currently_held: List[int],
        requested_vector: List[int],
        total_needed: List[int],
        available_vector: List[int],
    ) -> Dict[str, Any]:
        """Evaluate request under conservative Hold & Wait prevention."""
        m = len(currently_held)
        has_held = any(v > 0 for v in currently_held)

        trade_offs = (
            "Trade-offs of Hold & Wait Prevention (Conservative Allocation):\n"
            "+ Completely eliminates Hold and Wait condition.\n"
            "- Severely reduced resource utilization: Resources reserved at start may not be used until later.\n"
            "- High probability of starvation for processes with large resource demands."
        )

        if has_held:
            return {
                "allowed": False,
                "violated_condition": "Hold and Wait",
                "reason": (
                    f"POLICY VIOLATION: Process P{process_id} already holds resources {currently_held}. "
                    "Under Hold & Wait prevention, incremental requests while holding resources are disallowed. "
                    f"P{process_id} must release all held resources before making a new claim."
                ),
                "trade_offs": trade_offs,
            }

        # Check if all needed resources can be satisfied simultaneously
        can_satisfy_all = all(int(requested_vector[j]) <= int(available_vector[j]) for j in range(m))

        if can_satisfy_all:
            return {
                "allowed": True,
                "violated_condition": "Hold and Wait",
                "reason": (
                    f"POLICY COMPLIANT: Process P{process_id} requested all resources simultaneously "
                    "and holds zero prior resources. All resources are currently available and allocated in bulk."
                ),
                "trade_offs": trade_offs,
            }
        else:
            return {
                "allowed": False,
                "violated_condition": "Hold and Wait",
                "reason": (
                    f"DEFERRED ALL-OR-NOTHING: Process P{process_id} requested resources, but some are currently "
                    "unavailable. Under Conservative Allocation, NO resources are allocated piecemeal; process waits empty-handed."
                ),
                "trade_offs": trade_offs,
            }
