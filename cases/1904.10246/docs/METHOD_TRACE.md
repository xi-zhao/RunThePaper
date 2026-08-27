# Method Trace

## MTH001 — Global Maximum-Likelihood Estimation

- Source: Sec. 3.1 and Sec. 3.3.
- Role: estimate \(a\) from all \(h_k\) without phase estimation.
- Inputs: target \(a\), schedule \(m_k\), shots \(N_k\), independent binomial
  counts \(h_k\).
- Output: one global \(\hat a\) per repetition.
- Steps:
  1. sample \(h_k\sim{\rm Binomial}(N_k,p_k(a))\);
  2. evaluate the full joint log-likelihood on a grid spanning
     \([0,\pi/2]\);
  3. retain the global grid maximum;
  4. refine only its bracketing cell with bounded scalar optimization;
  5. map \(\hat\theta\) to \(\hat a=\sin^2\hat\theta\).
- Checks: endpoint-safe log probabilities; analytic \(m=0\) MLE equivalence;
  direct dense-grid agreement on deterministic small examples; likelihood at
  the returned point is no lower than neighboring cells.
- Code pointer: `scripts/reproduce.py::maximum_likelihood_estimates`.
- Status: `verified`.
- Open questions: the authors' precise modified-grid implementation is not
  released; the reproduced estimator solves the same global optimization.

## MTH002 — Fig. 2 Simulation Protocol

- Source: Sec. 3.3 and Fig. 2 caption.
- Role: generate all six query-error panels at paper scale.
- Inputs: \(a\in\{2/3,1/3,1/6,1/12,1/24,1/48\}\),
  \(N_{\rm shot}=100\), LIS/EIS/classical schedules, 1000 repetitions.
- Output: \(\sqrt{\operatorname{mean}[(\hat a-a)^2]}\) at each query count,
  analytic CR curves, and fitted slopes over \(10^3\le N_q\le10^5\).
- Checks: six amplitudes present; all three methods present; exact query
  formulas; reported \(a=1/48\) slopes near \(-0.76,-0.95,-0.50\); monotone
  asymptotic improvement; deterministic rerun checksum.
- Code pointer: `scripts/reproduce.py::run_fig2`.
- Status: `verified`.

## MTH003 — Fig. A Percentile And Conventional Comparator

- Source: Appendix A and Fig. A caption.
- Role: compare EIS to the phase-estimation envelope at equal query scale.
- Inputs: \(a=1/48\), 1000 EIS repetitions, \(N_{\rm shot}=30,100\),
  percentile \(100(8/\pi^2)=81.0569469\), classical sampling, and
  \(Q_m=2^m-1\) conventional grids.
- Output: percentile of \(|\hat a-a|\) for stochastic methods and the
  deterministic largest four-candidate conventional error.
- Checks: exact percentile; all four series; conventional error decreases as
  \(O(1/Q_m)\); \(N_{\rm shot}=30\) EIS remains comparable to conventional AE.
- Code pointer: `scripts/reproduce.py::run_figa`.
- Status: `verified`.

## MTH004 — Circuit Resource Accounting

- Source: Sec. 4.2, Figs. 6-7, Table 2.
- Role: independently generate the resource table under the paper's compiler
  convention.
- Inputs: \(n=2\), \(b_{\max}=\pi/4\), all-to-all connectivity, Qiskit 0.7
  primitive decomposition, maximum powers \(2^0,\ldots,2^8\).
- Output: CNOT and qubit counts for both algorithms.
- Steps: count preparation, bare-\(\mathbf Q\), controlled-\(\mathbf Q\), and
  inverse-QFT blocks; sum by schedule; compare every row with the source table.
- Checks: direct block sum equals the independent closed form for every row;
  proposed qubits stay at three; conventional qubits increase by one per added
  phase bit; all 38 CNOT/qubit numeric cells match the table.
- Code pointer: `scripts/reproduce.py::derive_resource_table`.
- Status: `verified`.

Only the four verified methods above may authorize final target execution.
