# OS Deadlock Analysis — Test Results Template
## Institution: MIT Academy of Engineering
## Department: Computer Department
## Course: Operating Systems IA Activity 2 — Concurrency & Deadlock Evaluation
## Team Members: Parth Wankhade, Aryan Agarwal, Vikas Choudhary, Sanket Kongare

---

### Test Execution Summary Table

| Test ID | Scenario Name | Inputs Summary | Expected Result | Actual Output | Status |
| :---: | :--- | :--- | :--- | :--- | :---: |
| **TC1** | Banker's Safety — Safe State | 5 Processes, 3 Resources (A, B, C), Available=[3, 3, 2] | Safe State, Complete Sequence Found | is_safe=True; Sequence=<P1 -> P3 -> P4 -> P0 -> P2> | **PASS** |
| **TC2** | Request Exceeds Available | Process P4 requests [4, 2, 0] vs Available [3, 3, 2] | Status: WAITING_DEFERRED; State Preserved | Decision: WAITING_DEFERRED; State Preserved: True | **PASS** |
| **TC3** | Avoidance Denial (Unsafe State) | P1 requests [1, 0] when Available=[1, 1], Tentative Avail=[0, 1] | Status: DENIED_UNSAFE; State Preserved | Decision: DENIED_UNSAFE; State Preserved: True | **PASS** |
| **TC4** | Deadlock Detection Multi-Instance | 3 Processes, Circular Requests, Available=[0, 0] | Deadlock Detected: True; P0, P1, P2 deadlocked | is_deadlocked=True; Candidates=['P0', 'P1', 'P2'] | **PASS** |
| **TC5** | Deadlock Prevention Policy | P0 holds C (rank 3), requests A (rank 1); Order: A < B < C | Request REJECTED; Circular Wait broken | Allowed: False; Condition: Circular Wait | **PASS** |
| **TC6** | Boundary & Invalid Inputs | 6 Subtests (Zero Available, Negative, Dim Mismatch, Exceed Need) | Valid cases accepted; Invalid strictly rejected | 6/6 Subtests Passed | **PASS** |

---

### Detailed Test Notes

#### TC1 — Safe State Verification
- **Configuration:** Standard Silberschatz textbook allocation (5 processes, 3 resource types).
- **Need Calculation:** Need matrix accurately reflects $Maximum - Allocation$.
- **Trace Output:** Step 1 processes P1 ($Need \le Work$). Step 2 processes P3. Step 3 processes P4. Step 4 processes P0. Step 5 processes P2.
- **Final Work:** $[10, 5, 7]$, matching total system resources.

#### TC2 — Resource Request Exceeds Available
- **Condition:** Process P4 requests 4 units of resource A, but Available has only 3 units.
- **Integrity Check:** The request is $\le$ remaining Need (4).
- **Result:** Classified as `WAITING_DEFERRED`. The process waits; the request is neither discarded nor permanently denied, and matrices are completely unchanged.

#### TC3 — Request Produces Unsafe Tentative State
- **Condition:** Request is within remaining Need and within current Available.
- **Tentative Allocation:** Simulation constructs tentative copies where Available becomes $[0, 1]$.
- **Safety Check:** Evaluates tentative state; discovers that zero processes can finish.
- **Result:** Classified as `DENIED_UNSAFE`. Tentative state discarded; original allocation preserved.

#### TC4 — Multi-Instance Deadlock Detection
- **Condition:** Processes P0, P1, P2 with circular outstanding requests and Available=[0, 0].
- **Result:** Neither process can proceed. Multi-instance detection flags $\{P_0, P_1, P_2\}$ as deadlocked.

#### TC5 — Deadlock Prevention Policy
- **Policy:** Havender's Hierarchical Ordering ($A < B < C$).
- **Test:** Process holding resource C attempts to acquire resource A.
- **Result:** Request strictly rejected because $rank(A) \le rank(C)$. Proves Circular Wait elimination.

#### TC6 — Boundary & Invalid Inputs
- **Test 6.1:** Zero Available resources with zero-need process cascading completion $\rightarrow$ Accepted & Safe.
- **Test 6.2:** Process ID out of range $\rightarrow$ Rejected with clear error message.
- **Test 6.3:** Negative request values $\rightarrow$ Rejected immediately.
- **Test 6.4:** Allocation exceeding declared Maximum $\rightarrow$ System validation error flagged.
- **Test 6.5:** Request exceeding remaining Need $\rightarrow$ Maximum claim violation flagged.
- **Test 6.6:** Matrix dimension mismatch $\rightarrow$ Dimension validation error flagged.
