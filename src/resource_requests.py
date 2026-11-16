"""Resource Request Simulation and Deadlock Avoidance Module.

Implements the resource-request algorithm of Banker's Algorithm. Evaluates
requests in strict OS priority order, distinguishes between invalid, waiting,
unsafe denied, and granted states, and guarantees defensive state preservation.
"""

from typing import List, Dict, Any, Tuple, Optional
from copy import deepcopy
from src.validation import validate_resource_request, calculate_need_matrix, ValidationError
from src.bankers_algorithm import run_safety_algorithm


class RequestDecision:
    """Standardized decision categories for resource requests."""
    GRANTED_SAFE = "GRANTED_SAFE"
    WAITING_DEFERRED = "WAITING_DEFERRED"
    DENIED_UNSAFE = "DENIED_UNSAFE"
    INVALID_EXCEEDS_NEED = "INVALID_EXCEEDS_NEED"
    INVALID_INPUT = "INVALID_INPUT"


def request_resources(
    process_id: int,
    request: List[int],
    allocation: List[List[int]],
    maximum: List[List[int]],
    available: List[int],
) -> Dict[str, Any]:
    """Simulate a dynamic resource request and evaluate safety using Banker's Algorithm.

    Strict Order of Operations:
    1. Check Process ID validity.
    2. Check Request data types (non-negative integers) and dimensions.
    3. Check Request <= remaining Need. If violated -> INVALID_EXCEEDS_NEED.
    4. Check Request <= Available. If violated -> WAITING_DEFERRED (Request is valid, but process must wait).
    5. Create defensive copies for tentative state:
       - Tentative_Available = Available - Request
       - Tentative_Allocation[i] = Allocation[i] + Request
    6. Execute Banker's safety check on tentative state.
    7. If tentative state is safe -> GRANTED_SAFE.
    8. If tentative state is unsafe -> DENIED_UNSAFE (Discard tentative state, keep original).

    Args:
        process_id: Index of requesting process (0 to n-1).
        request: List of requested resource quantities.
        allocation: Current allocation matrix (n, m).
        maximum: Current maximum matrix (n, m).
        available: Current available vector (m).

    Returns:
        Dict containing:
            - decision (str): One of RequestDecision constants.
            - decision_label (str): Human-readable status badge text.
            - is_granted (bool): True if granted, False otherwise.
            - is_waiting (bool): True if deferred due to availability.
            - is_denied (bool): True if denied because tentative state is unsafe.
            - is_invalid (bool): True if input or claim is invalid.
            - explanation (str): Step-by-step plain-English explanation.
            - original_state (Dict[str, Any]): Deep copy of original state.
            - tentative_state (Optional[Dict[str, Any]]): Tentative state if safety check was run.
            - safety_result (Optional[Dict[str, Any]]): Result of Banker's check on tentative state.
            - final_state (Dict[str, Any]): Resulting state (updated if granted, unchanged otherwise).
    """
    # Defensive copies of original state to guarantee zero accidental side effects
    orig_allocation = deepcopy(allocation)
    orig_maximum = deepcopy(maximum)
    orig_available = list(available)

    orig_state = {
        "allocation": deepcopy(orig_allocation),
        "maximum": deepcopy(orig_maximum),
        "available": list(orig_available),
    }

    # Step 1-4: Validate request format, process_id, need claim, and availability
    status_code, validation_msg, details = validate_resource_request(
        process_id, request, orig_allocation, orig_maximum, orig_available
    )

    # Case A: Invalid process ID, invalid dimensions, or negative values
    if status_code in ("INVALID_PROCESS_ID", "INVALID_REQUEST_DIMENSIONS", "INVALID_NEGATIVE_OR_TYPE", "INVALID_SYSTEM_STATE"):
        return {
            "decision": RequestDecision.INVALID_INPUT,
            "decision_label": "INVALID — BAD INPUT / PROCESS IDENTIFIER",
            "is_granted": False,
            "is_waiting": False,
            "is_denied": False,
            "is_invalid": True,
            "explanation": f"Request rejected immediately: {validation_msg}",
            "original_state": orig_state,
            "tentative_state": None,
            "safety_result": None,
            "final_state": deepcopy(orig_state),
        }

    # Case B: Maximum claim violation (Request > Need)
    if status_code == "INVALID_EXCEEDS_NEED":
        return {
            "decision": RequestDecision.INVALID_EXCEEDS_NEED,
            "decision_label": "INVALID — REQUEST EXCEEDS REMAINING NEED",
            "is_granted": False,
            "is_waiting": False,
            "is_denied": False,
            "is_invalid": True,
            "explanation": (
                f"Error: {validation_msg} "
                "Operating System policy rejects requests that exceed a process's declared maximum claim."
            ),
            "original_state": orig_state,
            "tentative_state": None,
            "safety_result": None,
            "final_state": deepcopy(orig_state),
        }

    # Case C: Request <= Need but Request > Available -> WAITING / DEFERRED
    if status_code == "WAITING_INSUFFICIENT_AVAILABLE":
        return {
            "decision": RequestDecision.WAITING_DEFERRED,
            "decision_label": "WAITING / DEFERRED — INSUFFICIENT AVAILABLE RESOURCES",
            "is_granted": False,
            "is_waiting": True,
            "is_denied": False,
            "is_invalid": False,
            "explanation": (
                f"{validation_msg} "
                "The process is placed in a waiting queue until other processes release resources. "
                "The request is neither invalid nor permanently denied; current allocation remains unchanged."
            ),
            "original_state": orig_state,
            "tentative_state": None,
            "safety_result": None,
            "final_state": deepcopy(orig_state),
        }

    # Case D: Both checks passed -> Tentative Allocation Simulation
    m = len(orig_available)
    tentative_allocation = deepcopy(orig_allocation)
    tentative_available = list(orig_available)

    for j in range(m):
        tentative_allocation[process_id][j] += int(request[j])
        tentative_available[j] -= int(request[j])

    tentative_need = calculate_need_matrix(tentative_allocation, orig_maximum)

    tentative_state = {
        "allocation": deepcopy(tentative_allocation),
        "maximum": deepcopy(orig_maximum),
        "available": list(tentative_available),
        "need": tentative_need,
    }

    # Run Banker's Safety Check on the tentative state
    safety_result = run_safety_algorithm(
        tentative_allocation, orig_maximum, tentative_available
    )

    if safety_result["is_safe"]:
        # Case D1: Tentative state is safe -> GRANT request
        granted_state = {
            "allocation": deepcopy(tentative_allocation),
            "maximum": deepcopy(orig_maximum),
            "available": list(tentative_available),
        }
        return {
            "decision": RequestDecision.GRANTED_SAFE,
            "decision_label": "GRANTED — SAFE STATE PRESERVED",
            "is_granted": True,
            "is_waiting": False,
            "is_denied": False,
            "is_invalid": False,
            "explanation": (
                f"Request by Process P{process_id} for {request} is GRANTED. "
                f"Simulating the allocation leaves the system in a safe state with sequence: "
                f"{safety_result['safe_sequence_str']}. Deadlock avoidance condition satisfied."
            ),
            "original_state": orig_state,
            "tentative_state": tentative_state,
            "safety_result": safety_result,
            "final_state": granted_state,
        }
    else:
        # Case D2: Tentative state is unsafe -> DENY request and discard tentative state
        return {
            "decision": RequestDecision.DENIED_UNSAFE,
            "decision_label": "DENIED — WOULD PRODUCE UNSAFE STATE",
            "is_granted": False,
            "is_waiting": False,
            "is_denied": True,
            "is_invalid": False,
            "explanation": (
                f"Request by Process P{process_id} for {request} is DENIED. "
                f"Although resources are currently available, granting them would leave the system in an "
                f"UNSAFE state where no complete execution sequence can be guaranteed "
                f"(Unfinished processes: {[f'P{u}' for u in safety_result['unfinished_processes']]}). "
                f"Tentative allocation is discarded and original state is preserved."
            ),
            "original_state": orig_state,
            "tentative_state": tentative_state,
            "safety_result": safety_result,
            "final_state": deepcopy(orig_state),
        }
