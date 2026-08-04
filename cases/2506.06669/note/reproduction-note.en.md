# Remote Entanglement Generation Via Enhanced Quantum State Transfer: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2506.06669` scientific reproduction. Its public status is **Historical scientific artifact (10 numerical targets; 10 figure_rendered)** and its frozen audit score is **68.73/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. A formal independent-reimplementation attestation is available.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | FIG1CD | Zig-zag spectrum and signed eigenfunction parity structure. | figure_rendered | unknown |
| `T002` | FIG2ABC_S2_S3 | Analytic three-site PST solution space and detuning-time spectra. | figure_rendered | paper_subset |
| `T003` | FIG2DEF | Five-site PST population spectra and even-site suppression. | figure_rendered | paper_subset |
| `T004` | FIG3AB | Master-equation FST dynamics for m=0 and m=4. | figure_rendered | paper_subset |
| `T005` | FIG3CD | Theory density support for remote Bell generation. | figure_rendered | paper_subset |
| `T006` | FIG3E_S8DEF | FST robustness under even-frequency, odd-frequency and coupling noise. | figure_rendered | paper_subset |
| `T007` | FIG4_ACDF | Separable 3x3 FST dynamics and ideal four-corner W density. | figure_rendered | paper_subset |
| `T008` | FIGS7DEF | PST robustness under three independent parameter-noise channels. | figure_rendered | paper_subset |
| `T009` | FIGS9 | One-dimensional Lindblad Bell fidelity versus m and theory density matrices. | figure_rendered | paper_subset |
| `T010` | FIGS10 | Two-dimensional Lindblad W fidelity versus m and population spectra. | figure_rendered | paper_subset |

## Public artifacts

- 10 independently generated data files;
- 11 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T001=figure_rendered, T002=figure_rendered, T003=figure_rendered, T004=figure_rendered, T005=figure_rendered, T006=figure_rendered, T007=figure_rendered, T008=figure_rendered, T009=figure_rendered, T010=figure_rendered. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
