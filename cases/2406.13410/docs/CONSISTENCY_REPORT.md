# Consistency Report

## Independent checks

| Audit item | Result | Evidence |
| --- | --- | --- |
| Poisson identity and GOE suppression | passed | exact Poisson error `0`; GOE variance below Poisson for `L>=1` |
| Spacing normalization and repulsion | passed | truncated-grid error `0.01106`; `P_P(0)=1`, `P_W(0)=0` |
| Quadratic ion heating | passed | `alpha=0.00963394 K/(V/m)^2`, relative fit RMS `0.002735` |
| Radial/axial nonthermal behavior | passed | high-field radial excess kurtosis `1.4053`; axial distribution remains closer to Gaussian |
| Gaussian cloud width | passed | `19.3095 um` versus printed `19.4(8) um` |
| Classical loss exponent | passed | fitted `-0.73781` versus `-0.75` |
| f-wave survival family | passed | all seven spectra finite, bounded, and nonconstant |
| f-wave energy trend | passed | peak loss occurs at intermediate `0.45 Delta E_s` |
| Polarization capture | passed | unitarity, threshold exponents, and `1/9/36 E_s` barriers |

## What is and is not supported

- The analytic reference curves, classical branch, and dimensionless capture
  problem are directly supported by independent derivation and numerics.
- The reconstructed collision ensemble supports the paper's quadratic heating
  and anisotropy features, but the withheld Julia code and microscopic inputs
  prevent a paper-exact MD claim.
- The resonant recombination implementation supports the partial-wave energy
  trends.  Its unprinted f-wave coupling, bare resonance position, and absolute
  rate scale remain declared assumptions rather than fitted source-pixel data.
- The experimental resonance histograms, survival spectra, and confinement
  scans cannot be assessed quantitatively without author arrays.

## Paper-audit verdict

No paper error candidate is emitted.  The feature-level checks found no stable
formula or trend contradiction after independent limiting-law and invariant
tests.  Missing inputs are a reproducibility limitation, not evidence that the
paper is wrong.  Any future discrepancy remains `inconclusive` until it has two
distinct strong checks, convergence evidence, excluded convention/parameter
alternatives, and a fresh-context protocol-v2 review.

The review bundles are ready under `outputs/review/`, but there is deliberately
no `independent_review.json` until a genuinely fresh reviewer completes both
phases.
