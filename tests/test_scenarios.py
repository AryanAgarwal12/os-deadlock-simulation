"""Unit tests for TC1-TC6 and Reporting (tests/test_scenarios.py)."""

import pytest
import sys
from src.test_scenarios import (
    run_tc1_safe_state,
    run_tc2_request_exceeds_available,
    run_tc3_request_produces_unsafe_state,
    run_tc4_deadlock_detection,
    run_tc5_prevention_policy,
    run_tc6_boundary_and_invalid_inputs,
    run_all_test_scenarios,
)
from src.reporting import (
    export_test_results_to_csv,
    export_test_results_to_markdown,
    export_ai_usage_record_to_csv,
    export_ai_usage_record_to_markdown,
)


def test_tc1_safe_state_passes():
    res = run_tc1_safe_state()
    assert res["status"] == "PASS"
    assert res["test_id"] == "TC1"


def test_tc2_request_exceeds_available_passes():
    res = run_tc2_request_exceeds_available()
    assert res["status"] == "PASS"
    assert res["test_id"] == "TC2"


def test_tc3_request_produces_unsafe_state_passes():
    res = run_tc3_request_produces_unsafe_state()
    assert res["status"] == "PASS"
    assert res["test_id"] == "TC3"


def test_tc4_deadlock_detection_passes():
    res = run_tc4_deadlock_detection()
    assert res["status"] == "PASS"
    assert res["test_id"] == "TC4"


def test_tc5_prevention_policy_passes():
    res = run_tc5_prevention_policy()
    assert res["status"] == "PASS"
    assert res["test_id"] == "TC5"


def test_tc6_boundary_and_invalid_inputs_passes():
    res = run_tc6_boundary_and_invalid_inputs()
    assert res["status"] == "PASS"
    assert res["test_id"] == "TC6"


def test_run_all_test_scenarios():
    all_results = run_all_test_scenarios()
    assert len(all_results) == 6
    assert all(tc["status"] == "PASS" for tc in all_results)


def test_reporting_export_csv_and_markdown():
    all_results = run_all_test_scenarios()
    csv_str = export_test_results_to_csv(all_results)
    assert "TC1" in csv_str
    assert "PASS" in csv_str

    md_str = export_test_results_to_markdown(all_results)
    assert "# Operating Systems IA Activity 2" in md_str
    assert "TC1" in md_str
    assert "✅ PASS" in md_str


def test_ai_usage_reporting():
    rows = [
        {
            "AI Tool Used": "Antigravity IDE",
            "Purpose": "Dashboard architecture and test automation",
            "Output Generated": "Modular Python files and Streamlit UI",
            "Student Verification": "Verified against textbook theorems",
        }
    ]
    csv_str = export_ai_usage_record_to_csv(rows)
    assert "Antigravity IDE" in csv_str
    md_str = export_ai_usage_record_to_markdown(rows)
    assert "AI Usage Record" in md_str


def test_request_simulation_test_cases_loading():
    from src.test_scenarios import (
        get_request_simulation_test_cases,
        load_request_test_case,
        execute_loaded_request_test_case,
    )
    from src.resource_requests import RequestDecision

    cases = get_request_simulation_test_cases()
    assert "TC1" in cases
    assert "TC2" in cases
    assert "TC3" in cases
    assert "TC4" in cases
    assert "TC6.5" in cases

    # TC1 execution: P1 requests [1, 0, 2] -> GRANTED_SAFE
    res1 = execute_loaded_request_test_case("TC1")
    assert res1["decision"] == RequestDecision.GRANTED_SAFE
    assert res1["is_granted"] is True

    # TC2 execution: P4 requests [4, 2, 0] -> WAITING_DEFERRED
    res2 = execute_loaded_request_test_case("TC2")
    assert res2["decision"] == RequestDecision.WAITING_DEFERRED
    assert res2["is_waiting"] is True

    # TC3 execution: P1 requests [1, 0] -> DENIED_UNSAFE with rollback
    res3 = execute_loaded_request_test_case("TC3")
    assert res3["decision"] == RequestDecision.DENIED_UNSAFE
    assert res3["is_denied"] is True

    # TC4 execution: Deadlock detection -> is_deadlocked is True
    res4 = execute_loaded_request_test_case("TC4")
    assert res4["is_deadlocked"] is True
    assert set(res4["deadlocked_processes"]) == {0, 1, 2}

    # TC6.5 execution: P0 requests [8, 0, 0] > Need [7, 4, 3] -> INVALID_EXCEEDS_NEED
    res5 = execute_loaded_request_test_case("TC6.5")
    assert res5["decision"] == RequestDecision.INVALID_EXCEEDS_NEED


def test_tc1_request_simulation_details():
    """Verify TC1 inputs, execution, decision, and pre/post state consistency."""
    from src.test_scenarios import load_request_test_case
    from src.resource_requests import request_resources, RequestDecision

    tc = load_request_test_case("TC1")
    assert tc["process_id"] == 1
    assert tc["request"] == [1, 0, 2]
    assert tc["available"] == [3, 3, 2]
    assert tc["allocation"][1] == [2, 0, 0]
    assert tc["maximum"][1] == [3, 2, 2]

    res = request_resources(
        tc["process_id"],
        tc["request"],
        tc["allocation"],
        tc["maximum"],
        tc["available"],
    )

    assert res["decision"] == RequestDecision.GRANTED_SAFE
    assert res["is_granted"] is True
    assert res["safety_result"] is not None
    assert res["safety_result"]["is_safe"] is True

    # Pre-evaluation state
    assert res["original_state"]["available"] == [3, 3, 2]
    assert res["original_state"]["allocation"][1] == [2, 0, 0]

    # Post-evaluation granted state
    assert res["final_state"]["available"] == [2, 3, 0]
    assert res["final_state"]["allocation"][1] == [3, 0, 2]


def test_tc2_request_simulation_preserves_state():
    """Verify TC2 returns WAITING_DEFERRED and preserves original system state."""
    from src.test_scenarios import load_request_test_case
    from src.resource_requests import request_resources, RequestDecision

    tc = load_request_test_case("TC2")
    assert tc["process_id"] == 4
    assert tc["request"] == [4, 2, 0]

    res = request_resources(
        tc["process_id"],
        tc["request"],
        tc["allocation"],
        tc["maximum"],
        tc["available"],
    )

    assert res["decision"] == RequestDecision.WAITING_DEFERRED
    assert res["is_granted"] is False
    assert res["is_waiting"] is True

    # Defensive immutability: final state must match original state
    assert res["final_state"]["available"] == res["original_state"]["available"]
    assert res["final_state"]["allocation"] == res["original_state"]["allocation"]
    assert res["final_state"]["available"] == [3, 3, 2]
    assert res["final_state"]["allocation"][4] == [0, 0, 2]


def test_tc3_request_simulation_denial_and_rollback():
    """Verify TC3 returns DENIED_UNSAFE and rolls back tentative state completely."""
    from src.test_scenarios import load_request_test_case
    from src.resource_requests import request_resources, RequestDecision

    tc = load_request_test_case("TC3")
    assert tc["process_id"] == 1
    assert tc["request"] == [1, 0]

    res = request_resources(
        tc["process_id"],
        tc["request"],
        tc["allocation"],
        tc["maximum"],
        tc["available"],
    )

    assert res["decision"] == RequestDecision.DENIED_UNSAFE
    assert res["is_granted"] is False
    assert res["is_denied"] is True

    # Complete rollback verification
    assert res["final_state"]["available"] == [1, 1]
    assert res["final_state"]["allocation"][1] == [1, 0]
    assert res["final_state"]["available"] == res["original_state"]["available"]
    assert res["final_state"]["allocation"] == res["original_state"]["allocation"]


@pytest.mark.skipif(
    sys.platform == "win32" and sys.version_info >= (3, 13),
    reason="Streamlit AppTest runner deadlock on Windows Python 3.13+",
)
def test_page4_streamlit_ui_integration():
    """AppTest integration test verifying Page 4 selector, evaluation, and rollback table."""
    import os
    from streamlit.testing.v1 import AppTest

    app_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
    at = AppTest.from_file(app_path)
    at.run()
    at.sidebar.radio[0].set_value("4. Resource Request Simulation").run()

    # 1. Test TC1 Load & Evaluate Immediately
    load_eval_btn = [b for b in at.button if "Load & Evaluate Immediately" in b.label][0]
    load_eval_btn.click().run()

    # Process P1 must be selected, NOT P0
    assert at.selectbox(key="sim_proc_dropdown").value == 1
    assert at.number_input(key="req_input_0").value == 1
    assert at.number_input(key="req_input_1").value == 0
    assert at.number_input(key="req_input_2").value == 2

    # Verify status is GRANTED
    rendered_statuses = [m.value for m in at.markdown if "STATUS:" in m.value]
    assert len(rendered_statuses) > 0
    assert "STATUS: GRANTED — SAFE STATE PRESERVED" in rendered_statuses[0]

    # Verify Rollback / State Comparison Table
    rollback_dfs = [df.value for df in at.dataframe if "Metric" in df.value.columns]
    assert len(rollback_dfs) > 0
    comp_df = rollback_dfs[0]
    avail_row = comp_df[comp_df["Metric"] == "Available Vector"].iloc[0]
    assert avail_row["Original State"] == "[3, 3, 2]"
    assert avail_row["Tentative / Final State"] == "[2, 3, 0]"
    assert avail_row["State Mutated?"] == "Yes (Granted)"

    # 2. Test TC2 Load & Evaluate Immediately
    at.selectbox(key="tc_selector_dropdown").set_value("TC2 — Request Exceeds Available / Deferred (Waiting)").run()
    load_eval_btn2 = [b for b in at.button if "Load & Evaluate Immediately" in b.label][0]
    load_eval_btn2.click().run()

    assert at.selectbox(key="sim_proc_dropdown").value == 4
    rendered_statuses2 = [m.value for m in at.markdown if "STATUS:" in m.value]
    assert "STATUS: WAITING / DEFERRED" in rendered_statuses2[0]

    comp_df2 = [df.value for df in at.dataframe if "Metric" in df.value.columns][0]
    avail_row2 = comp_df2[comp_df2["Metric"] == "Available Vector"].iloc[0]
    assert avail_row2["Original State"] == "[3, 3, 2]"
    assert avail_row2["Tentative / Final State"] == "[3, 3, 2]"
    assert avail_row2["State Mutated?"] == "No (Preserved)"

    # 3. Test TC3 Load & Evaluate Immediately
    at.selectbox(key="tc_selector_dropdown").set_value("TC3 — Unsafe Tentative State / Denied with Rollback").run()
    load_eval_btn3 = [b for b in at.button if "Load & Evaluate Immediately" in b.label][0]
    load_eval_btn3.click().run()

    assert at.selectbox(key="sim_proc_dropdown").value == 1
    rendered_statuses3 = [m.value for m in at.markdown if "STATUS:" in m.value]
    assert "STATUS: DENIED — UNSAFE TENTATIVE STATE" in rendered_statuses3[0]

    comp_df3 = [df.value for df in at.dataframe if "Metric" in df.value.columns][0]
    avail_row3 = comp_df3[comp_df3["Metric"] == "Available Vector"].iloc[0]
    assert avail_row3["Original State"] == "[1, 1]"
    assert avail_row3["Tentative / Final State"] == "[1, 1]"
    assert avail_row3["State Mutated?"] == "No (Preserved)"

    # 4. Test TC4 Navigation to Deadlock Detection
    at.selectbox(key="tc_selector_dropdown").set_value("TC4 — Deadlock Detection Scenario (Outstanding Requests)").run()
    btn4 = [b for b in at.button if "Run TC4 in Deadlock Detection Page" in b.label][0]
    btn4.click().run()

    assert at.session_state["nav_page"] == "5. Deadlock Detection & RAG"
    assert at.sidebar.radio[0].value == "5. Deadlock Detection & RAG"
    assert at.session_state["det_available"] == [0, 0]


