# Demonstrating quantum error mitigation on logical qubits: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `10.1038-s41467-025-67768-4` scientific reproduction. Its public status is **Historical scientific artifact (9 numerical targets; 2 blocked_missing_method, 1 failed, 5 partially_reproduced, 1 reproduced)** and its frozen audit score is **72.25/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | MAIN_FIG2C | Feedback/post-selection expectation under amplified Pauli injection. | failed | paper_subset |
| `T002` | MAIN_FIG3C | One-round corrected and uncorrected repetition-code expectations. | partially_reproduced | paper_subset |
| `T003` | MAIN_FIG3E | Multi-round distance-7 repetition-code expectation at approximately fixed total error. | partially_reproduced | paper_subset |
| `T004` | MAIN_FIG4BC | Distance-3 surface-code logical Pauli channel, Bloch-circle contraction, and state-specific logical observables. | partially_reproduced | paper_subset |
| `T005` | SUPP_FIG8 | Complete versus injection-only ZNE bias and sampling overhead. | partially_reproduced | paper_subset |
| `T006` | SUPP_FIG9 | Large-scale surface-code logical-memory ZNE bias and overhead. | reproduced | paper_exact |
| `T007` | SUPP_TABLE3 | Per-layer unit-error probabilities intended to preserve cumulative injected error. | partially_reproduced | paper_exact |
| `T008` | SUPP_FIG2 | [[72,12,6]] qLDPC Monte Carlo logical-error distribution. | blocked_missing_method | unknown |
| `T009` | SUPP_FIG10BC | Lattice-surgery circuit-level Monte Carlo ZNE bias and overhead. | blocked_missing_method | unknown |

## Public artifacts

- 7 independently generated data files;
- 10 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T001=failed, T002=partially_reproduced, T003=partially_reproduced, T004=partially_reproduced, T005=partially_reproduced, T007=partially_reproduced, T008=blocked_missing_method, T009=blocked_missing_method. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
