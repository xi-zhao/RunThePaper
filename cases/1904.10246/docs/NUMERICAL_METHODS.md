# Numerical Methods

## NUM001 — Fig. 2 Maximum-Likelihood Simulation

- Target: `T_FIG2`
- Equations/methods: EQ001-EQ005, MTH001-MTH002
- Parameters: six paper amplitudes, \(N_{\rm shot}=100\), 1000 repetitions
- Solver: full-domain theta grid followed by bounded scalar refinement
- Tolerance: grid resolves at least 24 samples per highest likelihood period;
  local `xatol=1e-13`
- Random seed: `190410246` (paper seed unreported; deterministic case control)
- Output schema: tidy CSV with panel, method, \(M\), \(N_q\), simulation RMSE,
  CR bound
- Validation: analytic classical MLE, direct schedule sums, source-reported
  slopes, finite/range checks, all-panel completeness
- Numerical risk: periodic likelihood aliases; controlled by a full physical
  domain search, never by a single local initial guess

## NUM002 — Table 1 Symbolic Scaling

- Target: `T_TABLE1`
- Equations: EQ003-EQ006
- Method: eliminate \(M\) from exact/asymptotic \(N_q(M)\),
  \(\mathcal I(M)\), and search-grid cost
- Output schema: one CSV row per classical/LIS/EIS update rule
- Validation: rational-exponent algebra and exact match to all table entries

## NUM003 — Table 2 Resource Counts

- Target: `T_TABLE2`
- Equations/methods: EQ008, MTH004
- Parameters: \(n=2\), \(b_{\max}=\pi/4\), all-to-all, Qiskit 0.7,
  \(q=0,2^0,\ldots,2^8\)
- Solver: direct primitive-block sum and independently evaluated closed form
- Output schema: CSV rows with both algorithms' CNOT/qubit counts
- Validation: direct/closed-form equality, monotonicity, constant proposed
  qubit count, exact comparison with 37 numeric source cells
- Boundary: counts are compiler-convention evidence, not modern hardware costs

## NUM004 — Fig. A Percentile Comparison

- Target: `T_FIGA`
- Equations/methods: EQ001, EQ002, EQ004, EQ007, MTH001, MTH003
- Parameters: \(a=1/48\), 1000 repetitions, \(N_{\rm shot}=30,100\),
  percentile `81.05694691387022`
- Solver: the same verified global MLE as Fig. 2; conventional series is
  evaluated analytically from the four nearest grid integers
- Random seed: `190410247`
- Output schema: tidy CSV with conventional, EIS-30, EIS-100, and classical
  series
- Validation: exact percentile, convergence, complete series, comparability of
  EIS-30 and conventional envelopes

## Efficiency And Reuse Plan

- Baseline implementation: NumPy/SciPy CPU, chunked global likelihood grids
- Main bottleneck: repeated evaluation of periodic likelihoods
- Efficient choice: group repetitions in vectorized chunks and refine only the
  global grid winner
- Complexity: proportional to repetitions × grid points × schedule length;
  grids remain below the 30-minute Trial budget
- Case boundary: paper schedules, reference crops, style, resource constants,
  and acceptance values remain entirely inside this case
