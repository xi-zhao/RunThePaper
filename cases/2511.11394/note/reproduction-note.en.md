# Relaxation toward an Ideal Chern Band through Coupling to a Markovian Bath: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2511.11394` scientific reproduction. Its public status is **Historical scientific artifact (6 numerical targets; 5 evidence_compared, 1 partially_reproduced)** and its frozen audit score is **67.10/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | FIG001 | Small-q dissipative approach toward the Dirichlet/Chern bound. | partially_reproduced | paper_exact |
| `V001` | VALIDATION001 | Go/no-go validation of the calibrated geometric jump sum rule. | evidence_compared | not_applicable |
| `V002` | VALIDATION002 | Detector-level go/pivot/stop decision for the Chern-band click idea. | evidence_compared | detector_extension |
| `T002` | FIG002 | Exact versus small-q extended-Hubbard Dirichlet energy. | evidence_compared | paper_exact |
| `T003` | FIG003 | Momentum-resolved trace-condition deviation. | evidence_compared | paper_exact |
| `T004` | SMFIG006 | Robustness of near-ideal relaxation and the finite-mesh topological transition under U and V sweeps. | evidence_compared | paper_exact |

## Public artifacts

- 14 independently generated data files;
- 11 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T001=partially_reproduced, V001=evidence_compared, V002=evidence_compared, T002=evidence_compared, T003=evidence_compared, T004=evidence_compared. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
