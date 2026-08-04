# Amplitude Estimation without Phase Estimation: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `1904.10246` scientific reproduction. Its public status is **Historical scientific artifact (4 numerical targets; 4 reproduced)** and its frozen audit score is **95.00/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T_FIG2` | FIG002 | RMSE of the amplitude MLE versus oracle-query count for classical, LIS, and EIS schedules. | reproduced | paper_exact |
| `T_TABLE1` | TAB001 | Asymptotic query and classical post-processing costs versus target error. | reproduced | paper_exact |
| `T_TABLE2` | TAB002 | CNOT and qubit resources for proposed and conventional circuits. | reproduced | paper_exact |
| `T_FIGA` | FIGA | 81-percentile absolute amplitude error for conventional QAE, EIS, and classical sampling. | reproduced | paper_exact |

## Public artifacts

- 4 independently generated data files;
- 4 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
