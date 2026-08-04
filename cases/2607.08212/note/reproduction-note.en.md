# Möbius-Guided Diagonal-Gate Compilation with Native Multiqubit Controlled-Phase Gates on Neutral-Atom Processors: scientific numerical reproduction note

## Bottom line

This is the public package for the historical `2607.08212` scientific reproduction. Its public status is **Historical scientific artifact (6 numerical targets; 4 evidence_compared, 1 partially_reproduced, 1 reproduced)** and its frozen audit score is **70.85/100**. The score records evidence strength; it is neither a percentage of correctness nor a declaration that the whole paper is complete.

Here, reproduction means understanding the paper, following its equations or method, implementing the numerical work independently, and then generating data and figures. The data come from equations, independent numerics, or analytic derivation, not sampled pixels from paper figures. The public package excludes the paper PDF, standalone source figures, digitized image points, comparison boards, author code, and private runtime state. This is a legacy case without a machine-verifiable author-code isolation attestation, so publication does not upgrade it to complete.

## Numerical targets

| Target | Paper item | Scientific meaning | Frozen status | Parameter match |
| --- | --- | --- | --- | --- |
| `ALGEBRA_CORE` | FIG002 | Exact algebraic frontend for diagonal projector phases. | reproduced | paper_exact |
| `FIG3C_NATIVE` | FIG003C | Many-body projector phases remain visible as native CCZ operations. | evidence_compared | paper_subset |
| `FIG3A_ZAP` | FIG003A | Early lowering expands six CCZ blocks into a large one-/two-qubit stream. | evidence_compared | paper_subset |
| `ROUTING_PROXY` | FIG004_008 | Preserving native three- and four-body supports reduces serialized routed work across six disclosed many-body proxy families, without creating an artificial advantage for pairwise controls. | evidence_compared | proxy_model |
| `ROUTING_PROXY_SCALING` | FIG006 | Compact native support streams reduce routed quantum duration and classical compilation/routing work as size grows. | evidence_compared | proxy_model |
| `ROUTING_PROXY_SENSITIVITY` | FIG007 | Fixed routed streams isolate how assumed native three- and four-qubit errors alter the native-vs-ZAP decision. | partially_reproduced | proxy_model |

## Public artifacts

- 5 independently generated data files;
- 6 independently generated figures;
- runnable and inspectable code under `code/`;
- machine-readable boundaries and scoring under `outputs/checks/`.

Run `python code/scripts/verify_public_artifacts.py` to recompute hashes and format/non-empty checks for every published artifact. Numerical entrypoint sources are retained under `code/scripts/` and `code/src/`; some legacy scripts require paper-specific parameters or external public data, as documented in their comments and the numerical-method note.

## Remaining boundary

Frozen non-final target states: FIG3C_NATIVE=evidence_compared, FIG3A_ZAP=evidence_compared, ROUTING_PROXY=evidence_compared, ROUTING_PROXY_SCALING=evidence_compared, ROUTING_PROXY_SENSITIVITY=partially_reproduced. The legacy case has no machine-verifiable author-code isolation attestation. No source-image comparison panel or digitized source curve is published in this projection.

Layout, typography, axes, line styles, palettes, and interpolation may be optimized for rendering diagnostics, but they must not alter physical parameters or numerical arrays and must never replace scientific computation with source-image pixels.
