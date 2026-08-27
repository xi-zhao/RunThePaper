# Figure Classification

The full ten-page paper and the TeX source bundle were inventoried before any
numerical implementation. The four frozen target item IDs are bundles: each
bundle contains every visible theory sequence in its panel. Experimental
markers and error bars stay in a separate reference lane.

| Paper item | Item type | Class | Selected? | Decision | Visible contents / reason |
| --- | --- | --- | --- | --- | --- |
| Table I | table | `not_in_scope` | no | excluded | Eight logical hidden-variable outcome sets; tables are not numerical-figure targets. |
| Figure 1(a) | figure panel | `schematic_context` | no | excluded | Alice measurement-basis diagram. |
| Figure 1(b) | figure panel | `schematic_context` | no | excluded | Bob measurement-basis diagram. |
| Figure 2(a) | figure panel | `experimental_context` | no | excluded | Sagnac photon-source schematic. |
| Figure 2(b) | figure panel | `experimental_context` | no | excluded | Polarization measurement stations. |
| Figure 2(c) | figure panel | `experimental_context` | no | excluded | Coincidence logic and acquisition. |
| `FIG003-THEORY` | figure-series bundle | `numeric_reproduction` | yes | target `T-FIG003` | Calculated \(\mathcal W\), modelled \(P_{ab'}\), \(P_{bc'}\), \(P_{ac'}\), and \(-0.125\) limit. |
| `FIG003-EXPERIMENT` | figure-series bundle | `experimental_context` | no | excluded | Measured Wigner/probability markers and uncertainty bars. |
| `FIG004-THEORY` | figure-series bundle | `numeric_reproduction` | yes | target `T-FIG004` | Calculated \(\mathcal W\), three modelled probabilities, and ideal \(-0.125\) limit. |
| `FIG004-EXPERIMENT` | figure-series bundle | `experimental_context` | no | excluded | Measured markers and uncertainty bars. |
| `FIG005A-THEORY` | figure-series bundle | `numeric_reproduction` | yes | target `T-FIG005A` | Figure 5 top: calculated \(\mathcal W\), three modelled probabilities, and \(-0.183\) limit. |
| `FIG005A-EXPERIMENT` | figure-series bundle | `experimental_context` | no | excluded | Alice-fixed measured markers and uncertainty bars. |
| `FIG005B-THEORY` | figure-series bundle | `numeric_reproduction` | yes | target `T-FIG005B` | Figure 5 bottom: calculated \(\mathcal W\), three modelled probabilities, and \(-0.183\) limit. |
| `FIG005B-EXPERIMENT` | figure-series bundle | `experimental_context` | no | excluded | Bob-fixed measured markers and uncertainty bars. |

## Theory Sequence Ledger

Every selected bundle contains exactly these five generated sequences:

1. `W_MODEL`: calculated Wigner value;
2. `P_AB`: modelled \(P_{++}^{\hat a\hat b'}\);
3. `P_BC`: modelled \(P_{++}^{\hat b\hat c'}\);
4. `P_AC`: modelled \(P_{++}^{\hat a\hat c'}\);
5. `W_LIMIT`: the panel's visible analytic violation-limit line.

The shaded \(\mathcal W<0\) band, axes, grid, labels, and legend are rendering
semantics rather than extra scientific series.
