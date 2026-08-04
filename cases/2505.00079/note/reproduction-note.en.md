# Emergent photons and mechanisms of confinement: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2505.00079` scientific reproduction. Its public status is **Historical scientific artifact (8 numerical targets; 3 blocked_compute_scale, 1 failed, 4 partially_reproduced)** and its frozen audit score is **30.20/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | FIG002 | Z7 Polyakov order parameter and defect ordering across beta. | partially_reproduced | reduced_scale |
| `T002` | FIG002 | Polyakov phase distributions and representative defects. | partially_reproduced | reduced_scale |
| `T003` | FIG003 | Circular Z4 Polyakov histogram in the photon phase. | partially_reproduced | paper_subset |
| `T004` | FIG004 | Two Z3 susceptibility peaks and Polyakov distributions. | failed | reduced_scale |
| `T005` | FIG005 | Z3/Z4/Z7 correlator ratios approaching the Coulomb curve. | partially_reproduced | paper_subset |
| `T006` | SMFIG001 | Binned error saturation justifying 500 skipped sweeps. | blocked_compute_scale | not_applicable |
| `T007` | SMFIG002 | Raw plaquette correlator components. | blocked_compute_scale | not_applicable |
| `T008` | SMTAB002 | Power-series coefficients of total correlators. | blocked_compute_scale | not_applicable |

## Public artifacts

- 5 independently generated data files;
- 1 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T001=partially_reproduced, T002=partially_reproduced, T003=partially_reproduced, T004=failed, T005=partially_reproduced, T006=blocked_compute_scale, T007=blocked_compute_scale, T008=blocked_compute_scale. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
