"""OS Deadlock Analysis & Resource Allocation Dashboard.

Interactive web application built with Streamlit for MIT Academy of Engineering
(Computer Department - OS Lab Activity 2). Demonstrates Banker's Algorithm, deadlock
avoidance, multi-instance detection, Resource Allocation Graph analysis, hierarchical
prevention, victim recovery, and verified test scenarios (TC1-TC6).

Project Team:
- Parth Wankhade
- Aryan Agarwal
- Vikas Choudhary
- Sanket Kongare
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from copy import deepcopy
from typing import List, Dict, Any, Tuple

from src.validation import (
    validate_system_state,
    calculate_need_matrix,
    validate_dimensions,
    ValidationError,
)
from src.bankers_algorithm import run_safety_algorithm
from src.resource_requests import request_resources, RequestDecision
from src.deadlock_detection import (
    detect_deadlock_multi_instance,
    analyze_resource_allocation_graph,
)
from src.deadlock_prevention import (
    HierarchicalOrderingPolicy,
    HoldAndWaitPreventionPolicy,
    COFFMAN_CONDITIONS,
)
from src.deadlock_recovery import (
    suggest_victim_processes,
    recover_by_process_termination,
)
from src.test_scenarios import (
    run_all_test_scenarios,
    run_tc1_safe_state,
    run_tc2_request_exceeds_available,
    run_tc3_request_produces_unsafe_state,
    run_tc4_deadlock_detection,
    run_tc5_prevention_policy,
    run_tc6_boundary_and_invalid_inputs,
    SAFE_SYSTEM_CONFIG,
    DEADLOCKED_SYSTEM_CONFIG,
    REQUEST_SIMULATION_TEST_CASES,
    get_request_simulation_test_cases,
    load_request_test_case,
    execute_loaded_request_test_case,
)
from src.reporting import (
    export_test_results_to_csv,
    export_test_results_to_markdown,
    export_ai_usage_record_to_csv,
    export_ai_usage_record_to_markdown,
)


# -------------------------------------------------------------------------
# Page Configuration and Global Styling
# -------------------------------------------------------------------------
st.set_page_config(
    page_title="OS Deadlock Analysis & Resource Allocation",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for polished academic appearance in light theme
st.markdown("""
<style>
    /* Global light theme container styles */
    .stApp {
        background-color: #FFFFFF;
        color: #111827;
    }
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .badge-safe {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        display: inline-block;
        border: 1px solid #86EFAC;
    }
    .badge-unsafe {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        display: inline-block;
        border: 1px solid #FCA5A5;
    }
    .badge-wait {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 12px;
        border-radius: 9999px;
        font-weight: 600;
        display: inline-block;
        border: 1px solid #FCD34D;
    }
    .academic-note {
        background-color: #F0FDF4;
        border-left: 4px solid #16A34A;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
        color: #14532D;
    }
    .academic-warning {
        background-color: #FEF2F2;
        border-left: 4px solid #DC2626;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
        color: #7F1D1D;
    }
    .academic-info {
        background-color: #F0F9FF;
        border-left: 4px solid #0284C7;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
        color: #0C4A6E;
    }
    .academic-wait {
        background-color: #FFFBEB;
        border-left: 4px solid #D97706;
        padding: 12px 16px;
        border-radius: 4px;
        margin: 12px 0;
        color: #78350F;
    }
    code {
        color: #1E293B !important;
        background-color: #F1F5F9 !important;
        padding: 2px 6px !important;
        border-radius: 4px !important;
        border: 1px solid #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------------------
# Session State Initialization
# -------------------------------------------------------------------------
def init_session_state():
    """Ensure all required session state variables exist with safe defaults."""
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = True
        st.session_state["num_processes"] = 5
        st.session_state["num_resources"] = 3
        st.session_state["resource_names"] = ["A", "B", "C"]
        st.session_state["allocation"] = deepcopy(SAFE_SYSTEM_CONFIG["allocation"])
        st.session_state["maximum"] = deepcopy(SAFE_SYSTEM_CONFIG["maximum"])
        st.session_state["available"] = list(SAFE_SYSTEM_CONFIG["available"])
        st.session_state["total"] = list(SAFE_SYSTEM_CONFIG["total"])
        st.session_state["preset_name"] = "Preset 1: Standard Safe State (Silberschatz)"
        st.session_state["is_custom_data"] = False

        # Detection page session state
        st.session_state["det_allocation"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["allocation"])
        st.session_state["det_request"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["request"])
        st.session_state["det_available"] = list(DEADLOCKED_SYSTEM_CONFIG["available"])
        st.session_state["det_resource_names"] = ["A", "B"]

        # Recovery page session state
        st.session_state["rec_allocation"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["allocation"])
        st.session_state["rec_request"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["request"])
        st.session_state["rec_available"] = list(DEADLOCKED_SYSTEM_CONFIG["available"])

        # AI Usage record rows
        st.session_state["ai_usage_rows"] = [
            {
                "AI Tool Used": "Antigravity IDE (Gemini)",
                "Purpose": "Dashboard UI design, modular algorithm architecture, and testing scaffold",
                "Output Generated": "Python modules (validation, bankers, requests, detection, prevention, recovery) & Streamlit UI",
                "Student Verification": "Verified step-by-step against Silberschatz Operating System Concepts (Chapter 8)",
            },
            {
                "AI Tool Used": "Antigravity IDE (Gemini)",
                "Purpose": "Analytical test cases (TC1-TC6) design and boundary conditions",
                "Output Generated": "Pytest automated suite and deterministic test vectors",
                "Student Verification": "Manually calculated Work/Need traces on paper and verified PASS/FAIL results",
            },
            {
                "AI Tool Used": "None / Manual Work",
                "Purpose": "Theoretical derivation and viva-voce technical defense",
                "Output Generated": "Independent verification notes and viva answers",
                "Student Verification": "Prepared and validated by student for academic evaluation",
            },
        ]


init_session_state()


# -------------------------------------------------------------------------
# Sidebar Navigation
# -------------------------------------------------------------------------
st.sidebar.markdown("### 🖥️ OS Deadlock Dashboard")
st.sidebar.markdown("**MIT Academy of Engineering**")
st.sidebar.caption("Computer Department | Activity 2")
st.sidebar.markdown("---")
st.sidebar.markdown("**👥 Team Members:**")
st.sidebar.markdown(
    "• **Parth Wankhade**  \n"
    "• **Aryan Agarwal**  \n"
    "• **Vikas Choudhary**  \n"
    "• **Sanket Kongare**"
)
st.sidebar.markdown("---")

pages = [
    "1. Overview Dashboard",
    "2. Resource Allocation Matrix",
    "3. Banker's Algorithm (Safety Check)",
    "4. Resource Request Simulation",
    "5. Deadlock Detection & RAG",
    "6. Deadlock Prevention",
    "7. Deadlock Recovery",
    "8. Test Lab & Analytical Results",
    "9. AI Usage Record & Submission",
]

# Support programmatic page navigation across sections
if "nav_page" not in st.session_state:
    st.session_state["nav_page"] = pages[0]

if "target_nav_page" in st.session_state:
    target = st.session_state.pop("target_nav_page")
    st.session_state["nav_page"] = target
    st.session_state["sidebar_navigation_radio"] = target

if "sidebar_navigation_radio" not in st.session_state or st.session_state["sidebar_navigation_radio"] not in pages:
    st.session_state["sidebar_navigation_radio"] = st.session_state["nav_page"]

selected_page = st.sidebar.radio(
    "Navigate Sections",
    options=pages,
    key="sidebar_navigation_radio",
)
st.session_state["nav_page"] = selected_page

st.sidebar.markdown("---")
st.sidebar.markdown("#### System Configuration Snapshot")
st.sidebar.text(f"Processes: {st.session_state['num_processes']} (P0-P{st.session_state['num_processes']-1})")
st.sidebar.text(f"Resources: {st.session_state['num_resources']} ({', '.join(st.session_state['resource_names'])})")
st.sidebar.text(f"Available: {st.session_state['available']}")
if st.session_state["is_custom_data"]:
    st.sidebar.caption("✏️ User Custom Configuration Active")
else:
    st.sidebar.caption(f"📌 {st.session_state['preset_name']}")


# -------------------------------------------------------------------------
# PAGE 1: Overview Dashboard
# -------------------------------------------------------------------------
if selected_page == "1. Overview Dashboard":
    st.markdown('<div class="main-title">OS Deadlock Analysis & Resource Allocation Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">A complete, mathematically verified educational platform for Concurrency Control and Resource Allocation</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #F8FAFC; border-left: 4px solid #2563EB; padding: 12px 18px; border-radius: 6px; margin-bottom: 16px;">
        <span style="font-weight: 600; color: #1E293B;">🏛️ MIT Academy of Engineering — Computer Department</span><br>
        <span style="color: #475569;"><strong>Project Team:</strong> Parth Wankhade &bull; Aryan Agarwal &bull; Vikas Choudhary &bull; Sanket Kongare</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="academic-note">
        <strong>⚠️ Crucial Operating Systems Principle:</strong><br>
        <strong>Banker's Algorithm is a Deadlock AVOIDANCE algorithm, NOT an existing-deadlock detection algorithm.</strong><br>
        • A <strong>Safe State</strong> guarantees that at least one execution sequence exists where all processes can finish without deadlock.<br>
        • An <strong>Unsafe State</strong> means the OS <em>cannot guarantee</em> avoiding a deadlock under maximum possible future demands. It does <strong>NOT</strong> mean the system is currently deadlocked! An unsafe state may or may not lead to deadlock depending on future runtime requests.<br>
        • <strong>Deadlock</strong> is an active condition where two or more processes are permanently blocked waiting for resources held by each other.
    </div>
    """, unsafe_allow_html=True)

    # Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Configured Processes", f"{st.session_state['num_processes']} processes", f"P0 - P{st.session_state['num_processes']-1}")
    with col2:
        st.metric("Resource Types", f"{st.session_state['num_resources']} types", ", ".join(st.session_state["resource_names"]))
    with col3:
        st.metric("Current Available", str(st.session_state["available"]), "Unallocated units")
    with col4:
        # Dynamically compute safety of current state
        try:
            safety_check = run_safety_algorithm(
                st.session_state["allocation"],
                st.session_state["maximum"],
                st.session_state["available"],
            )
            if safety_check["is_safe"]:
                st.markdown("**System Safety Status:**")
                st.markdown('<span class="badge-safe">SAFE STATE (Avoidance Guarantee)</span>', unsafe_allow_html=True)
            else:
                st.markdown("**System Safety Status:**")
                st.markdown('<span class="badge-unsafe">UNSAFE STATE (Caution)</span>', unsafe_allow_html=True)
        except Exception as e:
            st.warning("Needs Valid Matrix Setup")

    st.markdown("---")
    st.markdown("### 📚 Conceptual Foundation: The 4 System States")

    state_comp = pd.DataFrame([
        {
            "System State": "Safe State",
            "Definition": "A safe sequence <P1, P2, ... Pn> exists such that each Pi's max need can be satisfied by current Available plus resources released by previous processes.",
            "Deadlock Present?": "❌ Absolutely No",
            "OS Strategy": "Deadlock Avoidance (Banker's Algorithm grants requests only if tentative state remains safe).",
        },
        {
            "System State": "Unsafe State",
            "Definition": "No complete safe sequence can be guaranteed under worst-case maximum claims. Some processes may get starved if all claim maximum needs simultaneously.",
            "Deadlock Present?": "⚠️ Not necessarily (potential deadlock in future).",
            "OS Strategy": "Reject or defer the transition into this state.",
        },
        {
            "System State": "Deadlocked State",
            "Definition": "Two or more processes are currently blocked in a circular wait, each holding a resource needed by another, with no process capable of proceeding.",
            "Deadlock Present?": "🚨 Yes, Confirmed Active Deadlock.",
            "OS Strategy": "Deadlock Detection & Recovery (abort processes or preempt resources).",
        },
        {
            "System State": "Invalid Input",
            "Definition": "Inputs violate physical or logical constraints (e.g. Allocation > Maximum, negative values, dimension mismatch).",
            "Deadlock Present?": "N/A (Logical Error)",
            "OS Strategy": "Strict input validation; immediate rejection with actionable error messages.",
        },
    ])
    st.dataframe(state_comp, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("### 🔒 The Four Coffman Conditions (Necessary for Deadlock)")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("**1. Mutual Exclusion**")
        st.caption("At least one resource must be held in non-shareable mode.")
    with c2:
        st.markdown("**2. Hold and Wait**")
        st.caption("A process holds at least one resource while waiting for more.")
    with c3:
        st.markdown("**3. No Preemption**")
        st.caption("Resources cannot be forcibly confiscated; only released voluntarily.")
    with c4:
        st.markdown("**4. Circular Wait**")
        st.caption("A closed cycle of processes exists, each waiting for the next.")

    st.markdown("---")
    st.markdown("### 🧭 Application Guide & Navigation")
    st.markdown("""
    Use the sidebar menu to explore all experimental facets:
    - **Page 2: Resource Allocation Matrix:** Configure matrices, select presets, auto-compute Need, validate integrity.
    - **Page 3: Banker's Algorithm (Safety Check):** Run safety algorithm, inspect Work vectors, view complete safe sequence.
    - **Page 4: Resource Request Simulation:** Simulate dynamic requests, distinguish waiting vs unsafe denial, verify state immutability.
    - **Page 5: Deadlock Detection & RAG:** Multi-instance detection algorithm and Resource Allocation Graph cycle analysis.
    - **Page 6: Deadlock Prevention:** Enforce Hierarchical Resource Ordering to break Circular Wait.
    - **Page 7: Deadlock Recovery:** Terminate victim processes, reclaim resources, and verify resolution.
    - **Page 8: Test Lab & Analytical Results:** Run and inspect TC1 through TC6; download CSV & Markdown reports.
    - **Page 9: AI Usage Record & Submission:** Review integrity declarations and viva-voce preparation questions.
    """)


# -------------------------------------------------------------------------
# PAGE 2: Resource Allocation Matrix
# -------------------------------------------------------------------------
elif selected_page == "2. Resource Allocation Matrix":
    st.markdown('<div class="main-title">Resource Allocation & Demand Configuration</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Configure process/resource dimensions, Allocation, Maximum, Available, and verify Need = Max - Alloc</div>', unsafe_allow_html=True)

    # Preset Selection
    st.markdown("#### 📦 Load Standard Academic Presets")
    preset_cols = st.columns([3, 1, 1])
    with preset_cols[0]:
        preset_choice = st.selectbox(
            "Select Preset Configuration",
            [
                "Preset 1: Standard Safe State (Silberschatz)",
                "Preset 2: Unsafe State Example",
                "Preset 3: TC2 Scenario (Request Exceeds Available)",
                "Preset 4: TC3 Scenario (Avoidance Denial - Unsafe)",
                "Preset 5: Deadlock Detection Multi-Instance",
            ],
            index=0,
        )
    with preset_cols[1]:
        st.write("")
        st.write("")
        if st.button("Load Selected Preset", use_container_width=True):
            if "Preset 1" in preset_choice:
                st.session_state["num_processes"] = 5
                st.session_state["num_resources"] = 3
                st.session_state["resource_names"] = ["A", "B", "C"]
                st.session_state["allocation"] = deepcopy(SAFE_SYSTEM_CONFIG["allocation"])
                st.session_state["maximum"] = deepcopy(SAFE_SYSTEM_CONFIG["maximum"])
                st.session_state["available"] = list(SAFE_SYSTEM_CONFIG["available"])
                st.session_state["total"] = list(SAFE_SYSTEM_CONFIG["total"])
                st.session_state["preset_name"] = preset_choice
                st.session_state["is_custom_data"] = False
            elif "Preset 2" in preset_choice:
                st.session_state["num_processes"] = 3
                st.session_state["num_resources"] = 2
                st.session_state["resource_names"] = ["A", "B"]
                st.session_state["allocation"] = [[2, 1], [1, 2], [1, 1]]
                st.session_state["maximum"] = [[5, 3], [4, 4], [3, 3]]
                st.session_state["available"] = [0, 1]
                st.session_state["total"] = [4, 5]
                st.session_state["preset_name"] = preset_choice
                st.session_state["is_custom_data"] = False
            elif "Preset 3" in preset_choice:
                st.session_state["num_processes"] = 5
                st.session_state["num_resources"] = 3
                st.session_state["resource_names"] = ["A", "B", "C"]
                st.session_state["allocation"] = deepcopy(SAFE_SYSTEM_CONFIG["allocation"])
                st.session_state["maximum"] = deepcopy(SAFE_SYSTEM_CONFIG["maximum"])
                st.session_state["available"] = list(SAFE_SYSTEM_CONFIG["available"])
                st.session_state["total"] = list(SAFE_SYSTEM_CONFIG["total"])
                st.session_state["preset_name"] = preset_choice
                st.session_state["is_custom_data"] = False
            elif "Preset 4" in preset_choice:
                st.session_state["num_processes"] = 2
                st.session_state["num_resources"] = 2
                st.session_state["resource_names"] = ["A", "B"]
                st.session_state["allocation"] = [[1, 1], [1, 0]]
                st.session_state["maximum"] = [[2, 2], [3, 1]]
                st.session_state["available"] = [1, 1]
                st.session_state["total"] = [3, 2]
                st.session_state["preset_name"] = preset_choice
                st.session_state["is_custom_data"] = False
            elif "Preset 5" in preset_choice:
                st.session_state["num_processes"] = 3
                st.session_state["num_resources"] = 2
                st.session_state["resource_names"] = ["A", "B"]
                st.session_state["allocation"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["allocation"])
                st.session_state["maximum"] = [[2, 1], [1, 2], [2, 2]]
                st.session_state["available"] = list(DEADLOCKED_SYSTEM_CONFIG["available"])
                st.session_state["total"] = [2, 2]
                st.session_state["preset_name"] = preset_choice
                st.session_state["is_custom_data"] = False
            st.rerun()

    with preset_cols[2]:
        st.write("")
        st.write("")
        if st.button("Reset to Default", use_container_width=True):
            st.session_state["num_processes"] = 5
            st.session_state["num_resources"] = 3
            st.session_state["resource_names"] = ["A", "B", "C"]
            st.session_state["allocation"] = deepcopy(SAFE_SYSTEM_CONFIG["allocation"])
            st.session_state["maximum"] = deepcopy(SAFE_SYSTEM_CONFIG["maximum"])
            st.session_state["available"] = list(SAFE_SYSTEM_CONFIG["available"])
            st.session_state["total"] = list(SAFE_SYSTEM_CONFIG["total"])
            st.session_state["preset_name"] = "Preset 1: Standard Safe State (Silberschatz)"
            st.session_state["is_custom_data"] = False
            st.rerun()

    st.markdown("---")
    st.markdown("#### ⚙️ Dimensions & System Vectors")
    dim_col1, dim_col2, dim_col3 = st.columns([1, 1, 2])

    with dim_col1:
        new_n = st.number_input("Number of Processes (n)", min_value=1, max_value=8, value=st.session_state["num_processes"], step=1)
    with dim_col2:
        new_m = st.number_input("Number of Resource Types (m)", min_value=1, max_value=6, value=st.session_state["num_resources"], step=1)

    # Adjust matrices if user altered dimensions
    if new_n != st.session_state["num_processes"] or new_m != st.session_state["num_resources"]:
        res_names = [chr(65 + j) for j in range(new_m)]
        new_alloc = []
        new_max = []
        for i in range(new_n):
            alloc_row = []
            max_row = []
            for j in range(new_m):
                old_val_a = st.session_state["allocation"][i][j] if i < len(st.session_state["allocation"]) and j < len(st.session_state["allocation"][0]) else 0
                old_val_m = st.session_state["maximum"][i][j] if i < len(st.session_state["maximum"]) and j < len(st.session_state["maximum"][0]) else 1
                alloc_row.append(old_val_a)
                max_row.append(max(old_val_m, old_val_a))
            new_alloc.append(alloc_row)
            new_max.append(max_row)

        new_avail = [st.session_state["available"][j] if j < len(st.session_state["available"]) else 2 for j in range(new_m)]
        st.session_state["num_processes"] = new_n
        st.session_state["num_resources"] = new_m
        st.session_state["resource_names"] = res_names
        st.session_state["allocation"] = new_alloc
        st.session_state["maximum"] = new_max
        st.session_state["available"] = new_avail
        st.session_state["is_custom_data"] = True
        st.rerun()

    n = st.session_state["num_processes"]
    m = st.session_state["num_resources"]
    proc_labels = [f"P{i}" for i in range(n)]
    res_labels = st.session_state["resource_names"]

    # Available vector editor
    with dim_col3:
        st.markdown("**Available Resources Vector**")
        avail_df = pd.DataFrame([st.session_state["available"]], columns=res_labels, index=["Available"])
        edited_avail_df = st.data_editor(avail_df, key="avail_editor", use_container_width=True)
        new_avail_list = [int(edited_avail_df.iloc[0][c]) for c in res_labels]
        if new_avail_list != st.session_state["available"]:
            st.session_state["available"] = new_avail_list
            st.session_state["is_custom_data"] = True

    st.markdown("---")
    st.markdown("#### 📝 Allocation & Maximum Matrices (Editable)")
    mat_col1, mat_col2 = st.columns(2)

    with mat_col1:
        st.markdown("**Allocation Matrix [Current Held Resources]**")
        alloc_df = pd.DataFrame(st.session_state["allocation"], index=proc_labels, columns=res_labels)
        edited_alloc_df = st.data_editor(alloc_df, key="alloc_editor", use_container_width=True)
        new_alloc = [[int(edited_alloc_df.iloc[i][c]) for c in res_labels] for i in range(n)]
        if new_alloc != st.session_state["allocation"]:
            st.session_state["allocation"] = new_alloc
            st.session_state["is_custom_data"] = True

    with mat_col2:
        st.markdown("**Maximum Matrix [Declared Peak Claims]**")
        max_df = pd.DataFrame(st.session_state["maximum"], index=proc_labels, columns=res_labels)
        edited_max_df = st.data_editor(max_df, key="max_editor", use_container_width=True)
        new_max = [[int(edited_max_df.iloc[i][c]) for c in res_labels] for i in range(n)]
        if new_max != st.session_state["maximum"]:
            st.session_state["maximum"] = new_max
            st.session_state["is_custom_data"] = True

    # Validation check on current state
    is_valid, val_msg, val_details = validate_system_state(
        st.session_state["allocation"],
        st.session_state["maximum"],
        st.session_state["available"],
    )

    if not is_valid:
        st.markdown(f"""
        <div class="academic-warning">
            <strong>❌ Input Validation Error:</strong><br>
            {val_msg}<br>
            <em>Please adjust matrix values above. Note: Allocation cannot exceed Maximum for any process/resource pair.</em>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="academic-note">
            <strong>✅ System State Validated:</strong> Dimensions, non-negative integer types, and Allocation ≤ Maximum constraints satisfied.
        </div>
        """, unsafe_allow_html=True)

        # Calculate and Display Need Matrix
        need_matrix = calculate_need_matrix(st.session_state["allocation"], st.session_state["maximum"])
        need_df = pd.DataFrame(need_matrix, index=proc_labels, columns=res_labels)

        st.markdown("#### 🧮 Calculated Need Matrix [Need = Maximum - Allocation]")
        st.caption("Represents the maximum remaining resources each process may claim before terminating.")
        st.dataframe(need_df, use_container_width=True)

        # Total System Resources Consistency Check
        calc_total = [
            sum(st.session_state["allocation"][i][j] for i in range(n)) + st.session_state["available"][j]
            for j in range(m)
        ]
        tot_df = pd.DataFrame(
            [
                [sum(st.session_state["allocation"][i][j] for i in range(n)) for j in range(m)],
                st.session_state["available"],
                calc_total,
            ],
            index=["Total Allocated (Sum)", "Currently Available", "Calculated System Total"],
            columns=res_labels,
        )
        st.markdown("#### ⚖️ Resource Accounting Balance (Conservation Law)")
        st.dataframe(tot_df, use_container_width=True)


# -------------------------------------------------------------------------
# PAGE 3: Banker's Algorithm (Safety Check)
# -------------------------------------------------------------------------
elif selected_page == "3. Banker's Algorithm (Safety Check)":
    st.markdown('<div class="main-title">Banker’s Algorithm — Safety Algorithm</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Determines if the system is in a Safe State by simulating process execution and resource release</div>', unsafe_allow_html=True)

    alloc = st.session_state["allocation"]
    max_mat = st.session_state["maximum"]
    avail = st.session_state["available"]
    res_names = st.session_state["resource_names"]
    proc_names = [f"P{i}" for i in range(len(alloc))]

    is_valid, err_msg, _ = validate_system_state(alloc, max_mat, avail)
    if not is_valid:
        st.error(f"Cannot run Banker's Safety Algorithm: {err_msg}")
    else:
        need = calculate_need_matrix(alloc, max_mat)

        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("##### Current System Matrices")
            display_df = pd.DataFrame({
                "Process": proc_names,
                "Allocation": [str(alloc[i]) for i in range(len(alloc))],
                "Maximum": [str(max_mat[i]) for i in range(len(max_mat))],
                "Need (Max - Alloc)": [str(need[i]) for i in range(len(need))],
            })
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        with c2:
            st.markdown("##### Vectors")
            st.info(f"**Available Vector:** {avail}\n\n**Resources:** {', '.join(res_names)}")

        st.markdown("---")
        if st.button("🚀 Execute Banker's Safety Check", type="primary", use_container_width=True):
            safety_res = run_safety_algorithm(alloc, max_mat, avail)

            if safety_res["is_safe"]:
                st.markdown(f"""
                <div class="academic-note" style="font-size: 1.15rem;">
                    <strong>✅ SYSTEM IS IN A SAFE STATE</strong><br>
                    <strong>Safe Sequence Found:</strong> <code style="font-size: 1.2rem; font-weight: bold;">{safety_res['safe_sequence_str']}</code><br>
                    {safety_res['explanation']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="academic-warning" style="font-size: 1.15rem;">
                    <strong>❌ SYSTEM IS IN AN UNSAFE STATE</strong><br>
                    <strong>Safe Sequence:</strong> None<br>
                    {safety_res['explanation']}
                </div>
                """, unsafe_allow_html=True)

            # Step-by-Step Trace Table
            st.markdown("#### 📋 Step-by-Step Execution Trace")
            if safety_res["trace"]:
                trace_rows = []
                for tr in safety_res["trace"]:
                    trace_rows.append({
                        "Step": tr["step"],
                        "Process": tr["process_name"],
                        "Work Vector Before": str(tr["work_before"]),
                        "Need Vector": str(tr["need"]),
                        "Condition Check": f"Need ≤ Work ({all(tr['need'][j] <= tr['work_before'][j] for j in range(len(avail)))})",
                        "Allocation Released": str(tr["allocation_released"]),
                        "New Work Vector": str(tr["work_after"]),
                        "Finish Vector": str(tr["finish_state"]),
                    })
                st.dataframe(pd.DataFrame(trace_rows), use_container_width=True, hide_index=True)
            else:
                st.warning("No process could begin execution with the initial Available vector.")

            # Educational Takeaway
            st.markdown("---")
            st.markdown("""
            **Theoretical Insights:**
            - **Complexity:** Time complexity is $\\mathcal{O}(m \\times n^2)$ where $n$ is processes and $m$ is resource types.
            - **Determinism:** If multiple processes satisfy Need ≤ Work at the same step, multiple valid safe sequences may exist. The safety property holds regardless of which candidate is chosen.
            - **Avoidance Guarantee:** As long as the system remains in a safe state, the OS can ensure deadlock will never occur.
            """)


# -------------------------------------------------------------------------
# PAGE 4: Resource Request Simulation (Deadlock Avoidance)
# -------------------------------------------------------------------------
elif selected_page == "4. Resource Request Simulation":
    st.markdown('<div class="main-title">Resource Request Simulation — Deadlock Avoidance</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Simulate process resource requests; distinguish waiting, unsafe rejection, and granted states</div>', unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # Interactive Test-Case Preset Selector (Direct Lab Integration)
    # ---------------------------------------------------------------------
    st.markdown("### 🧪 Assignment Test Case Selector")
    st.caption("Directly load and evaluate verified assignment test scenarios into the simulation controls, or test custom manual requests below.")

    tc_options = [
        "TC1 — Safe State / Safe Request (Granted)",
        "TC2 — Request Exceeds Available / Deferred (Waiting)",
        "TC3 — Unsafe Tentative State / Denied with Rollback",
        "TC4 — Deadlock Detection Scenario (Outstanding Requests)",
        "TC6.5 — Claim Violation / Request Exceeds Need (Invalid)",
    ]

    selected_tc_label = st.selectbox(
        "Select Assignment Test Scenario to Load",
        tc_options,
        index=0,
        key="tc_selector_dropdown",
    )

    tc_id = selected_tc_label.split(" — ")[0]
    tc_data = load_request_test_case(tc_id)

    # Display Test Case Summary Card
    st.markdown(f"""
    <div class="academic-info">
        <strong>📋 Scenario: {tc_data['title']}</strong><br>
        <strong>Test ID:</strong> <code>{tc_data['id']}</code> &nbsp;|&nbsp; 
        <strong>Scenario Type:</strong> <code>{tc_data['type'].upper()}</code> &nbsp;|&nbsp; 
        <strong>Expected Decision:</strong> <code>{tc_data.get('expected_decision', 'N/A')}</code><br>
        <strong>Description:</strong> {tc_data['description']}
    </div>
    """, unsafe_allow_html=True)

    if tc_data["type"] == "request":
        tc_col1, tc_col2, tc_col3 = st.columns([1.5, 1.8, 2.5])
        with tc_col1:
            load_tc_btn = st.button("📥 Load Test Case Inputs", use_container_width=True, help="Populate matrices, process, and request vector with this test case's parameters")
        with tc_col2:
            load_eval_btn = st.button("⚡ Load & Evaluate Immediately", type="primary", use_container_width=True, help="Load inputs and immediately evaluate Banker's avoidance check")
        with tc_col3:
            st.caption(f"🎯 Target: Process P{tc_data['process_id']} requests {tc_data['request']} | Config: {tc_data['num_processes']} Procs, {tc_data['num_resources']} Resources")

        if load_tc_btn or load_eval_btn:
            st.session_state["num_processes"] = tc_data["num_processes"]
            st.session_state["num_resources"] = tc_data["num_resources"]
            st.session_state["resource_names"] = list(tc_data["resource_names"])
            st.session_state["allocation"] = deepcopy(tc_data["allocation"])
            st.session_state["maximum"] = deepcopy(tc_data["maximum"])
            st.session_state["available"] = list(tc_data["available"])
            st.session_state["total"] = list(tc_data.get("total", []))
            st.session_state["preset_name"] = f"Loaded {tc_data['id']}: {tc_data['title']}"
            st.session_state["is_custom_data"] = False

            # Set selected process and request quantities synchronously in widget keys
            proc_id = int(tc_data["process_id"])
            st.session_state["sim_proc_dropdown"] = proc_id
            st.session_state["sim_selected_proc"] = proc_id
            st.session_state["sim_req_vals"] = [int(v) for v in tc_data["request"]]

            # Clean up stale request input keys if resource count changed
            for k in range(tc_data["num_resources"], 10):
                st.session_state.pop(f"req_input_{k}", None)

            for j, val in enumerate(tc_data["request"]):
                st.session_state[f"req_input_{j}"] = int(val)

            st.session_state["loaded_tc_meta"] = {
                "id": tc_data["id"],
                "title": tc_data["title"],
                "process_id": proc_id,
                "request": [int(v) for v in tc_data["request"]],
                "expected_decision": tc_data["expected_decision"],
                "expected_label": tc_data["expected_label"],
            }
            if load_eval_btn:
                st.session_state["auto_eval_trigger"] = True
            st.rerun()

    else:
        # TC4: Deadlock Detection Scenario
        st.markdown("""
        <div class="academic-warning" style="margin-top: 10px;">
            <strong>⚠️ Conceptual Distinction — Avoidance vs. Detection:</strong><br>
            <strong>TC4</strong> is a <strong>Deadlock Detection</strong> scenario ($Available=[0, 0]$ with circular active requests among $P_0, P_1, P_2$).<br>
            It evaluates <em>existing blocked requests</em> in an active deadlock, rather than a single process requesting additional resources under Banker's avoidance.<br>
            To examine TC4 in its proper theoretical environment (with matrix reduction and Resource Allocation Graph cycle analysis), click the button below:
        </div>
        """, unsafe_allow_html=True)

        tc4_col1, tc4_col2 = st.columns([2, 3])
        with tc4_col1:
            if st.button("➡️ Run TC4 in Deadlock Detection Page", type="primary", use_container_width=True):
                st.session_state["det_allocation"] = deepcopy(tc_data["allocation"])
                st.session_state["det_request"] = deepcopy(tc_data["request_matrix"])
                st.session_state["det_available"] = list(tc_data["available"])
                st.session_state["det_resource_names"] = list(tc_data["resource_names"])
                st.session_state["target_nav_page"] = "5. Deadlock Detection & RAG"
                st.rerun()
        with tc4_col2:
            st.caption("Automatically populates the Deadlock Detection matrices with TC4 and navigates to Page 5.")

    st.markdown("---")

    alloc = st.session_state["allocation"]
    max_mat = st.session_state["maximum"]
    avail = st.session_state["available"]
    n = len(alloc)
    m = len(avail)
    res_names = st.session_state["resource_names"]
    proc_names = [f"P{i}" for i in range(n)]

    is_valid, err_msg, _ = validate_system_state(alloc, max_mat, avail)
    if not is_valid:
        st.error(f"Cannot simulate requests: {err_msg}")
    else:
        need = calculate_need_matrix(alloc, max_mat)

        # Active System Matrix Summary Expander
        with st.expander("📊 View Active System Matrices (Allocation, Maximum, Need, Available)", expanded=False):
            exp_c1, exp_c2 = st.columns([3, 1])
            with exp_c1:
                matrix_summary_df = pd.DataFrame({
                    "Process": proc_names,
                    "Allocation": [str(alloc[i]) for i in range(n)],
                    "Maximum": [str(max_mat[i]) for i in range(n)],
                    "Need (Max - Alloc)": [str(need[i]) for i in range(n)],
                })
                st.dataframe(matrix_summary_df, use_container_width=True, hide_index=True)
            with exp_c2:
                st.info(f"**Available:** {avail}\n\n**Resources:** {', '.join(res_names)}")

        st.markdown("#### 📥 Configure & Submit Resource Request")
        req_c1, req_c2 = st.columns([1, 2])

        with req_c1:
            # Ensure sim_proc_dropdown exists and is valid for current n
            if "sim_proc_dropdown" not in st.session_state or st.session_state["sim_proc_dropdown"] not in range(n):
                default_proc = st.session_state.get("sim_selected_proc", 0)
                if default_proc not in range(n):
                    default_proc = 0
                st.session_state["sim_proc_dropdown"] = default_proc

            sel_proc = st.selectbox(
                "Requesting Process",
                options=list(range(n)),
                format_func=lambda x: f"P{x}",
                key="sim_proc_dropdown",
            )
            st.session_state["sim_selected_proc"] = sel_proc
            st.caption(f"Process P{sel_proc} current held: {alloc[sel_proc]}")
            st.caption(f"Process P{sel_proc} remaining need: {need[sel_proc]}")
            st.caption(f"Currently available in system: {avail}")

        with req_c2:
            st.markdown("**Enter Requested Quantities**")
            req_cols = st.columns(m)
            req_vals = []
            saved_req = st.session_state.get("sim_req_vals", [0] * m)
            if len(saved_req) != m:
                saved_req = [0] * m

            for j in range(m):
                with req_cols[j]:
                    if f"req_input_{j}" not in st.session_state:
                        st.session_state[f"req_input_{j}"] = int(saved_req[j])
                    val = st.number_input(
                        f"Resource {res_names[j]}",
                        min_value=0,
                        max_value=25,
                        key=f"req_input_{j}",
                    )
                    req_vals.append(int(val))
            st.session_state["sim_req_vals"] = req_vals

        st.markdown(f"**Submitted Request:** `P{sel_proc} requests {req_vals}`")

        col_btn1, col_btn2 = st.columns([1, 1])
        auto_trigger = st.session_state.pop("auto_eval_trigger", False)
        with col_btn1:
            eval_clicked = st.button("🔍 Evaluate Request (Banker's Avoidance)", type="primary", use_container_width=True) or auto_trigger
        with col_btn2:
            if st.button("🔄 Reset Matrices to Saved Safe Baseline", use_container_width=True):
                st.session_state["num_processes"] = 5
                st.session_state["num_resources"] = 3
                st.session_state["resource_names"] = ["A", "B", "C"]
                st.session_state["allocation"] = deepcopy(SAFE_SYSTEM_CONFIG["allocation"])
                st.session_state["maximum"] = deepcopy(SAFE_SYSTEM_CONFIG["maximum"])
                st.session_state["available"] = list(SAFE_SYSTEM_CONFIG["available"])
                st.session_state["total"] = list(SAFE_SYSTEM_CONFIG["total"])
                st.session_state["preset_name"] = "Preset 1: Standard Safe State (Silberschatz)"
                st.session_state["is_custom_data"] = False
                st.session_state["sim_proc_dropdown"] = 0
                st.session_state["sim_selected_proc"] = 0
                st.session_state["sim_req_vals"] = [0, 0, 0]
                for j in range(3):
                    st.session_state[f"req_input_{j}"] = 0
                for k in range(3, 10):
                    st.session_state.pop(f"req_input_{k}", None)
                st.session_state.pop("loaded_tc_meta", None)
                st.session_state.pop("auto_eval_trigger", None)
                st.rerun()

        if eval_clicked:
            result = request_resources(sel_proc, req_vals, alloc, max_mat, avail)

            # Display Decision Badge
            st.markdown("---")
            st.markdown("### 🎯 Decision & OS Evaluation")

            # Benchmark check if an assignment scenario was loaded
            if "loaded_tc_meta" in st.session_state:
                meta = st.session_state["loaded_tc_meta"]
                is_match = (result["decision"] == meta["expected_decision"])
                status_icon = "✅" if is_match else "⚠️"
                status_text = "PASS — EXPECTATION VERIFIED" if is_match else "RESULT DEVIATES FROM BENCHMARK"
                badge_style = "badge-safe" if is_match else "badge-unsafe"
                card_style = "academic-note" if is_match else "academic-warning"

                st.markdown(f"""
                <div class="{card_style}" style="margin-bottom: 15px;">
                    <strong>🧪 Scenario Benchmark Verification:</strong> <code>{meta['id']} — {meta['title']}</code><br>
                    <strong>Requester:</strong> <code>Process P{sel_proc}</code> &nbsp;|&nbsp; 
                    <strong>Request Vector:</strong> <code>{req_vals}</code><br>
                    <strong>Expected Decision:</strong> <code>{meta['expected_decision']}</code> &nbsp;|&nbsp; 
                    <strong>Actual Output:</strong> <code>{result['decision']}</code> &nbsp;|&nbsp; 
                    <span class="{badge_style}">{status_icon} {status_text}</span>
                </div>
                """, unsafe_allow_html=True)

            decision = result["decision"]
            if decision == RequestDecision.GRANTED_SAFE:
                st.markdown(f"""
                <div class="academic-note" style="font-size: 1.15rem;">
                    <span class="badge-safe">STATUS: GRANTED — SAFE STATE PRESERVED</span><br><br>
                    {result['explanation']}
                </div>
                """, unsafe_allow_html=True)

                # Show tentative sequence
                if result["safety_result"]:
                    st.info(f"**Tentative Safe Sequence:** {result['safety_result']['safe_sequence_str']}")

                # Offer commit button
                if st.button("💾 Commit Allocation to Live System State", key="commit_btn"):
                    st.session_state["allocation"] = deepcopy(result["final_state"]["allocation"])
                    st.session_state["available"] = list(result["final_state"]["available"])
                    st.session_state["is_custom_data"] = True
                    st.success("Allocation committed successfully! Live system state updated.")
                    st.rerun()

            elif decision == RequestDecision.WAITING_DEFERRED:
                st.markdown(f"""
                <div class="academic-wait" style="font-size: 1.15rem;">
                    <span class="badge-wait">STATUS: WAITING / DEFERRED — INSUFFICIENT AVAILABLE</span><br><br>
                    {result['explanation']}
                </div>
                """, unsafe_allow_html=True)

            elif decision == RequestDecision.DENIED_UNSAFE:
                st.markdown(f"""
                <div class="academic-warning" style="font-size: 1.15rem;">
                    <span class="badge-unsafe">STATUS: DENIED — UNSAFE TENTATIVE STATE (ROLLED BACK)</span><br><br>
                    {result['explanation']}
                </div>
                """, unsafe_allow_html=True)
                if result["safety_result"]:
                    st.warning(f"Safety check failed. Unfinished processes: {[f'P{u}' for u in result['safety_result']['unfinished_processes']]}")

            elif decision == RequestDecision.INVALID_EXCEEDS_NEED:
                st.markdown(f"""
                <div class="academic-warning" style="font-size: 1.15rem;">
                    <span class="badge-unsafe">STATUS: INVALID — REQUEST EXCEEDS REMAINING NEED</span><br><br>
                    {result['explanation']}
                </div>
                """, unsafe_allow_html=True)

            else:  # INVALID INPUT
                st.markdown(f"""
                <div class="academic-warning" style="font-size: 1.15rem;">
                    <span class="badge-unsafe">STATUS: INVALID INPUT / BAD PROCESS IDENTIFIER</span><br><br>
                    {result['explanation']}
                </div>
                """, unsafe_allow_html=True)

            # State Comparison Table
            st.markdown("#### 🔍 State Immutability & Rollback Verification")
            st.caption("Verifies that the original system state was preserved defensively unless granted and committed.")

            comp_df = pd.DataFrame({
                "Metric": ["Available Vector", f"Allocation P{sel_proc}", f"Remaining Need P{sel_proc}"],
                "Original State": [str(avail), str(alloc[sel_proc]), str(need[sel_proc])],
                "Tentative / Final State": [
                    str(result["final_state"]["available"]),
                    str(result["final_state"]["allocation"][sel_proc]),
                    str(calculate_need_matrix(result["final_state"]["allocation"], max_mat)[sel_proc]),
                ],
                "State Mutated?": ["Yes (Granted)" if result["is_granted"] else "No (Preserved)" for _ in range(3)],
            })
            st.dataframe(comp_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# PAGE 5: Deadlock Detection & RAG
# -------------------------------------------------------------------------
elif selected_page == "5. Deadlock Detection & RAG":
    st.markdown('<div class="main-title">Deadlock Detection & Resource Allocation Graph (RAG)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Detect existing deadlocks in multi-instance systems and analyze graph cycles</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="academic-info">
        <strong>Distinction between Avoidance and Detection:</strong><br>
        • <strong>Avoidance (Banker's):</strong> Uses <em>Maximum Potential Need</em> ($Need = Max - Alloc$) to prevent the system from ever entering an unsafe state.<br>
        • <strong>Detection:</strong> Uses <em>Active Outstanding Requests</em> ($Request$) to determine if processes are <em>currently deadlocked right now</em>.
    </div>
    """, unsafe_allow_html=True)

    det_col1, det_col2 = st.columns([1, 1])
    with det_col1:
        st.markdown("#### Load Detection Scenario")
        det_scenario = st.radio(
            "Select Detection Scenario",
            ["Scenario A: Genuine Deadlock (3 processes, circular wait)", "Scenario B: No Deadlock (Resolvable)"],
            index=0,
        )
        if "Scenario A" in det_scenario:
            st.session_state["det_allocation"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["allocation"])
            st.session_state["det_request"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["request"])
            st.session_state["det_available"] = list(DEADLOCKED_SYSTEM_CONFIG["available"])
            st.session_state["det_resource_names"] = ["A", "B"]
        else:
            st.session_state["det_allocation"] = [[1, 0], [0, 1], [2, 1]]
            st.session_state["det_request"] = [[0, 1], [1, 0], [0, 0]]
            st.session_state["det_available"] = [0, 1]
            st.session_state["det_resource_names"] = ["A", "B"]

    with det_col2:
        st.markdown("#### Model Assumptions & Limitations")
        st.caption("• Outstanding request matrix represents blocked processes.")
        st.caption("• Processes holding 0 resources are marked Finish=True initially.")
        st.caption("• Algorithm complexity: O(m × n²).")

    st.markdown("---")
    st.markdown("#### 📊 Detection State Matrices")
    d_m1, d_m2, d_m3 = st.columns([1, 1, 1])
    d_n = len(st.session_state["det_allocation"])
    d_m = len(st.session_state["det_available"])
    d_proc = [f"P{i}" for i in range(d_n)]
    d_res = st.session_state["det_resource_names"]

    with d_m1:
        st.markdown("**Allocation Matrix**")
        st.dataframe(pd.DataFrame(st.session_state["det_allocation"], index=d_proc, columns=d_res), use_container_width=True)
    with d_m2:
        st.markdown("**Outstanding Request Matrix**")
        st.dataframe(pd.DataFrame(st.session_state["det_request"], index=d_proc, columns=d_res), use_container_width=True)
    with d_m3:
        st.markdown("**Available Vector**")
        st.dataframe(pd.DataFrame([st.session_state["det_available"]], index=["Available"], columns=d_res), use_container_width=True)

    if st.button("🔎 Run Deadlock Detection Algorithm", type="primary", use_container_width=True):
        det_result = detect_deadlock_multi_instance(
            st.session_state["det_allocation"],
            st.session_state["det_request"],
            st.session_state["det_available"],
        )

        if det_result["is_deadlocked"]:
            st.markdown(f"""
            <div class="academic-warning" style="font-size: 1.15rem;">
                <strong>🚨 DEADLOCK CONFIRMED</strong><br>
                <strong>Deadlocked Processes:</strong> {', '.join(det_result['deadlocked_process_names'])}<br><br>
                {det_result['explanation']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="academic-note" style="font-size: 1.15rem;">
                <strong>✅ NO DEADLOCK DETECTED</strong><br>
                All processes can obtain their requests and finish.<br><br>
                {det_result['explanation']}
            </div>
            """, unsafe_allow_html=True)

        # Detection Trace
        st.markdown("#### 📋 Deadlock Detection Trace")
        det_trace_rows = []
        for tr in det_result["trace"]:
            det_trace_rows.append({
                "Step": tr["step"],
                "Process": tr["process_name"],
                "Work Before": str(tr["work_before"]),
                "Request": str(tr["request"]),
                "Alloc Released": str(tr["allocation_released"]),
                "Work After": str(tr["work_after"]),
                "Finish Vector": str(tr["finish_state"]),
            })
        st.dataframe(pd.DataFrame(det_trace_rows), use_container_width=True, hide_index=True)

    # RAG Graph Visualization
    st.markdown("---")
    st.markdown("### 🕸️ Resource Allocation Graph (RAG) Analysis")
    rag_totals = [
        sum(st.session_state["det_allocation"][i][j] for i in range(d_n)) + st.session_state["det_available"][j]
        for j in range(d_m)
    ]
    rag_info = analyze_resource_allocation_graph(
        st.session_state["det_allocation"],
        st.session_state["det_request"],
        rag_totals,
    )

    st.markdown(f"**Cycle Analysis:** `Has Cycle: {rag_info['has_cycle']}` | `Single Instance System: {rag_info['is_single_instance']}`")
    st.info(rag_info["conclusion"])

    # Build Plotly Network Diagram
    fig = go.Figure()
    # Node coordinates
    node_x = {}
    node_y = {}
    for i in range(d_n):
        node_x[f"P{i}"] = 1.0
        node_y[f"P{i}"] = (i + 1) / (d_n + 1)
    for j in range(d_m):
        node_x[f"R{d_res[j]}"] = 3.0
        node_y[f"R{d_res[j]}"] = (j + 1) / (d_m + 1)

    # Draw edge lines
    for edge in rag_info["edges"]:
        x0, y0 = node_x[edge["from"]], node_y[edge["from"]]
        x1, y1 = node_x[edge["to"]], node_y[edge["to"]]
        edge_color = "#DC2626" if edge["type"] == "request" else "#2563EB"
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode="lines",
            line=dict(width=2, color=edge_color),
            hoverinfo="text",
            text=f"{edge['from']} -> {edge['to']} ({edge['label']})",
            showlegend=False,
        ))

    # Draw Process Nodes
    fig.add_trace(go.Scatter(
        x=[node_x[f"P{i}"] for i in range(d_n)],
        y=[node_y[f"P{i}"] for i in range(d_n)],
        mode="markers+text",
        marker=dict(size=36, color="#3B82F6", line=dict(width=2, color="#1E40AF")),
        text=[f"P{i}" for i in range(d_n)],
        textposition="middle center",
        name="Processes",
    ))

    # Draw Resource Nodes
    fig.add_trace(go.Scatter(
        x=[node_x[f"R{d_res[j]}"] for j in range(d_m)],
        y=[node_y[f"R{d_res[j]}"] for j in range(d_m)],
        mode="markers+text",
        marker=dict(size=40, color="#10B981", symbol="square", line=dict(width=2, color="#065F46")),
        text=[f"R{d_res[j]}" for j in range(d_m)],
        textposition="middle center",
        name="Resources",
    ))

    fig.update_layout(
        title="Resource Allocation Graph (Blue Edges: Allocation R->P | Red Edges: Request P->R)",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#F9FAFB",
        font=dict(color="#111827", family="sans-serif"),
        height=380,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(fig, use_container_width=True)


# -------------------------------------------------------------------------
# PAGE 6: Deadlock Prevention
# -------------------------------------------------------------------------
elif selected_page == "6. Deadlock Prevention":
    st.markdown('<div class="main-title">Deadlock Prevention — Policy Enforcement</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Mathematically eliminate necessary conditions for deadlock (Havender’s Hierarchical Resource Ordering)</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="academic-note">
        <strong>Deadlock Prevention Philosophy:</strong><br>
        Deadlock prevention constrains resource requests in advance so that <em>at least one</em> of the 
        four Coffman conditions cannot physically occur. Unlike Banker's algorithm (avoidance), prevention 
        requires no runtime safety search—it simply enforces strict architectural allocation rules.
    </div>
    """, unsafe_allow_html=True)

    tab_hier, tab_hold = st.tabs(["1. Hierarchical Resource Ordering (Circular Wait)", "2. Conservative Allocation (Hold & Wait)"])

    with tab_hier:
        st.markdown("### 🏆 Policy 1: Global Resource-Acquisition Ordering")
        st.markdown("**Order Defined:** `Resource A (Rank 1) < Resource B (Rank 2) < Resource C (Rank 3) < Resource D (Rank 4)`")
        st.info(
            "**Rule:** A process can only request resource $R_j$ if $rank(R_j) > rank(R_k)$ for all currently held resources $R_k$. "
            "To request a lower-ranked resource, the process must first release all equal or higher-ranked resources."
        )

        prev_col1, prev_col2 = st.columns(2)
        with prev_col1:
            st.markdown("#### Configure Process State")
            p_held = st.multiselect(
                "Resources Currently Held by Process P1",
                ["A (Rank 1)", "B (Rank 2)", "C (Rank 3)", "D (Rank 4)"],
                default=["C (Rank 3)"],
            )
            p_req = st.multiselect(
                "Proposed New Resource Request by Process P1",
                ["A (Rank 1)", "B (Rank 2)", "C (Rank 3)", "D (Rank 4)"],
                default=["A (Rank 1)"],
            )

        with prev_col2:
            st.markdown("#### Coffman Condition Eliminated")
            st.markdown("**Condition Eliminated:** <span class=\"badge-safe\">Circular Wait</span>", unsafe_allow_html=True)
            st.caption(
                "**Mathematical Proof:** Suppose a cycle exists: $P_0 \\rightarrow P_1 \\rightarrow \\dots \\rightarrow P_k \\rightarrow P_0$. "
                "Each process $P_i$ holds $R_{a_i}$ and requests $R_{a_{i+1}}$. By hierarchical policy, "
                "$rank(R_{a_0}) < rank(R_{a_1}) < \\dots < rank(R_{a_k}) < rank(R_{a_0})$, which is an impossible contradiction ($x < x$). "
                "Hence, circular wait can NEVER form."
            )

        # Convert selections to vectors
        held_vec = [1 if f"A (" in s else 0 for s in p_held]
        b_held = 1 if any("B (" in s for s in p_held) else 0
        c_held = 1 if any("C (" in s for s in p_held) else 0
        d_held = 1 if any("D (" in s for s in p_held) else 0
        held_arr = [held_vec[0] if held_vec else 0, b_held, c_held, d_held]

        req_vec = [1 if f"A (" in s else 0 for s in p_req]
        b_req = 1 if any("B (" in s for s in p_req) else 0
        c_req = 1 if any("C (" in s for s in p_req) else 0
        d_req = 1 if any("D (" in s for s in p_req) else 0
        req_arr = [req_vec[0] if req_vec else 0, b_req, c_req, d_req]

        policy = HierarchicalOrderingPolicy(["A", "B", "C", "D"])
        eval_res = policy.evaluate_request(1, held_arr, req_arr)

        st.markdown("---")
        st.markdown("#### 🎯 Prevention Decision")
        if eval_res["allowed"]:
            st.markdown(f"""
            <div class="academic-note" style="font-size: 1.1rem;">
                <span class="badge-safe">ALLOWED — ORDERING PRESERVED</span><br><br>
                {eval_res['reason']}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="academic-warning" style="font-size: 1.1rem;">
                <span class="badge-unsafe">REJECTED — ORDERING VIOLATION</span><br><br>
                {eval_res['reason']}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("#### ⚖️ Engineering Trade-offs of Hierarchical Ordering")
        st.text(eval_res["trade_offs"])

    with tab_hold:
        st.markdown("### 📦 Policy 2: Conservative Allocation (Hold & Wait Elimination)")
        st.info(
            "**Rule:** A process must request ALL needed resources at once before beginning execution. "
            "If even one resource is unavailable, none are granted, and the process holds 0 resources while waiting."
        )

        st.markdown("""
        **Trade-offs:**
        - **Advantage:** Completely prevents Hold & Wait.
        - **Disadvantage:** Drastically reduces resource utilization (resources reserved at start may not be needed until near end of execution).
        - **Starvation Risk:** Processes with large resource requirements may wait indefinitely.
        """)


# -------------------------------------------------------------------------
# PAGE 7: Deadlock Recovery
# -------------------------------------------------------------------------
elif selected_page == "7. Deadlock Recovery":
    st.markdown('<div class="main-title">Deadlock Recovery — Process Termination & Preemption</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Recover from an active deadlock by aborting victim processes and reclaiming resources</div>', unsafe_allow_html=True)

    rec_alloc = st.session_state["rec_allocation"]
    rec_req = st.session_state["rec_request"]
    rec_avail = st.session_state["rec_available"]
    r_n = len(rec_alloc)
    r_m = len(rec_avail)
    r_names = ["A", "B"]

    # Initial detection check
    init_det = detect_deadlock_multi_instance(rec_alloc, rec_req, rec_avail)

    rec_c1, rec_c2 = st.columns([1, 1])
    with rec_c1:
        st.markdown("#### System State Before Recovery")
        st.dataframe(pd.DataFrame(rec_alloc, index=[f"P{i}" for i in range(r_n)], columns=r_names), use_container_width=True)
        st.info(f"**Available Vector:** {rec_avail}")
        if init_det["is_deadlocked"]:
            st.error(f"Active Deadlock Confirmed on: {', '.join(init_det['deadlocked_process_names'])}")
        else:
            st.success("No active deadlock currently present.")

    with rec_c2:
        st.markdown("#### 🎯 Victim Selection Heuristics")
        if init_det["is_deadlocked"]:
            suggestions = suggest_victim_processes(rec_alloc, init_det["deadlocked_processes"])
            sug_df = pd.DataFrame(suggestions)[["process_name", "total_resources_held", "held_vector"]]
            st.dataframe(sug_df, use_container_width=True, hide_index=True)
            st.caption("Top recommendation releases the most resources to unblock remaining processes.")
        else:
            st.caption("No victims required.")

    st.markdown("---")
    st.markdown("#### 💥 Execute Recovery Action")
    if init_det["is_deadlocked"]:
        victim_to_terminate = st.selectbox(
            "Select Victim Process to Terminate",
            init_det["deadlocked_processes"],
            format_func=lambda x: f"P{x} (Holds {sum(rec_alloc[x])} total units: {rec_alloc[x]})",
        )

        rec_btn_cols = st.columns([1, 1])
        with rec_btn_cols[0]:
            if st.button("🚨 Terminate Victim & Reclaim Resources", type="primary", use_container_width=True):
                rec_result = recover_by_process_termination(victim_to_terminate, rec_alloc, rec_req, rec_avail)

                # Update session state with post-recovery state
                st.session_state["rec_allocation"] = deepcopy(rec_result["state_after"]["allocation"])
                st.session_state["rec_request"] = deepcopy(rec_result["state_after"]["request"])
                st.session_state["rec_available"] = list(rec_result["state_after"]["available"])

                st.markdown("---")
                if rec_result["is_fully_resolved"]:
                    st.markdown(f"""
                    <div class="academic-note" style="font-size: 1.15rem;">
                        <strong>✅ RECOVERY SUCCESSFUL (Deadlock Fully Resolved)</strong><br><br>
                        {rec_result['explanation']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="academic-warning" style="font-size: 1.15rem;">
                        <strong>⚠️ PARTIAL RECOVERY (Deadlock Persists)</strong><br><br>
                        {rec_result['explanation']}
                    </div>
                    """, unsafe_allow_html=True)

                st.rerun()

        with rec_btn_cols[1]:
            if st.button("🔄 Reset Recovery Scenario", use_container_width=True):
                st.session_state["rec_allocation"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["allocation"])
                st.session_state["rec_request"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["request"])
                st.session_state["rec_available"] = list(DEADLOCKED_SYSTEM_CONFIG["available"])
                st.rerun()
    else:
        st.success("All processes have been resolved or terminated. System is clean!")
        if st.button("Reset Scenario", use_container_width=True):
            st.session_state["rec_allocation"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["allocation"])
            st.session_state["rec_request"] = deepcopy(DEADLOCKED_SYSTEM_CONFIG["request"])
            st.session_state["rec_available"] = list(DEADLOCKED_SYSTEM_CONFIG["available"])
            st.rerun()


# -------------------------------------------------------------------------
# PAGE 8: Test Lab & Analytical Results (TC1 to TC6)
# -------------------------------------------------------------------------
elif selected_page == "8. Test Lab & Analytical Results":
    st.markdown('<div class="main-title">Test Lab & Analytical Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Rigorous automated verification of all six required assignment test scenarios (TC1–TC6)</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="academic-note">
        <strong>Automated Evaluation Integrity:</strong><br>
        All PASS / FAIL statuses are computed dynamically by comparing actual program output against 
        independently specified theoretical expectations. Tests cannot pass by default.
    </div>
    """, unsafe_allow_html=True)

    run_all = st.button("🧪 Run All 6 Analytical Test Scenarios", type="primary", use_container_width=True)

    if run_all or "last_test_results" not in st.session_state:
        st.session_state["last_test_results"] = run_all_test_scenarios()

    results = st.session_state["last_test_results"]
    total = len(results)
    passed = sum(1 for tc in results if tc["status"] == "PASS")

    # Scorecard
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.metric("Total Scenarios", total)
    with sc2:
        st.metric("Passed Scenarios", passed)
    with sc3:
        st.metric("Pass Rate", f"{(passed/total)*100:.0f}%")

    st.markdown("---")
    st.markdown("### 📋 Test Scenario Cards")

    for tc in results:
        status_color = "#16A34A" if tc["status"] == "PASS" else "#DC2626"
        badge_class = "badge-safe" if tc["status"] == "PASS" else "badge-unsafe"

        with st.expander(f"{tc['test_id']} — {tc['scenario_name']} [{tc['status']}]", expanded=True):
            col_a, col_b = st.columns([1, 1])
            with col_a:
                st.markdown(f"**Test ID:** `{tc['test_id']}`")
                st.markdown(f"**Inputs:** {tc['inputs_summary']}")
                st.markdown(f"**Expected Result:** {tc['expected_result']}")
            with col_b:
                st.markdown(f"**Status:** <span class=\"{badge_class}\">{tc['status']}</span>", unsafe_allow_html=True)
                st.markdown(f"**Actual Output:** `{tc['actual_output']}`")

            st.markdown(f"**Analytical Conclusion:** {tc['analysis']}")

    # Export Options
    st.markdown("---")
    st.markdown("### 💾 Export Analytical Evidence for Submission")
    exp_c1, exp_c2 = st.columns(2)

    csv_data = export_test_results_to_csv(results)
    md_data = export_test_results_to_markdown(results)

    with exp_c1:
        st.download_button(
            label="📥 Download Test Results as CSV",
            data=csv_data,
            file_name="deadlock_test_results.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with exp_c2:
        st.download_button(
            label="📥 Download Test Results as Markdown Report",
            data=md_data,
            file_name="deadlock_test_report.md",
            mime="text/markdown",
            use_container_width=True,
        )


# -------------------------------------------------------------------------
# PAGE 9: AI Usage Record & Submission
# -------------------------------------------------------------------------
elif selected_page == "9. AI Usage Record & Submission":
    st.markdown('<div class="main-title">AI Usage Record & Submission Checklist</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Academic integrity disclosure table, B.Tech submission checklist, and viva preparation guide</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="background-color: #F8FAFC; border-left: 4px solid #2563EB; padding: 14px 20px; border-radius: 6px; margin-bottom: 18px;">
        <strong style="color: #1E293B; font-size: 1.05rem;">🏛️ MIT Academy of Engineering &mdash; Computer Department</strong><br>
        <span style="color: #334155;">Course: Operating Systems Lab (Activity 2 &mdash; Deadlock Analysis)</span><br><br>
        <strong>👥 Project Team Members:</strong>
        <ul style="margin-top: 6px; margin-bottom: 6px; color: #334155;">
            <li><strong>Parth Wankhade</strong></li>
            <li><strong>Aryan Agarwal</strong></li>
            <li><strong>Vikas Choudhary</strong></li>
            <li><strong>Sanket Kongare</strong></li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="academic-note">
        <strong>Academic Integrity Statement:</strong><br>
        Students must maintain transparency regarding tools used during development. The table below 
        documents generative AI assistance and student verification. You may edit these rows before downloading.
    </div>
    """, unsafe_allow_html=True)

    # Editable AI Usage Record
    st.markdown("#### 📝 Student AI Usage Record (Editable)")
    ai_df = pd.DataFrame(st.session_state["ai_usage_rows"])
    edited_ai_df = st.data_editor(ai_df, key="ai_usage_editor", use_container_width=True, num_rows="dynamic")
    st.session_state["ai_usage_rows"] = edited_ai_df.to_dict("records")

    ai_c1, ai_c2 = st.columns(2)
    with ai_c1:
        st.download_button(
            "📥 Download AI Usage Record (CSV)",
            data=export_ai_usage_record_to_csv(st.session_state["ai_usage_rows"]),
            file_name="ai_usage_record.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with ai_c2:
        st.download_button(
            "📥 Download AI Usage Record (Markdown)",
            data=export_ai_usage_record_to_markdown(st.session_state["ai_usage_rows"]),
            file_name="ai_usage_record.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("### 📋 B.Tech OS Lab Activity 2 — Submission Checklist")
    chk1 = st.checkbox("✅ Complete, functional Python application with modular architecture (src/ and tests/)", value=True)
    chk2 = st.checkbox("✅ Interactive Streamlit web dashboard running locally", value=True)
    chk3 = st.checkbox("✅ Banker's Algorithm safety check with step-by-step Work vector trace", value=True)
    chk4 = st.checkbox("✅ Resource request simulator distinguishing Grant, Wait, Denial, and Invalid inputs", value=True)
    chk5 = st.checkbox("✅ Multi-instance deadlock detection cleanly separated from deadlock avoidance", value=True)
    chk6 = st.checkbox("✅ Hierarchical deadlock prevention policy actively enforced", value=True)
    chk7 = st.checkbox("✅ Deadlock recovery via victim termination with post-recovery verification", value=True)
    chk8 = st.checkbox("✅ Analytical test cases TC1 through TC6 executed and passed with 100% rate", value=True)
    chk9 = st.checkbox("✅ Pytest automated test suite passing cleanly", value=True)
    chk10 = st.checkbox("✅ Viva-voce oral defense prepared", value=True)

    st.markdown("---")
    st.markdown("### 🎓 Viva-Voce Oral Defense Preparation Guide")

    with st.expander("Q1: What is the fundamental difference between Deadlock Avoidance and Deadlock Detection?"):
        st.write(
            "**Answer:** Deadlock Avoidance (e.g. Banker's Algorithm) acts *proactively* using declared maximum claims. "
            "A request is only granted if the resulting tentative state has a guaranteed safe completion sequence. "
            "Deadlock Detection acts *reactively* after requests are granted; it examines *active outstanding blocked requests* "
            "to check if an existing deadlock cycle has already formed."
        )

    with st.expander("Q2: Why does an Unsafe State not always mean Deadlock?"):
        st.write(
            "**Answer:** An unsafe state means the OS *cannot guarantee* that all processes can finish if they all suddenly "
            "request their maximum claims. However, in reality, processes may finish and release resources *before* requesting "
            "their maximum claims. Thus, an unsafe state is a potential danger zone, whereas deadlock is an active standstill."
        )

    with st.expander("Q3: How does Hierarchical Resource Ordering eliminate Circular Wait?"):
        st.write(
            "**Answer:** By assigning each resource a global integer rank (e.g., A=1, B=2, C=3) and requiring processes to "
            "acquire resources in strictly ascending order, it is mathematically impossible to form a circular dependency chain "
            "R0 < R1 < ... < Rk < R0, which would require a resource to have a rank strictly less than itself."
        )

    with st.expander("Q4: In a Resource Allocation Graph, when is a cycle proof of deadlock?"):
        st.write(
            "**Answer:** If all resource types have only *single instances*, a cycle is BOTH a necessary and sufficient condition "
            "for deadlock. However, if resource types have *multiple instances*, a cycle is necessary but NOT sufficient, "
            "because an external process holding an instance of the cycled resource may finish and break the cycle."
        )

    with st.expander("Q5: What are the primary trade-offs of Deadlock Recovery via process termination?"):
        st.write(
            "**Answer:** Process termination wastes all CPU computation performed by the victim so far. Furthermore, "
            "if the victim was updating shared files or data structures, partial updates could leave the system in an inconsistent "
            "state unless checkpointing or database transactional rollbacks are supported."
        )
