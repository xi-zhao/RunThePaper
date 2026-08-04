# Numerical Methods

## Shared ZNE engine

- Inputs: analytic/model expectation callable, code distance, explicit noise
  scales, ideal expectation.
- Solver: dense linear solve of the small Vandermonde-like system.
- Outputs: weights, mitigated expectation, absolute bias, sampling overhead.
- Checks: moment cancellation, K=0 identity, finite Pauli variances.

## T001: feedback circuit

- Paper parameters: `p=0.088`, `theta_0 in {0,-0.4 pi}`, displayed `r` range.
- Method: closed form plus an independent enumeration of all `4^3` injected
  Pauli patterns.
- Parameter match: exact for the literal injection-only circuit specified in
  text, but only a paper subset for Fig. 2(c), whose plotted simulator also
  contains an undisclosed convention or calibration map.
- Falsification result: the literal model changes sign at high `r`, while the
  paper dashed curve stays positive. The discrepancy is preserved and scored
  as a failed alignment rather than repaired from pixels.

## T002--T003: repetition code

- Paper parameters: `d in {3,5,7}`, `M in {1,2,3,4}`, `p=0.036` for fixed
  per-layer tests, and Supplementary Table 3 for fixed cumulative error.
- Method: exact binomial logical-failure sum; independent layer composition.
- Secondary declared model: aggregate median two-qubit/readout errors from
  Supplementary Table 1, kept separate from the injection-only result.
- Numerical risk: an aggregate median cannot reproduce a hidden per-gate map;
  this is a parameter-coverage limitation, not sampling error.

## T004: surface code

- Code: reconstructed rotated `[[9,1,3]]` CSS code.
- Decoder: deterministic minimum-weight independent X/Z decoder.
- Method: pre-enumerate `4^9=262,144` Pauli patterns once, then evaluate exact
  probabilities over the r grid.
- Paper parameter: preparation depolarizing rate `0.075`.
- Disclosed assumption: surface injection unit probability `0.036` because the
  surface-specific value is absent from the article.
- Checks: stabilizer algebra, distance, decoder syndrome closure, channel
  normalization, p=0 identity.

## T005: complete ZNE

- Model: repetition-code engine at `d=3,5,7,9,11`, comparing amplification of
  injected errors only against amplification of all declared effective errors.
- Scan: every K=1 pair with `r0=1` and integer `r1` over the configured range.
- Output: bias/overhead arrays and suppression factor at the paper's reference
  overhead where interpolation is supported.

## T006: large-scale logical memory

- Model: noisy-syndrome path-like Bravyi--Vargo fit with published
  coefficients.
- Paper parameters: `p=1e-3`, `d=7,11,15`, `K=1,...,4`,
  `r_k=k^(1/ceil(d/2))`, and `N in {0.01/P_L(1),0.001/P_L(1)}`.
- Method: double-precision analytic evaluation; logarithms are used inside the
  logical-error fit.
- Checks: explicit `d=11` anchor, monotone logical error with p, finite ZNE
  moments and overhead.

## T007: fixed total error

- Method: solve `1-(1-p_M)^(M+1)=P_tot`, anchoring `P_tot` from the displayed
  M=1 value.
- Acceptance: the four printed values are checked directly. Their cumulative
  error varies by 1.9005% relative range; the exact invariant schedule anchored
  at `M=1` is `[13.600, 9.286, 7.048, 5.680]%`. The paper statement is accepted
  only as approximate.

## Reproducibility controls

- Numerical code reads only `src/`, the entry script, and the authored config.
- The isolated runner denies `raw/`, reference figures, network access, and the
  original case workspace.
- Structured arrays and checks are generated before any reference-informed
  rendering.
