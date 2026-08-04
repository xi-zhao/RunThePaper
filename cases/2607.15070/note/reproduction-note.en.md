# Casimir effect for a massive scalar field confined between parallel plates with a spatially varying effective mass: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2607.15070` scientific reproduction. Its public status is **Historical scientific artifact (2 numerical targets; 2 reproduced)** and its frozen audit score is **90.00/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | FIG002 | Normalized Landau-like and additional renormalized vacuum-energy contributions. | reproduced | paper_exact |
| `T002` | FIG003 | Ratio of total renormalized energy to the Landau-like contribution. | reproduced | paper_exact |

## Public artifacts

- 2 independently generated data files;
- 3 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
