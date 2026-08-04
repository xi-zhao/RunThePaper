# Energy Spectra of Compressed Quantum States: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2507.07191` scientific reproduction. Its public status is **Historical scientific artifact (4 numerical targets; 4 reproduced)** and its frozen audit score is **97.50/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | BENCH_IDX91 | The minimum-energy six-level spectrum allowed by the paper's convex-relaxed compression constraint. | reproduced | not_applicable |
| `T002` | FIG001 | Binned half-chain min-entropy and von Neumann entropy across the complete 4x4 AFHM spectrum. | reproduced | paper_exact |
| `T003` | TAB001 | Exact ground-state overlap upper bounds Lambda(D) for bond dimensions 50,100,150. | reproduced | paper_exact |
| `T004` | FIG002 | The three overlap-bound-constrained inverse-square Predict+ spectra in Figure 2. | reproduced | paper_exact |

## Public artifacts

- 3 independently generated data files;
- 2 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
