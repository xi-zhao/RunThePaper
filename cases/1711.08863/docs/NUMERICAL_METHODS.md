# Numerical Methods

## NUM001

- Target: T001, Main Fig. 2, all 13 visible curves.
- Equations: EQ001-EQ004.
- Parameters: `gamma=1`, `phi in [0,pi]`, 1001 inclusive points.
- Solver: direct vectorized trigonometric evaluation; no fit or optimizer.
- Random seed: none.
- Output schema: phase plus exchange, two individual, and collective
  coefficients for each connection ordering.
- Validation: general point-pair sum versus independent Table-I expressions;
  exact special-phase identities.
- Numerical risks: only floating-point trigonometric roundoff at analytic zeros;
  checks use `1e-12` tolerance.

## Efficiency And Reuse Plan

- Runtime: 0.36 s in the attested isolated channel.
- Complexity: `O(S P^2 N_phi)` with four setups and at most four points, which
  is effectively linear in the phase grid.
- Memory: below 100 MB including Python/NumPy runtime; CSV is 318 KB.
- Reusable idea: connection-order strings provide a clean cross-paper model for
  waveguide-QED geometry sums; keep this implementation case-local until a
  second paper needs the same abstraction.

## Analytic Claim Methods

- T002: direct arbitrary-point coefficient sums are compared with the
  independently factorized emission-phasor expression, including unequal
  point rates and separate, nested and braided topologies.
- T003: the even-column identity minor proves the chain constraint rank is `N`
  for every `N`; the free phases construct the `N-1` couplings, with N=3,4,6
  numerical sanity checks.
- T004: a unit upper-triangular minor proves the all-to-all rank for every `N`;
  both printed N=3 phase constructions are evaluated directly.

All three methods ran in one isolated, hash-attested local CPU run. They are
analytic scientific evidence, so pixel comparison is intrinsically inapplicable.

## Paper-Scale Campaign Contract

- Config: `config/paper_scale_campaign.json`.
- Run contract: `run_contract_paper_scale.json`.
- Entrypoint: `python scripts/run_paper_scale_campaign.py --config config/paper_scale_campaign.json`.
- Paper scale: `gamma=1`, `0 <= phi <= pi`, 1001 inclusive points.
- Shards: eight contiguous index ranges; scheduler arrays may pass
  `--shard-index 0..7` and finish with `--aggregate-only`.
- Checkpoint/resume: each NPZ binds the full config hash and is validated before
  reuse; `--max-new-shards N` provides a deterministic local stop/resume path.
- Refinement acceptance: a 2001-point grid must agree at all shared points, and
  the refined general-sum/closed-form cross-check must remain below `1e-12`.
- Run boundary: only smoke/resume tests were executed in this upgrade. The
  existing isolated 1001-point dataset remains the scientific evidence.
