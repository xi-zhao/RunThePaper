# Figure and Claim Classification

The paper has one active numerical figure, no active numerical table, and four
independently adjudicable quantitative claims that are not already carried by a
display item. The atomic unit is one numerical series or one independent claim.

| Atomic item | Type | Target | Covered? | Current evidence or direct gap |
| --- | --- | --- | --- | --- |
| Main Fig. 1 Euler GHD, t=10 | theory series | T001 | yes | Independently generated TBA profile. |
| Main Fig. 1 Euler GHD, t=20 | theory series | T001 | yes | Independently generated TBA profile. |
| Main Fig. 1 Euler GHD, t=40 | theory series | T001 | yes | Independently generated TBA profile. |
| Main Fig. 1 diffusive GHD, t=10 | theory series | T001 | yes | Reduced collective-mode result exists; its 70-point evidence cap is retained. |
| Main Fig. 1 diffusive GHD, t=20 | theory series | T001 | yes | Reduced collective-mode result exists; its 70-point evidence cap is retained. |
| Main Fig. 1 diffusive GHD, t=40 | theory series | T001 | yes | Reduced collective-mode result exists; its 70-point evidence cap is retained. |
| Main Fig. 1 tDMRG markers, t=10 | theory benchmark series | T003 | **no** | Code and convergence contract are ready, but no paper-time run artifact exists. |
| Main Fig. 1 tDMRG markers, t=20 | theory benchmark series | T003 | **no** | Code and convergence contract are ready, but no paper-time run artifact exists. |
| Main Fig. 1 tDMRG markers, t=40 | theory benchmark series | T003 | **no** | Code and convergence contract are ready, but no paper-time run artifact exists. |
| `(D C)_SzSz=0.137,0.281,0.744` | text claim | T002 | yes | Independently evaluated for ell=3,4,7. |
| General kernel reduces to the hard-rod operator | analytic claim | T004 | **no** | No independent limiting-case artifact or acceptance check. |
| Free-model scattering kernel gives zero diffusion | analytic claim | T005 | **no** | No independent zero-scattering artifact or acceptance check. |
| Navier-Stokes entropy production is non-negative | analytic claim | T006 | **no** | No independent symbolic/numerical positivity artifact. |

## Explicit uncovered-item ledger (6/13)

| Uncovered item | Direct cause | Root cause | Next discriminating action |
| --- | --- | --- | --- |
| tDMRG t=10 | Paper-time output and convergence checks do not exist. | Paper-scale execution has not been run; compute sufficiency is not yet benchmarked. | Run the declared canary/resource benchmark, then the t=10 convergence variant if viable. |
| tDMRG t=20 | Paper-time output and convergence checks do not exist. | Paper-scale execution has not been run; compute sufficiency is not yet benchmarked. | Run the declared canary/resource benchmark, then the t=20 convergence variant if viable. |
| tDMRG t=40 | Paper-time output and convergence checks do not exist. | Paper-scale execution has not been run; compute sufficiency is not yet benchmarked. | Run the declared canary/resource benchmark, then the t=40 convergence variant if viable. |
| Hard-rod limit | No accepted independent limiting-case result. | The earlier reproduction method did not implement this claim as a target. | Derive and execute an independent hard-rod reduction check before paper comparison. |
| Free-model zero diffusion | No accepted independent zero-scattering result. | The earlier reproduction method did not implement this claim as a target. | Implement `T=0 => D=0` as an independent symbolic/numeric invariant. |
| Entropy-production positivity | No accepted independent positivity result. | The earlier reproduction method did not implement the supplement derivation as a target. | Independently derive the quadratic form and test non-negativity on admissible states. |

Machine-readable item-by-item decisions are in `figure_coverage.json`; the
authoritative `project inspect` output marks the same six entries with
`covered=false`.
