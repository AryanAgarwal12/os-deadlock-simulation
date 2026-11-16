# OS Deadlock Analysis & Resource Allocation Dashboard

**MIT Academy of Engineering — Computer Department**  
**Operating Systems Lab Activity 2 — Concurrency & Deadlock Evaluation**  
*A comprehensive, interactive, and mathematically verified simulation dashboard for Resource Allocation, Concurrency Control, Banker's Algorithm, Deadlock Avoidance, Multi-Instance Detection, Hierarchical Prevention, and Process Recovery.*

### 👥 Team Members
- **Parth Wankhade**
- **Aryan Agarwal**
- **Vikas Choudhary**
- **Sanket Kongare**

**College:** MIT Academy of Engineering  
**Department:** Computer Department

---

## 1. Project Overview & Objectives

In modern multi-threaded operating systems, multiple processes compete for finite shared resources (CPU, memory buffers, I/O devices, file locks). Improper resource management can cause **Deadlock**—a condition where a set of processes are permanently blocked because each holds a resource needed by another.

This project delivers a complete, beginner-friendly yet mathematically rigorous desktop dashboard designed to:
1. **Model Resource Allocation:** Dynamically configure $n$ processes ($P_0, \dots, P_{n-1}$) and $m$ resource types ($A, B, C, \dots$) with Allocation, Maximum, Available, and auto-computed Need matrices ($Need = Maximum - Allocation$).
2. **Execute Banker's Algorithm:** Evaluate system safety with step-by-step Work/Need execution traces and generate complete safe execution sequences.
3. **Simulate Dynamic Resource Requests:** Accurately categorize requests into **Granted (Safe)**, **Waiting (Deferred)**, **Denied (Unsafe)**, and **Invalid (Exceeds Need / Bad Input)** while enforcing zero state mutation on non-granted requests.
4. **Distinguish Avoidance from Detection:** Provide a standalone multi-instance deadlock detection algorithm based on active outstanding requests, alongside single-instance Resource Allocation Graph (RAG) cycle analysis.
5. **Demonstrate Deadlock Prevention:** Enforce Havender's Hierarchical Resource Ordering ($A < B < C < \dots$) to mathematically eliminate Circular Wait.
6. **Demonstrate Deadlock Recovery:** Terminate victim processes, reclaim resources, and dynamically verify whether the deadlock is completely or partially resolved.
7. **Automated Test Lab (TC1–TC6):** Verify all six assignment benchmark scenarios with independently computed expectations and downloadable CSV/Markdown reports.
8. **Academic Integrity:** Provide an editable AI Usage Record and Viva-Voce technical defense guide.

---

## 2. Technology Stack

- **Language:** Python 3.11 / Python 3.13+ (Uses pure standard Python for all core algorithms).
- **Web Dashboard:** Streamlit (`streamlit>=1.30.0`).
- **Data Presentation:** Pandas (`pandas>=2.0.0`) for structured matrix tables.
- **Graph Visualization:** Plotly (`plotly>=5.18.0`) for Resource Allocation Graphs.
- **Automated Testing:** Pytest (`pytest>=7.4.0`) for headless CI/unit testing.
- **Environment:** Local Windows workstation with Python virtual environment (`.venv`). No database, external API, or cloud services required.

---

## 3. Project Architecture

```
DEADLOCK/
│
├── app.py                      # Main interactive Streamlit multi-page web dashboard
├── requirements.txt            # Minimal, lightweight dependencies
├── README.md                   # Comprehensive documentation and run guide
├── .gitignore                  # Git exclusions for venv, cache, and logs
│
├── src/                        # Core algorithms (independent of UI)
│   ├── __init__.py             # Package initializer
│   ├── validation.py           # Robust input/dimension validation & Need calculation
│   ├── bankers_algorithm.py    # Banker's safety algorithm with Work/Finish trace
│   ├── resource_requests.py    # Request simulation with defensive state copies
│   ├── deadlock_detection.py   # Multi-instance detection & RAG cycle analysis
│   ├── deadlock_prevention.py  # Hierarchical ordering & Hold-and-Wait policies
│   ├── deadlock_recovery.py    # Victim process termination & resolution re-check
│   ├── test_scenarios.py       # Deterministic implementations of TC1 to TC6
│   └── reporting.py            # CSV & Markdown report generation
│
├── tests/                      # Automated unit test suite (42 tests)
│   ├── test_validation.py      # Input validation & constraint checking tests
│   ├── test_bankers_algorithm.py # Banker's safety, Work trace & edge-case tests
│   ├── test_resource_requests.py # Dynamic request granting, waiting & denial tests
│   ├── test_deadlock_detection.py # Multi-instance detection & RAG cycle tests
│   ├── test_prevention.py      # Hierarchical ordering & Coffman condition tests
│   ├── test_recovery.py        # Victim selection heuristics & recovery tests
│   └── test_scenarios.py       # TC1–TC6 execution & reporting export tests
│
└── docs/                       # Academic documentation
    ├── viva_questions.md       # 7 in-depth oral defense questions & model answers
    ├── algorithm_explanations.md # Formal mathematical definitions of all algorithms
    └── test_results_template.md# Analytical summary table of TC1–TC6
```

---

## 4. Setup and Installation Instructions (Windows)

Follow these steps in **Visual Studio Code** or the **Windows Command Prompt / PowerShell**:

### Step 1: Open the Project Directory
```powershell
cd DEADLOCK
```

### Step 2: Create and Activate Virtual Environment
```powershell
# Create the virtual environment named .venv
py -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate
```
*(If you see an execution policy prompt in PowerShell, run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` first).*

### Step 3: Install Required Packages
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 5. Running the Application

To launch the interactive dashboard in your web browser:
```powershell
python -m streamlit run app.py
```
Streamlit will automatically open the dashboard in your default browser at `http://localhost:8501`.

---

## 6. Running Automated Tests (Pytest)

To execute the complete 42-test automated unit test suite:
```powershell
python -m pytest -v
```

Expected output:
```
tests/test_bankers_algorithm.py::test_bankers_standard_safe_state PASSED
tests/test_bankers_algorithm.py::test_bankers_unsafe_state PASSED
tests/test_resource_requests.py::test_request_granted_safe PASSED
tests/test_resource_requests.py::test_request_waiting_deferred PASSED
tests/test_resource_requests.py::test_request_denied_unsafe PASSED
tests/test_deadlock_detection.py::test_detection_multi_instance_deadlocked PASSED
tests/test_prevention.py::test_hierarchical_ordering_rejected_descending PASSED
tests/test_recovery.py::test_recover_by_process_termination_successful PASSED
tests/test_scenarios.py::test_tc1_safe_state_passes PASSED
tests/test_scenarios.py::test_tc6_boundary_and_invalid_inputs_passes PASSED
============================= 43 passed in 0.16s ==============================
```

---

## 7. Navigating the 9 Dashboard Sections

| Page | Feature | Academic Focus |
| :--- | :--- | :--- |
| **1. Overview Dashboard** | Conceptual intro, state definitions, Coffman conditions | Distinguishes Safe vs Unsafe vs Deadlock vs Invalid input. |
| **2. Resource Allocation Matrix** | Matrix inputs, dimension controls, presets, Need calculation | Auto-computes $Need = Max - Alloc$; validates $Alloc \le Max$. |
| **3. Banker's Algorithm** | Safety algorithm execution, step-by-step Work traces | Finds safe sequence (e.g. `<P1 -> P3 -> P4 -> P0 -> P2>`). |
| **4. Resource Request Simulation** | Test-case selector (TC1, TC2, TC3, TC4) & request simulator | Direct loading of TC1–TC4; distinguishes Grant, Wait, Deny, Invalid. |
| **5. Deadlock Detection & RAG** | Multi-instance detection & Resource Allocation Graph | Distinguishes outstanding Request from future Need; detects cycles. |
| **6. Deadlock Prevention** | Havender's Hierarchical Resource Ordering ($A < B < C$) | Demonstrates mathematical elimination of Circular Wait. |
| **7. Deadlock Recovery** | Victim process termination & resource reclamation | Ranks victims by held resources; dynamically verifies if deadlock cleared. |
| **8. Test Lab (TC1–TC6)** | Automated benchmark runner with analytical conclusions | Independently compares actual vs expected; exports CSV & Markdown. |
| **9. AI Usage Record & Submission** | Editable AI Usage table, viva guide, submission checklist | Prepares academic integrity statement and viva answers. |

---

## 8. Summary of Assignment Scenarios (TC1 to TC6)

- **TC1 — Safe State Detection:** Evaluates the classic Silberschatz 5-process system. Accurately identifies safe sequence `<P1 -> P3 -> P4 -> P0 -> P2>`.
- **TC2 — Request Exceeds Available:** Process requests resources within remaining Need but exceeding Available. Accurately deferred as `WAITING_DEFERRED`; matrices preserved.
- **TC3 — Request Produces Unsafe State:** Request within Need and Available, but tentative state has no safe sequence. Correctly `DENIED_UNSAFE`; tentative state discarded.
- **TC4 — Deadlock Detection:** Multi-instance detection on circular request scenario. Accurately identifies $\{P_0, P_1, P_2\}$ as deadlocked.
- **TC5 — Deadlock Prevention:** Enforces $A < B < C$. Requesting lower-ranked resource while holding higher-ranked resource is rejected, eliminating Circular Wait.
- **TC6 — Boundary & Invalid Inputs:** Validates 6 distinct edge cases: zero Available with zero-need process, negative quantities, out-of-range process ID, Allocation > Maximum, Request > Need, and dimension mismatches.

---

## 9. Academic Assumptions and Limitations

1. **Banker's Algorithm Limitations:**
   - Requires processes to declare their *maximum* claims in advance, which is difficult to predict in interactive desktop environments.
   - Assumes fixed number of processes and resources during execution.
   - Time complexity $\mathcal{O}(m \times n^2)$ makes it unfeasible for high-frequency kernel thread scheduling.
2. **Deadlock Detection Assumptions:**
   - The outstanding request matrix represents blocked processes holding existing allocations.
   - Processes with zero allocations cannot participate in a deadlock cycle.
3. **Deadlock Recovery Costs:**
   - Process termination discards all CPU time invested by the victim.
   - Partial state updates in files or databases may require rollback checkpoints.

---

## 10. AI Usage Record and Academic Integrity

As part of B.Tech submission guidelines, Page 9 of the application includes an editable **AI Usage Record** table.
- Documents tool assistance (e.g. Antigravity IDE / Gemini for architecture scaffold and test runner).
- Documents student verification against standard textbook proofs (Silberschatz Chapter 8).
- Can be exported as a submission-ready CSV or Markdown file.
