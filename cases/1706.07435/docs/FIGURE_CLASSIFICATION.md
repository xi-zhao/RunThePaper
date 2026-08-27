# Figure Classification

Only independently generable theory-numerical figures, panels, or visible
series become executable targets. Experimental measurements/images,
schematics, context, and tables are inventoried but never generated.

This document is the human-readable narrative. The machine-readable coverage
contract lives in `figure_coverage.json`: every item classified here must also
appear there with a decision (`target`, `excluded`, or `deferred_blocked` with
a named blocker). Split mixed figures into panels and mixed panels into
`figure_series` items. Only ids frozen in
`physics_reproduction_project.json` under
`reproduction_scope.target_item_ids` may be targeted. Skipping a selected
theory-numerical item because it is "supporting" or "similar" is
not allowed. A selected target is regenerated from a verified formula/method;
source-image pixels are reference-only.

| Paper item | Parent item | Item type | Scientific role | Selected? | Decision | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| `FIG001` | — | figure | theory_numerical | yes | target → T001 | Bulk continuum and edge curve are generated from Eqs. (4)–(7). |
| `FIG002_A` | `FIG002` | figure_panel | theory_numerical | yes | target → T002 | Formula-tracked EP energy branches on the caption loop. |
| `FIG002_B` | `FIG002` | figure_panel | theory_numerical | yes | target → T002 | Real/imaginary EP dispersion sheets from direct formula evaluation. |
| `FIG002_C` | `FIG002` | figure_panel | theory_numerical | yes | target → T002 | `kx=0` spectral cut from the same Hamiltonian. |
| `FIG003_A` | `FIG003` | figure_panel | theory_numerical | yes | target → T003 | Phase regions follow the separability and degeneracy conditions. |
| `FIG003_B` | `FIG003` | figure_panel | theory_numerical | yes | target → T003 | EP positions follow the closed trajectory formula. |
| `SUPP001` | — | figure | schematic_context | no | excluded | Patch/torus explanatory drawing contains no numerical observable. |
| `SUPP002` | — | figure | theory_numerical | yes | target → T004 | Domain-wall matching equations generate the energy surface. |
| `SUPP003_A_RE` | `SUPP003` | figure_panel | theory_numerical | yes | target → T005 | Real cylinder spectrum for the caption's `(kappa_x,kappa_y)=(0.1,0)`. |
| `SUPP003_A_IM` | `SUPP003` | figure_panel | theory_numerical | yes | target → T005 | Imaginary cylinder spectrum for the same eigensystems. |
| `SUPP003_B_RE` | `SUPP003` | figure_panel | theory_numerical | yes | target → T005 | Real cylinder spectrum for `(kappa_x,kappa_y)=(0,0.1)`. |
| `SUPP003_B_IM` | `SUPP003` | figure_panel | theory_numerical | yes | target → T005 | Imaginary cylinder spectrum for the same eigensystems. |
| `SUPP004_A_RE` | `SUPP004` | figure_panel | theory_numerical | yes | target → T006 | Real hybrid-point sheet at `m=delta=1`. |
| `SUPP004_A_IM` | `SUPP004` | figure_panel | theory_numerical | yes | target → T006 | Imaginary hybrid-point sheet at `m=delta=1`. |
| `SUPP004_B_KX` | `SUPP004` | figure_panel | theory_numerical | yes | target → T006 | `ky=0` hybrid-point cut. |
| `SUPP004_B_KY` | `SUPP004` | figure_panel | theory_numerical | yes | target → T006 | `kx=0` hybrid-point cut. |
| `SUPP_TABLE_I` | — | table | context | no | excluded | Qualitative taxonomy, checked in the derivation lane. |

Allowed classes:

- `theory_numerical`
- `experimental_measurement`
- `experimental_image`
- `schematic_context`
- `context`
