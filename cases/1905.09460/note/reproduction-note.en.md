# Topological Phase Transition in Non-Hermitian Quasicrystals: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `1905.09460` scientific reproduction. Its public status is **Historical scientific artifact (4 numerical targets; 2 evidence_compared, 2 partially_reproduced)** and its frozen audit score is **84.29/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | FIG001 | Coincident PT, localization, and topological winding transition of the periodic AAH chain. | evidence_compared | paper_exact |
| `T002` | FIG003 | Laser spectrum broadens across the non-Hermitian transition near Delta_FM=2V0. | partially_reproduced | paper_subset |
| `T003` | SUPP001 | Open-boundary spectra, IPR transition, and edge-localized state counts. | partially_reproduced | paper_exact |
| `T004` | SUPP002 | Exact and low-reflectance etalon transmission amplitude. | evidence_compared | paper_exact |

## Public artifacts

- 8 independently generated data files;
- 4 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T001=evidence_compared, T002=partially_reproduced, T003=partially_reproduced, T004=evidence_compared. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
