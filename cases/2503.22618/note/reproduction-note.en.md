# Enhancing Revivals via Projective Measurements in a Quantum Scarred System: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2503.22618` scientific reproduction. Its public status is **Historical scientific artifact (8 numerical targets; 7 blocked_missing_method, 1 reproduced)** and its frozen audit score is **0.00/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T_FIG1` | FIG_MAIN_1 | Random-monitoring entanglement dynamics. | blocked_missing_method | not_applicable |
| `T_FIG2` | FIG_MAIN_2 | Periodic-monitoring fidelity and entanglement. | blocked_missing_method | not_applicable |
| `T_FIG3` | FIG_MAIN_3 | Post-measurement scar weight versus time. | blocked_missing_method | not_applicable |
| `T_FIG4` | FIG_MAIN_4 | Scar phase and amplitude resynchronization. | blocked_missing_method | not_applicable |
| `T_FIGS1` | FIG_SUPP_1 | Entanglement-velocity change after measurement. | blocked_missing_method | not_applicable |
| `T_FIGS2` | FIG_SUPP_2 | Long-time entropy-density finite-size curves. | blocked_missing_method | not_applicable |
| `T_FIGS3` | FIG_SUPP_3 | Bayesian finite-size data collapse. | blocked_missing_method | not_applicable |
| `T_BENCH` | BENCH_EXT | Exact audit of the synthetic Bayesian scar-weight LDP extension. | reproduced | not_applicable |

## Public artifacts

- 1 independently generated data files;
- 1 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T_FIG1=blocked_missing_method, T_FIG2=blocked_missing_method, T_FIG3=blocked_missing_method, T_FIG4=blocked_missing_method, T_FIGS1=blocked_missing_method, T_FIGS2=blocked_missing_method, T_FIGS3=blocked_missing_method. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
