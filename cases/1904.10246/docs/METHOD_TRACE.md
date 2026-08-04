# Method Trace

## MTH_MLE — paper-parameter Monte Carlo maximum likelihood

- Source: Sec. 3.1, Eqs. (4)-(6); Sec. 3.3.
- Role: Generate the independent Fig. 2 and Fig. A estimates.
- Inputs: target amplitude `a`, amplification schedule `m_k`, `N_shot`,
  repetition count, and a disclosed deterministic seed.
- Outputs: query count, RMSE or requested absolute-error percentile, Fisher
  bound, and per-series diagnostics.
- Steps:
  1. Convert `a` to `theta=asin(sqrt(a))`.
  2. For every schedule element, sample
     `h_k ~ Binomial(N_shot, sin^2((2m_k+1)theta))`.
  3. Accumulate the joint log-likelihood on the complete
     `[0, pi/2]` domain; endpoints are clipped only inside logarithms.
  4. Select the global grid maximum and use the adjacent log-likelihood
     values for bounded quadratic sub-grid interpolation.
  5. Transform `theta_hat` to `a_hat=sin^2(theta_hat)`.
  6. Aggregate 1000 independent repetitions as RMSE (Fig. 2) or the
     `100*8/pi^2` percentile of absolute error (Fig. A).
- Independent checks:
  - every Bernoulli probability lies in `[0,1]`;
  - at `m=0`, the MLE agrees with `h/N` up to grid/refinement tolerance;
  - query counts agree with the direct schedule sum;
  - the numerical error stays above, and approaches, the Fisher lower bound
    in the asymptotic regime;
  - two executions with the same target seed are byte-deterministic.
- Code pointer: `code/src/amplitude_estimation.py`,
  `code/scripts/run_reproduction_target.py`.
- Status: `verified`.
- Boundary: the authors did not publish their PRNG seed; no attempt is made to
  claim identical random samples.

## MTH_COMPLEXITY — asymptotic schedule derivation

- Source: Sec. 3.2-3.3 and Table 1.
- Role: Independently regenerate all Table 1 rows.
- Steps:
  1. Sum the query weights and squared query weights for Classical, LIS, EIS.
  2. Substitute `epsilon ~ I^{-1/2}`.
  3. Eliminate the schedule depth `M` in favor of `epsilon`.
  4. Multiply search-grid size by likelihood-evaluation cost for
     post-processing.
- Independent checks: symbolic exponent arithmetic yields
  Classical `(2,2)`, LIS `(4/3,5/3)`, EIS `(1,1 with log)`.
- Code pointer: `code/src/amplitude_estimation.py`.
- Status: `verified`.

## MTH_RESOURCES — Qiskit-0.7 resource-table reconstruction

- Source: Sec. 4.2, Figs. 6-7, Table 2.
- Role: Regenerate every exact CNOT and qubit entry in Table 2.
- Inputs: `q=2^r`, `r=0..8`, `n=2`, all-to-all connectivity.
- Steps:
  1. Proposed method: count four preparation CNOTs plus fourteen CNOTs per
     application of `Q`, giving `14q+4`; qubits remain three.
  2. Conventional method: count the controlled-amplification ladder and
     inverse-QFT overhead, giving `262q-127+r(r+1)` CNOTs and `7+r` qubits.
  3. Compare every generated integer to the frozen table, including the
     proposed zero-operator row.
- Independent checks: exact equality for all 37 numeric cells and recurrence
  checks between adjacent powers of two.
- Code pointer: `code/src/amplitude_estimation.py`.
- Status: `verified`.
- Boundary: this is a faithful reconstruction of the paper's frozen Qiskit
  0.7 resource convention, not a claim about a current transpiler.

## MTH_QAE_COMPARE — conventional-QAE percentile comparator

- Source: Appendix A and Ref. 16 construction as described there.
- Role: Generate the conventional-QAE and EIS comparison in Fig. A.
- Steps:
  1. For `M=2^m-1`, form the four integers nearest
     `theta_a M/pi` and `M-theta_a M/pi`.
  2. Map each integer back through `sin^2(pi y/M)`.
  3. Use the largest of the four absolute amplitude errors.
  4. Compare with the `8/pi^2` percentile of independent EIS simulations for
     `N_shot=30` and `100`, and with binomial classical sampling.
- Independent checks: the four candidates respect the `y <-> M-y`
  symmetry and the percentile is exactly `100*8/pi^2`.
- Code pointer: `code/src/amplitude_estimation.py`.
- Status: `verified`.
