"""OS Deadlock Analysis & Resource Allocation Dashboard
Core Algorithm and Analytical Package
"""

__version__ = "1.0.0"

from src.test_scenarios import (
    SAFE_SYSTEM_CONFIG,
    DEADLOCKED_SYSTEM_CONFIG,
    REQUEST_SIMULATION_TEST_CASES,
    get_request_simulation_test_cases,
    load_request_test_case,
    execute_loaded_request_test_case,
    run_all_test_scenarios,
    run_tc1_safe_state,
    run_tc2_request_exceeds_available,
    run_tc3_request_produces_unsafe_state,
    run_tc4_deadlock_detection,
    run_tc5_prevention_policy,
    run_tc6_boundary_and_invalid_inputs,
)

__all__ = [
    "SAFE_SYSTEM_CONFIG",
    "DEADLOCKED_SYSTEM_CONFIG",
    "REQUEST_SIMULATION_TEST_CASES",
    "get_request_simulation_test_cases",
    "load_request_test_case",
    "execute_loaded_request_test_case",
    "run_all_test_scenarios",
    "run_tc1_safe_state",
    "run_tc2_request_exceeds_available",
    "run_tc3_request_produces_unsafe_state",
    "run_tc4_deadlock_detection",
    "run_tc5_prevention_policy",
    "run_tc6_boundary_and_invalid_inputs",
]
