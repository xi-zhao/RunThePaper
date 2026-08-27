# Figure Classification

The frozen paper contains three figures and one table.  Every panel and every
visible series was inventoried before numerical implementation.  The selected
scope is exactly the eight theory-numerical panels frozen by the campaign.
Within each selected panel the four visible series are an indivisible target
contract and must all be generated.

| Paper item | Item type | Scientific role | Visible numerical series | Selected? | Decision | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| TABLE001 | table | symbolic context | four error formulas and four gate-count formulas | no | excluded | Tables are inventory context, not executable figure targets. |
| FIG001A | figure panel | schematic context | none | no | excluded | `n=2` TFIM interaction graph. |
| FIG001B | figure panel | schematic context | none | no | excluded | `n=3` TFIM interaction graph. |
| FIG001C | figure panel | schematic context | none | no | excluded | `n=4` TFIM interaction graph. |
| FIG001D | figure panel | schematic context | none | no | excluded | `n=5` TFIM interaction graph. |
| FIG001E | figure panel | schematic context | none | no | excluded | `n=6` TFIM interaction graph. |
| FIG002A | figure panel | theory numerical | `N_analytic`, `N_min`, `g_analytic`, `g_min` | yes | target `T-FIG002A` | XX first-order deterministic resource bounds. |
| FIG002B | figure panel | theory numerical | `N_analytic`, `N_min`, `g_analytic`, `g_min` | yes | target `T-FIG002B` | XX first-order randomised resource bounds. |
| FIG002C | figure panel | theory numerical | `N_analytic`, `N_min`, `g_analytic`, `g_min` | yes | target `T-FIG002C` | XX second-order deterministic resource bounds. |
| FIG002D | figure panel | theory numerical | `N_analytic`, `N_min`, `g_analytic`, `g_min` | yes | target `T-FIG002D` | XX second-order randomised resource bounds. |
| FIG003A | figure panel | theory numerical | `N_analytic`, `N_min`, `g_analytic`, `g_min` | yes | target `T-FIG003A` | TFIM first-order deterministic resource bounds. |
| FIG003B | figure panel | theory numerical | `N_analytic`, `N_min`, `g_analytic`, `g_min` | yes | target `T-FIG003B` | TFIM first-order randomised resource bounds. |
| FIG003C | figure panel | theory numerical | `N_analytic`, `N_min`, `g_analytic`, `g_min` | yes | target `T-FIG003C` | TFIM second-order deterministic resource bounds. |
| FIG003D | figure panel | theory numerical | `N_analytic`, `N_min`, `g_analytic`, `g_min` | yes | target `T-FIG003D` | TFIM second-order randomised resource bounds. |

## Series Contract

Each selected target must emit all four named series at every paper `M` value.
All series use `M` as the sort key and `connect_within_series_only` as the line
policy.  There are no mixed experimental/theory panels and no hidden source
series.  Source images are retained under `internal-paper-reference/` only
for comparison and pixel evidence.
