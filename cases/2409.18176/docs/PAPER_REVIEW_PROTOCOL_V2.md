# Paper Review Protocol v2

This case reproduces and audits the paper.  Its conclusions are fail-closed.

1. The complete paper and supplement were inventoried before implementation:
   ten numerical theory targets, three schematic regions, and one diagrammatic
   figure.
2. Formulas and numerical methods were implemented without opening the cited
   Zenodo repository and without author code, author arrays, or curve points
   inferred from source pixels.
3. The numerical run was isolated and attested before original figures were
   extracted for comparison.
4. A source discrepancy can become a `paper_error_candidate` only after two
   distinct strong checks, explicit falsification attempts, precise source
   pinpoints, and fresh-context independent review.
5. Implementation failures remain reproduction failures even when a source
   formula is suspicious.

## Current audit result

No `paper_error_candidate` is emitted.

- `DISC_T_MATRIX_SIGN`: the scattering sign/linewidth convention is incomplete;
  T001 remains a proxy.
- `DISC_HYDRO_MASS_FACTOR`: the supplemental closed-form denominators appear to
  omit mass factors.  The direct matrix and corrected expression agree to
  `1.67e-16`; the literal expression differs by `1.95e-3`.  Classification:
  `inconclusive` until independent symbolic review.
- `DISC_KUBO_BOLTZMANN_SCALE`: our two blind lanes differ by `11.2776`, whereas
  the paper reports a few-percent effect.  Classification:
  `reproduction_discrepancy`; the unexecuted convergence campaign and method
  uncertainty prevent attributing it to the paper.

Machine-readable evidence is in
`outputs/checks/paper_consistency_checks.json`.  The fresh-context review
bundles are prepared separately; no reviewer result is fabricated in this
case.
