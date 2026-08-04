# Exact Fractionalized Ground States in an Extended Spin-1 Kitaev Chain: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2510.12880` scientific reproduction. Its public status is **Historical scientific artifact (4 numerical targets; 4 evidence_compared)** and its frozen audit score is **95.00/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `V001` | VALIDATION001 | Exact algebraic and finite-size validation of the frustration-free 2^N+1 ground-state manifold. | evidence_compared | paper_subset |
| `V002` | VALIDATION002 | Energy-bound and symmetry checks behind the schematic phase diagram. | evidence_compared | paper_exact |
| `T001` | FIG005A | Squared fidelity of the uniform-positive-w fractionalized MPS with the exact ground state. | evidence_compared | paper_exact |
| `T002` | FIG005B | Squared fidelity of a one-w-flip MPS with the exact first-excited manifold. | evidence_compared | paper_exact |

## Public artifacts

- 4 independently generated data files;
- 2 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: V001=evidence_compared, V002=evidence_compared, T001=evidence_compared, T002=evidence_compared. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
