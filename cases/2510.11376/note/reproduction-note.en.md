# Disorder-Induced Strongly Correlated Photons in Waveguide QED: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2510.11376` scientific reproduction. Its public status is **Historical scientific artifact (16 numerical targets; 15 blocked_missing_method, 1 reproduced)** and its frozen audit score is **0.00/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T_FIG2` | FIG_MAIN_2 | Transmission antibunching probability maps. | blocked_missing_method | not_applicable |
| `T_FIG3` | FIG_MAIN_3 | Transmission PDFs, minima, and near-blockade maps. | blocked_missing_method | not_applicable |
| `T_FIG4` | FIG_MAIN_4 | Optimized probabilities and scaling with chain size. | blocked_missing_method | not_applicable |
| `T_FIG5` | FIG_MAIN_5 | Reflection antibunching maps and rare tails. | blocked_missing_method | not_applicable |
| `T_FIGS0` | FIG_SUPP_0 | Propagation-phase periodicity maps. | blocked_missing_method | not_applicable |
| `T_FIGS1` | FIG_SUPP_1 | Two-qubit reflection-tail asymptotics. | blocked_missing_method | not_applicable |
| `T_FIGS3` | FIG_SUPP_3 | Near-blockade PDFs and detuning solution clouds. | blocked_missing_method | not_applicable |
| `T_FIGS4` | FIG_SUPP_4 | Reflection correlations and disorder PDFs. | blocked_missing_method | not_applicable |
| `T_FIGS5` | FIG_SUPP_5 | Strong-disorder fidelity, Hellinger, and probabilities. | blocked_missing_method | not_applicable |
| `T_FIGS6` | FIG_SUPP_6 | Transmission loss dependence. | blocked_missing_method | not_applicable |
| `T_FIGS7` | FIG_SUPP_7 | Transmission loss probability maps. | blocked_missing_method | not_applicable |
| `T_FIGS8` | FIG_SUPP_8 | Reflection loss probability maps and tails. | blocked_missing_method | not_applicable |
| `T_FIGS9` | FIG_SUPP_9 | Monte Carlo uncertainty calibration. | blocked_missing_method | not_applicable |
| `T_FIGS10` | FIG_SUPP_10 | Finite-bandwidth input checks. | blocked_missing_method | not_applicable |
| `T_FIGS11` | FIG_SUPP_11 | Chiral-coupling correlation maps. | blocked_missing_method | not_applicable |
| `T_BENCH` | BENCH_EXT | Exact audit of the printed transmission formula and frozen PPB geometry. | reproduced | not_applicable |

## Public artifacts

- 1 independently generated data files;
- 1 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T_FIG2=blocked_missing_method, T_FIG3=blocked_missing_method, T_FIG4=blocked_missing_method, T_FIG5=blocked_missing_method, T_FIGS0=blocked_missing_method, T_FIGS1=blocked_missing_method, T_FIGS3=blocked_missing_method, T_FIGS4=blocked_missing_method, T_FIGS5=blocked_missing_method, T_FIGS6=blocked_missing_method, T_FIGS7=blocked_missing_method, T_FIGS8=blocked_missing_method, T_FIGS9=blocked_missing_method, T_FIGS10=blocked_missing_method, T_FIGS11=blocked_missing_method. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
