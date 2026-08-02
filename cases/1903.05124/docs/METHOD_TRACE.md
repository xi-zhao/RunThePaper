# Method Trace

Use this file for algorithmic or systems papers where the key reproduction
object is a method rather than a formula.

## Method cards

### MTH001 — random Clifford stabilizer dynamics

- Source: main model section and Fig. 2(a); Supplement growth and transition sections.
- Role: generate every entropy and mutual-information datum in T001, T003, T004, T005, and T006.
- Inputs: `L,m,d,p`, time horizon, boundary condition, realization count, and seed stream.
- Outputs: stabilizer tableau, entropy before/after measurement, steady-state subsystem entropies, and uncertainty estimates.
- Algorithm steps:
  1. initialize `|0>^(Lm)` as a binary stabilizer tableau;
  2. alternate even/odd neighbouring block pairs;
  3. inside each `2m`-qubit block pair, apply `d` alternating nearest-neighbour layers of uniformly sampled two-qubit Clifford gates;
  4. in every block sample `floor(pm)` or `ceil(pm)` distinct measured qubits with mean `pm` and measure `Z` using the Born-rule tableau update;
  5. compute subsystem entropy from restricted-stabilizer rank;
  6. aggregate independent realizations and persist raw values before plotting.
- Parameters: paper-exact values live in target manifests; author seeds and exact equilibration windows are unavailable and are replaced by fixed public seeds plus a convergence rule.
- Code pointers: `code/src/stabilizer_dynamics.py`, `code/scripts/run_supp_fig_s3.py`, and `code/tests/test_stabilizer_dynamics.py`.
- Checks: 80 seeded H/S/CNOT/Z-measurement circuits agree with an independent dense state-vector entropy calculation; product, Bell, and GHZ values pass; random uniform local Cliffords preserve rank and symplectic commutation; serial and eight-process ensembles are seed-identical; terminal half-chain and `I3` observables are sampled from the same deterministic trajectory; the source-defined odd step leaves the half-chain cut between block pairs; all seven S3 feature and split-sample checks pass for eight paper-exact 240-realization ensembles; no source-image input exists in the generator.
- Status: `verified` (MTH001 may authorize final numerical execution; paper-scale status remains target-specific).
- Open questions: author seeds are unavailable. The paper does specify uniformly sampled two-qubit Clifford gates; the implementation uses the complete 11,520-element group and publishes a fixed seed hierarchy. S3 steady-state windows are used only for validation metrics, while every displayed time point is retained.

### MTH002 — symplectic frame-potential estimator

- Source: Supplement S1, especially Eqs. (S3)–(S10) and Fig. S1.
- Role: generate Supp. Fig. S2 without constructing a `2^22 x 2^22` unitary.
- Inputs: `n=22`, circuit depth `d=2..44`, sample count, and random seed.
- Outputs: `Q_U` samples and means/standard errors of `Q_U^k` for `k=1..4`.
- Algorithm steps: compose the binary symplectic action and phase vector; form the fixed-Pauli kernel of `S-I`; row-reduce over GF(2) while tracking phases; assign `Q_U=0` or `2^r`; average powers.
- Code pointers: `code/src/frame_potential.py`, `code/scripts/run_supp_fig_s2.py`, and `code/tests/test_frame_potential.py`.
- Checks: all 11,520 signed two-qubit Clifford conjugation actions are complete and unique; exact identity/H/S/CNOT traces pass; 96 random binary-tableau traces agree with independent dense `4x4` matrices to `3.56e-15`; serial and parallel seeded batches are deterministic; all four paper-scale frame-potential features pass.
- Status: `verified` (paper-scale T002 execution completed).
- Open questions: the exact random seed is unavailable; it changes Monte Carlo noise, not the target ensemble.

### MTH003 — finite-size collapse and bootstrap

- Source: Supplement half-chain and tripartite-mutual-information sections.
- Role: turn independently simulated entropies into `p_c`, `nu`, `alpha`, and collapse coordinates.
- Inputs: means, standard errors, `p,L,d,m`, critical search windows, and bootstrap seed.
- Outputs: fitted parameters, cost surfaces, bootstrap intervals, and plotted collapse data.
- Algorithm steps: scan/optimize `p_c,nu`; interpolate a common scaling curve only within overlapping support; compute the stated variance-weighted cost; bootstrap the measurement-probability samples; separately fit `S(p_c,L)` versus `ln L`.
- Code pointers: `code/src/finite_size_scaling.py` and `code/tests/test_finite_size_scaling.py`.
- Checks: exact synthetic `p_c=0.42,nu=1.25` recovery; size-by-size leave-one-out stability; bounded-search edge detection; source-style 80% measurement-grid bootstrap; removal of logarithmic size offsets by the subtracted entropy form; and exact recovery of the weighted `S=alpha ln L+c` regression.
- Status: `verified` (final numerical execution allowed; target-level parameter and convergence gates still apply).
- Open questions: the cited collapse papers contain implementation choices not repeated in the article. The implementation therefore publishes its symmetric overlap interpolation, deterministic bounded grid refinement, source-style resampling rule, and leave-one-size-out sensitivity instead of hiding those choices.

Only `verified` opens final numerical execution. An independently checked
`reconstructed` method may open exploratory execution; `source_only` and
`blocked` do not.
