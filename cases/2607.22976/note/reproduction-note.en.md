# Spectral Topology and Non-Bloch Band Theory for Domain-Wall Systems: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2607.22976` scientific reproduction. Its public status is **Historical scientific artifact (5 numerical targets; 5 evidence_compared)** and its frozen audit score is **84.84/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `T001` | FIG2 | Topological interface localization and standing/traveling profiles. | evidence_compared | paper_subset |
| `T002` | FIG3 | Ronkin flat-region collapse and multi-valued domain GBZs. | evidence_compared | paper_subset |
| `T003` | FIG4 | Nonzero flux winding bounded by traveling modes. | evidence_compared | paper_subset |
| `T004` | FIGS1 | Ronkin and finite-diagonalization density agreement. | evidence_compared | paper_subset |
| `T005` | FIGS2BC | Boundary-sensitive change from ring to open chain and constituent OBC union. | evidence_compared | paper_exact |

## Public artifacts

- 5 independently generated data files;
- 10 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: T001=evidence_compared, T002=evidence_compared, T003=evidence_compared, T004=evidence_compared, T005=evidence_compared. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
