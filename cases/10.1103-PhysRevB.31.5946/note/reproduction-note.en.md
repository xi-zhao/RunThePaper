# Phase diagrams and critical behavior of Ising square lattices with nearest-, next-nearest-, and third-nearest-neighbor couplings: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `10.1103-PhysRevB.31.5946` scientific reproduction. Its public status is **Historical scientific artifact (15 numerical targets; 11 blocked_missing_method, 1 blocked_missing_parameter, 2 failed, 1 reproduced)** and its frozen audit score is **11.20/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T002` | FIG002 | Exact zero-temperature phase diagram. | reproduced | paper_exact |
| `T004` | FIG004 | Free-energy and entropy integration. | blocked_missing_method | not_applicable |
| `T005` | FIG005 | R=1 and 1.5 phase boundaries. | blocked_missing_method | not_applicable |
| `T006` | FIG006 | R=0.25, 0.5, and 0.75 phase boundaries. | blocked_missing_method | not_applicable |
| `T007` | FIG007 | R=-1, -0.5, and 0 phase boundaries. | blocked_missing_method | not_applicable |
| `T008` | FIG008 | Three-dimensional phase diagram. | blocked_missing_method | not_applicable |
| `T009` | FIG009 | Specific heat for R=0, R'=0.8. | failed | paper_subset |
| `T010` | FIG010 | First-order peak finite-size scaling. | failed | paper_subset |
| `T011` | FIG011 | Binder cumulant crossings. | blocked_missing_method | not_applicable |
| `T012` | FIG012 | Cumulant-derived critical parameters. | blocked_missing_method | not_applicable |
| `T013` | FIG013 | Critical temperature and exponent versus R. | blocked_missing_method | not_applicable |
| `T014` | FIG014 | Fixed-point cumulant versus R. | blocked_missing_method | not_applicable |
| `T015` | FIG015 | Bulk finite-size scaling with source R conflict. | blocked_missing_parameter | not_applicable |
| `T016` | FIG016 | First-order discontinuities. | blocked_missing_method | not_applicable |
| `T017` | FIG017 | Temperature-dependent order parameters. | blocked_missing_method | not_applicable |

## Public artifacts

- 2 independently generated data files;
- 2 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T004=blocked_missing_method, T005=blocked_missing_method, T006=blocked_missing_method, T007=blocked_missing_method, T008=blocked_missing_method, T009=failed, T010=failed, T011=blocked_missing_method, T012=blocked_missing_method, T013=blocked_missing_method, T014=blocked_missing_method, T015=blocked_missing_parameter, T016=blocked_missing_method, T017=blocked_missing_method. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
