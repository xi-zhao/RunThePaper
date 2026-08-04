# Formula Verification

Machine-readable result: `outputs/checks/formula_verification.json`.

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| DW001 | Laurent model, winding, finite Hamiltonian | open | Source coefficients traced; Bloch-stencil identity checked. |
| DW002 | Constrained Ronkin function | open | Jensen/root form and slope identity checked. |
| DW003 | GBZ sector conditions | open | Root indices and monotone sector ordering checked. |
| DW004 | Flux winding | open | Closed-loop determinant-phase definition traced and integer check specified. |
| DW005 | Spectral-potential DOS | open | Normalization and common Laplacian traced. |
| DW006 | Open-chain spectrum | open | Published OBC limit and union condition traced. |

## Open but non-exact presentation choices

| Formula | Missing paper detail | Numerical consequence |
| --- | --- | --- |
| DW001 | Cross-interface finite stencil | Finite eigenvectors may differ locally; bulk/TDL conditions are unchanged. |
| DW003 | Exact `E1-E3` and representative state indices | Fig. 2(c,d) and Fig. 3(b-d) use deterministic physics-selected examples and are `paper_subset`. |
| DW005 | Energy-grid resolution | DOS grid is convergence-controlled rather than source-identical. |
