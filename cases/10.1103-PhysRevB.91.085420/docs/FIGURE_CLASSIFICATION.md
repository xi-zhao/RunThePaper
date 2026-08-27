# Figure Classification

Only numerical figures/tables become executable reproduction targets.
This paper has exactly four figures; all are numerical.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| **Fig. 1(a)** | `numeric_reproduction` | **Yes** | Floquet eigenphases ω_{n,k}(β)/π over the (k,β) torus, 3 bands. Establishes the Floquet spectrum; validates the Bloch/Floquet machinery. J=K=3. T101. |
| **Fig. 1(b)** | `numeric_reproduction` | **Yes** | Initial band populations ρ_{n,k}(0) for the site-0 initial state. Direct input to Eqs. (8)/(13). J=K=3. T102. |
| **Fig. 2(a)** | `numeric_reproduction` | **Yes** | Actual population change Δρ_{n,k} vs k (bottom band) from full one-cycle dynamics. J=K=3, T=1024. T201. |
| **Fig. 2(b)** | `numeric_reproduction` | **Yes** | Theoretical Δρ_{n,k} from Eq. (8) (first-order adiabatic perturbation). Cross-check against Fig. 2(a). T202. |
| **Fig. 3** | `numeric_reproduction` | **Yes** | ⟨x⟩(t) over one adiabatic cycle for six durations T=1024..6144; dashed theory line Eq. (13) (filled circles) and Berry-only component (triangles). J=K=4. **Central dynamics target.** T301. |
| **Fig. 4** | `numeric_reproduction` | **Yes** | Δ⟨x⟩ vs J(=K) in [5.0,5.3]: actual (T=2560), theory Eq. (13), Berry-only. Detects Floquet-Chern jump (4,-8,4)->(-8,16,-8) near J=K=5.14. **Central topological-probe target.** T401. |

## Scope summary

- **In scope / reproduced now:** all four figures. Fig. 3 and Fig. 4 carry the
  paper's headline claim (T-independent Δ⟨x⟩ = Berry integral + IBC correction,
  and its use as a topological-transition probe). Fig. 1/2 validate the
  underlying Floquet spectrum, initial populations, and first-order perturbation.
- **Compute:** every target is `paper_exact` and feasible locally (3x3 Bloch
  matrix per k; adiabatic cycle = product of T one-period Floquet operators).
  No reduced-scale or proxy substitution is used.
- **Reference type:** paper figures are visual (no author data files). Comparison
  is structure + feature level (band shapes, symmetry, peak locations, sign
  pattern, transition window), stated explicitly in each scorecard entry.

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`
