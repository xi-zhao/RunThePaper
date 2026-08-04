# High-rate qLDPC processors: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2607.28795` scientific reproduction. Its public status is **Historical scientific artifact (4 numerical targets; 2 partially_reproduced, 2 reproduced)** and its frozen audit score is **78.75/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. A formal independent-reimplementation attestation is available.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | TABLE_I_VI | Mitten-code algebraic parameters and canonical logical weights. | partially_reproduced | paper_exact |
| `T002` | TABLE_V | Parallel magic-injection resource counts. | reproduced | paper_exact |
| `T003` | FIG8 | Runtime scaling of sketched versus full-nullspace binary RREF. | partially_reproduced | reduced_scale |
| `T004` | TABLE_X | Per-stage utilization and mean reaction time. | reproduced | paper_exact |

## Public artifacts

- 4 independently generated data files;
- 4 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T001=partially_reproduced, T003=partially_reproduced. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
