# Numerical Methods

## Method Cards

### NUM001 — Global binomial MLE (`T_FIG2`)

- Equations: `EQ_PROB`, `EQ_LOGLIK`, `EQ_FISHER`, `EQ_QUERY`, `EQ_CRB`, `EQ_LIS`, `EQ_EIS`
- Parameters: six paper amplitudes; `N_shot=100`; 1000 repetitions; LIS `M=0..31`; EIS `M=0..9`
- Domain: \(\theta\in[0,\pi/2]\), hence \(\hat a\in[0,1]\)
- Solver: vectorized coarse global likelihood search followed by local bounded refinement
- Random seed: `190410246`
- Output grain: one panel/series/stage point
- Validation: normalization, limiting MLE, exact schedule sums, slopes, CR bound, and high-query ordering
- Risk control: global domain search prevents local likelihood aliases from silently selecting the wrong amplitude

### NUM002 — Complexity identities (`T_TABLE1`)

- Equations: `EQ_QUERY`, `EQ_FISHER`, `EQ_LIS`, `EQ_EIS`
- Method: evaluate finite schedule sums, derive error scaling, then eliminate stage count
- Output grain: one schedule row
- Validation: all six published complexity entries checked exactly

### NUM003 — Resource formulas (`T_TABLE2`)

- Equation: `EQ_RESOURCES`
- Parameters: `n=2`, all-to-all connectivity, Qiskit-0.7 gate convention, Q-operator range 0–256
- Method: independently evaluate closed CNOT and qubit formulas
- Output grain: one Q-operator row
- Validation: 37/37 published numeric cells, constant proposed qubits, and reduction range
- Historical boundary: the obsolete transpiler is not rerun; its published convention and outputs are reconstructed from the paper

### NUM004 — Percentile comparison (`T_FIGA`)

- Equations: `EQ_PROB`, `EQ_LOGLIK`, `EQ_QUERY`, `EQ_EIS`, `EQ_QAE`
- Parameters: `a=1/48`, `N_shot=30,100`, percentile \(100(8/\pi^2)\), 1000 repetitions
- Solver: the same global MLE plus the four nearest conventional phase-grid candidates
- Random seed: `190410247`
- Output grain: one series/stage point
- Validation: monotone conventional curve, EIS comparability, shot-allocation ordering, and classical slope

## Efficiency And Reuse Plan

- Baseline implementation: case-local NumPy likelihood evaluation with SciPy bounded refinement.
- Main bottleneck: repeated global MLE over 1000 Monte Carlo replicas and multiple schedules.
- Efficient choice: batch probability/likelihood arrays and refine only coarse maxima.
- Complexity: linear in replicas, schedule count, and coarse-grid size; no exponential state-vector simulation is required.
- Performance evidence: final Figure 2 target completed in `19.03 s`; Appendix Figure A in `4.58 s`.
- Reuse boundary: amplitude-estimation formulas remain case-local; the generic target guard, formula gate, scorecard, and pixel pipeline remain harness responsibilities.
