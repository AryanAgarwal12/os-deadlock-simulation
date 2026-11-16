# Operating Systems Core Algorithms Specification

This document provides formal descriptions, mathematical formulations, and step-by-step pseudo-code for the resource allocation and deadlock management algorithms implemented in this project.

---

## 1. Banker's Safety Algorithm (Dijkstra / Habermann)

### 1.1 State Representation
Let:
- $n$: number of active processes ($P_0, P_1, \dots, P_{n-1}$)
- $m$: number of resource types ($R_0, R_1, \dots, R_{m-1}$)
- $\text{Available}[m]$: vector of available units of each resource type
- $\text{Allocation}[n \times m]$: matrix where $\text{Allocation}[i][j]$ is units of $R_j$ currently allocated to $P_i$
- $\text{Maximum}[n \times m]$: matrix where $\text{Maximum}[i][j]$ is peak demand of $R_j$ by $P_i$
- $\text{Need}[n \times m]$: matrix where $\text{Need}[i][j] = \text{Maximum}[i][j] - \text{Allocation}[i][j]$

### 1.2 Algorithm Steps
1. **Initialize:**
   - $\text{Work} = \text{Available}$ (copy vector of length $m$)
   - $\text{Finish}[i] = \text{False}$ for $i = 0, 1, \dots, n-1$
   - $\text{SafeSequence} = []$
2. **Search for Process:**
   Find an index $i$ such that:
   $$\text{Finish}[i] == \text{False} \quad \text{and} \quad \text{Need}[i][j] \le \text{Work}[j] \quad \forall j \in \{0, \dots, m-1\}$$
3. **Simulate Execution:**
   If such an $i$ exists:
   $$\text{Work}[j] = \text{Work}[j] + \text{Allocation}[i][j] \quad \forall j \in \{0, \dots, m-1\}$$
   $$\text{Finish}[i] = \text{True}$$
   $$\text{Append } i \text{ to } \text{SafeSequence}$$
   Return to Step 2.
4. **Evaluate Completion:**
   If $\text{Finish}[i] == \text{True} \quad \forall i$, then system is in a **SAFE STATE**, and $\text{SafeSequence}$ is a valid execution order.
   Otherwise, system is in an **UNSAFE STATE**, and unfinished processes cannot be guaranteed completion.

---

## 2. Banker's Resource-Request Algorithm

When process $P_i$ makes a request vector $\text{Request}_i[m]$:
1. **Check Claim:** If $\text{Request}_i[j] > \text{Need}[i][j]$ for any $j$, **ABORT with error** (process has exceeded its declared maximum claim).
2. **Check Availability:** If $\text{Request}_i[j] > \text{Available}[j]$ for any $j$, process $P_i$ must **WAIT** (request valid but resources currently unavailable; system state remains unchanged).
3. **Tentative Allocation Simulation:**
   Construct tentative copies:
   $$\text{Available}' = \text{Available} - \text{Request}_i$$
   $$\text{Allocation}'[i] = \text{Allocation}[i] + \text{Request}_i$$
   $$\text{Need}'[i] = \text{Need}[i] - \text{Request}_i$$
4. **Safety Evaluation:**
   Execute Banker's Safety Algorithm on the tentative state.
   - If $\text{is\_safe} == \text{True}$: **GRANT** request, commit tentative state to actual system state.
   - If $\text{is\_safe} == \text{False}$: **DENY** request, discard tentative state, restore original state.

---

## 3. Multiple-Instance Deadlock Detection Algorithm

### 3.1 Matrices Used
- $\text{Allocation}[n \times m]$: currently held resources.
- $\text{Request}[n \times m]$: currently requested, ungranted resources ($P_i$ is blocked waiting for $\text{Request}[i]$).
- $\text{Available}[m]$: unallocated resources.

*Note:* Unlike Banker's Algorithm, $\text{Request}$ represents active blocked requests, **not** future maximum need.

### 3.2 Algorithm Steps
1. Let $\text{Work} = \text{Available}$.
2. For $i = 0, \dots, n-1$:
   $$\text{Finish}[i] = \begin{cases} \text{True} & \text{if } \text{Allocation}[i][j] == 0 \quad \forall j \\ \text{False} & \text{otherwise} \end{cases}$$
3. Find an index $i$ such that:
   $$\text{Finish}[i] == \text{False} \quad \text{and} \quad \text{Request}[i][j] \le \text{Work}[j] \quad \forall j$$
4. If such an $i$ exists:
   $$\text{Work} = \text{Work} + \text{Allocation}[i]$$
   $$\text{Finish}[i] = \text{True}$$
   Return to Step 3.
5. If $\text{Finish}[i] == \text{False}$ for any $i$, then the system is in **DEADLOCK**, and all processes with $\text{Finish}[i] == \text{False}$ are deadlocked.

---

## 4. Single-Instance Resource Allocation Graph (RAG) Analysis

Construct a directed bipartite graph $G = (V, E)$ where:
- $V = P \cup R$, $P = \{P_0, \dots, P_{n-1}\}$, $R = \{R_0, \dots, R_{m-1}\}$.
- **Assignment Edges:** $R_j \rightarrow P_i$ if $R_j$ is allocated to $P_i$.
- **Request Edges:** $P_i \rightarrow R_j$ if $P_i$ has an outstanding request for $R_j$.

**Theorem:**
- In a single-instance system, $G$ contains a directed cycle $\iff$ system is deadlocked.
- In a multiple-instance system, a directed cycle is a necessary condition, but not a sufficient condition.

---

## 5. Deadlock Prevention via Hierarchical Resource Ordering

Impose a total ordering $F: R \rightarrow \mathbb{N}$ on all resource types:
$$F(R_0) < F(R_1) < \dots < F(R_{m-1})$$

**Policy Rule:**
A process $P_i$ holding a set of resources can only request resource $R_j$ if:
$$F(R_j) > \max_{R_k \in \text{Held}(P_i)} F(R_k)$$

To request a lower-ranked resource $R_l$, the process must first release all resources with rank $\ge F(R_l)$.

**Result:**
The Circular Wait condition is eliminated by mathematical proof.
