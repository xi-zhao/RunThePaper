# Plaquette: A hardware-aware design platform for fault-tolerant quantum computers: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2607.08767` scientific reproduction. Its public status is **Historical scientific artifact (1 numerical target; 1 failed)** and its frozen audit score is **45.00/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `F5A_PROXY` | Fig. 5(a) coherent over-rotation | The exact Plaquette repetition-memory circuit locations, frame convention, and decoder graph are unpublished; the coherent result is 0.9052 instead of 0.387. | failed | not_recorded |

## Public artifacts

- 1 independently generated data files;
- 1 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: F5A_PROXY=failed. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
