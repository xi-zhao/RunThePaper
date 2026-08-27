# Numerical Methods

## Model

The local model represents the Steane-code MSP benchmark at feature level. It uses the paper's 42 labeled error locations as the Monte Carlo event count and models postselection plus logical failure by two explicit probabilities:

```text
M = 42
u = 0.22   # undetected-error probability
l = 0.08   # logical-failure probability per undetected error
```

The physical error rate grid is:

```text
1e-4, 2e-4, 5e-4, 1e-3, 2e-3, 5e-3, 1e-2, 2e-2, 5e-2
```

## Algorithms

1. Formula gate:
   - check that PSC examples square to Paulis;
   - check the controlled-H propagation identity;
   - reconstruct `|H><H|` from Pauli expectations.

2. Fidelity and acceptance:
   - compute exact feature curves from the closed model;
   - run `400000` Monte Carlo shots for each `p`;
   - compare Monte Carlo values with the reference curve and sampling error.

3. Runtime:
   - calibrate a small state-vector-like update cost;
   - calibrate propagated-error lookup/update cost;
   - add conservative scheduler/event floors so the plot reports a plausible local feature, not an exaggerated microbenchmark.

4. Sampling precision:
   - repeat the estimator for multiple shot counts;
   - fit the log-log slope of estimator standard deviation versus shots.

## Output Data Schema

- `outputs/data/fidelity_acceptance_benchmark.csv`
  - `p`
  - `exact_acceptance`
  - `mc_acceptance`
  - `acceptance_abs_error`
  - `exact_infidelity`
  - `mc_infidelity`
  - `infidelity_abs_error`
  - `accepted_shots`
  - `total_shots`

- `outputs/data/runtime_proxy_benchmark.csv`
  - `p`
  - `statevector_like_time_per_shot_us`
  - `propagated_clifford_time_per_shot_us`
  - `speedup_ratio`
  - `expected_nontrivial_errors_per_shot`

- `outputs/data/sampling_scaling.csv`
  - `shots`
  - `estimate_std`
  - `scaled_std_times_sqrt_n`

## Numerical Risks

- The generated curves are not the authors' exact Steane-code simulation curves.
- The source package provides final PNGs but not the underlying arrays.
- Runtime comparison is a local proxy; it is useful for the speedup mechanism, not for reproducing the exact wall-clock values in the paper.
- Exact reproduction would require implementing the full Steane gadget and matching the paper's Stim/Cirq shot counts.
