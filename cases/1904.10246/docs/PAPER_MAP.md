# Paper Map

## Identity

- Paper ID: `1904.10246`
- Title: *Amplitude Estimation without Phase Estimation*
- Authors: Yohichi Suzuki, Shumpei Uno, Rudy Raymond, Tomoki Tanaka, Tamiya Onodera, Naoki Yamamoto
- Frozen version: `arXiv:1904.10246v2`
- Local PDF: `raw/paper.pdf`
- Local source archive: `paper-source.tar.gz`
- Publication: *Quantum Information Processing* 19, 75 (2020), DOI `10.1007/s11128-019-2565-2`

## Reproduction Goal

Reproduce all paper-level numerical objects with paper parameters:

1. Fig. 2: six-panel query-error scaling for classical sampling, the linearly
   incremental sequence (LIS), and the exponentially incremental sequence
   (EIS), including the reported slopes at \(a=1/48\).
2. Table 1: query and post-processing complexity exponents.
3. Table 2: CNOT and qubit resource counts for the \(n=2\),
   \(b_{\max}=\pi/4\) integral circuit.
4. Fig. A: the 81-percentile comparison with conventional phase-estimation
   amplitude estimation.

Circuit and workflow drawings are exhaustively mapped as non-numerical context.
No source curve or panel is used as generated scientific data.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| 1 Introduction | Claim framing | Controlled operations and QFT motivate a NISQ-suitable alternative. |
| 2 Preliminary | Amplitude-amplification model | Defines \(\mathcal A\), \(\mathbf Q\), \(a=\sin^2\theta_a\), and amplified success probability. |
| 3.1 Algorithm | Likelihood construction | Independent binomial observations from several \(m_k\) values are fused by ML. |
| 3.2 Statistics | Analytic performance | Fisher information, query count, CR bound, LIS/EIS sequences. |
| 3.3 Numerical simulation | Main numerical target | 1000 repetitions, \(N_{\rm shot}=100\), six amplitudes. |
| 4 Monte Carlo integration | Resource example | \(n=2\), \(b_{\max}=\pi/4\), Qiskit 0.7 gate set, all-to-all connectivity. |
| Appendix A | Comparator target | 81.0569th-percentile EIS/classical error and conventional AE envelope. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Eqs. (2)-(3) | Amplified Bernoulli success probability | verified |
| EQ002 | Eqs. (4)-(6) | Joint binomial log-likelihood and ML estimator | verified |
| EQ003 | Eqs. (7)-(10) | Fisher information and CR error | verified |
| EQ004 | Eq. (11) | Total query count | verified |
| EQ005 | Sec. 3.2 LIS/EIS paragraphs | Exact sequence sums and asymptotic slopes | verified |
| EQ006 | Sec. 3.3, Table 1 | Query/post-processing complexity conversion | verified |
| EQ007 | Appendix A | Conventional AE four-nearest-integer error envelope | verified |
| EQ008 | Sec. 4.2, Figs. 6-7, Table 2 | Closed-form CNOT/qubit resource model | verified |
| MTH001 | Sec. 3.1 and 3.3 | Global ML estimation over \([0,\pi/2]\) | verified |
| MTH002 | Sec. 3.3 | Fig. 2 simulation protocol | verified |
| MTH003 | Appendix A | Percentile/comparator protocol | verified |
| MTH004 | Sec. 4.2 | Gate-decomposition resource accounting | verified |

## Figure/Table Inventory

| Item | Caption summary | Class | Decision |
| --- | --- | --- | --- |
| Fig. 1 | Schematic of circuit fusion and likelihood combination | schematic_context | excluded |
| Fig. 2 | Query count versus RMSE for six target amplitudes | numeric_reproduction | target `T_FIG2` |
| Fig. 3 | Amplitude-amplification circuit for Monte Carlo integration | schematic_context | excluded |
| Fig. 4 | Conventional phase-estimation circuit | schematic_context | excluded |
| Fig. 5 | Controlled-\(R_y\) realization of \(\mathcal R\) | schematic_context | excluded |
| Fig. 6 | \(n=2\) proposed circuit with one \(\mathbf Q\) | schematic_context | excluded |
| Fig. 7 | \(n=2\) conventional circuit with one controlled \(\mathbf Q\) | schematic_context | excluded |
| Table 1 | Query/post-processing complexity by update rule | numeric_reproduction | target `T_TABLE1` |
| Table 2 | CNOT/qubit counts versus maximum \(\mathbf Q\) power | numeric_reproduction | target `T_TABLE2` |
| Fig. A | 81-percentile comparison with conventional AE | numeric_reproduction | target `T_FIGA` |

Fig. 2 has six panels, ordered by the source layout:
`a=2/3`, `a=1/12`, `a=1/3`, `a=1/24`, `a=1/6`, `a=1/48`.

## Assumptions And Evidence Boundaries

- The paper does not report RNG seeds. A fixed case seed is used solely to make
  the independent 1000-repetition simulations deterministic.
- The source gives the exact shot count, repetition count, amplitude values,
  schedules, metrics, and plotted query range. The precise internal grid used
  by the authors' modified brute-force optimizer is not released; the
  reproduction performs an independent global grid search followed by bounded
  local refinement and verifies it against the analytic \(m=0\) MLE.
- Table 2 is tied to the paper's stated Qiskit 0.7 decomposition convention,
  all-to-all connectivity, \(n=2\), and \(b_{\max}=\pi/4\). It is not a claim
  about modern compiler counts.
- EPS/PDF assets are reference-only inputs for comparison and pixel evidence.
