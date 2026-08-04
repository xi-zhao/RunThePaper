# Quantum-Coherent Thermodynamics: Leaf Typicality via Minimum-Variance Foliation: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2602.12212` scientific reproduction. Its public status is **Historical scientific artifact (10 numerical targets; 9 evidence_compared, 1 reproduced)** and its frozen audit score is **72.05/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | MAIN_FIG_1 | Spin-1 minimum-variance leaf geometry and leaf-canonical curves. | reproduced | paper_exact |
| `T002` | MAIN_FIG_2_LEFT | Finite-size leaf-typicality outlier diagnostics. | evidence_compared | paper_exact |
| `T003` | MAIN_FIG_2_RIGHT | Exact mixed-state dynamics compared with one delta-selected optimal representative. | evidence_compared | paper_exact |
| `T004` | FIG_S1 | Full local-observable typicality at beta=0.25. | evidence_compared | paper_exact |
| `T005` | FIG_S2 | Full local-observable typicality at beta=0.75. | evidence_compared | paper_exact |
| `T006` | FIG_S3 | Full local-observable typicality at beta=1.75. | evidence_compared | paper_exact |
| `T007` | FIG_S4 | Integrable-foliation counterexample with H and H0 interchanged. | evidence_compared | paper_exact |
| `T008A` | FIG_S5 | Spectral-compression clouds for h0,z=1.5. | evidence_compared | paper_exact |
| `T008B` | FIG_S5 | Spectral-compression clouds for h0,z=0.5. | evidence_compared | paper_exact |
| `T009` | FIG_S6 | Population-weighted diagonal-entropy gain per site. | evidence_compared | paper_exact |

## Public artifacts

- 8 independently generated data files;
- 10 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T002=evidence_compared, T003=evidence_compared, T004=evidence_compared, T005=evidence_compared, T006=evidence_compared, T007=evidence_compared, T008A=evidence_compared, T008B=evidence_compared, T009=evidence_compared. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
