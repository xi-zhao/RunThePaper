# Figure Classification

Every paper figure and table is listed below. Numerical objects are targets;
schematic circuit/context objects are excluded because they contain no
paper-level numerical result.

| Paper item | Kind | Class | Reproduce? | Reason |
| --- | --- | --- | --- | --- |
| Fig. 1 | non_numeric | schematic_context | no | Workflow diagram of circuit fusion and likelihood multiplication. |
| Fig. 2 | numeric | numeric_reproduction | `T_FIG2` | Six independent numerical panels report RMSE versus queries; each panel is separately inventoried in `figure_coverage.json`. |
| Fig. 3 | non_numeric | schematic_context | no | Generic amplitude-amplification circuit. |
| Fig. 4 | non_numeric | schematic_context | no | Generic conventional phase-estimation circuit. |
| Fig. 5 | non_numeric | schematic_context | no | Gate diagram implementing \(\mathcal R\). |
| Fig. 6 | non_numeric | schematic_context | no | Explicit proposed \(n=2\) circuit diagram. |
| Fig. 7 | non_numeric | schematic_context | no | Explicit conventional \(n=2\) circuit diagram. |
| Table 1 | numeric | numeric_reproduction | `T_TABLE1` | Analytic query and post-processing complexity table. |
| Table 2 | numeric | numeric_reproduction | `T_TABLE2` | Numerical CNOT/qubit resource table. |
| Fig. A | numeric | numeric_reproduction | `T_FIGA` | Numerical percentile comparison with conventional AE. |

## Fig. 2 Panel Ledger

| Panel ID | Position | Target probability | Numerical series |
| --- | --- | ---: | --- |
| FIG002_A | upper left | \(2/3\) | classical/LIS/EIS simulation and CR bounds |
| FIG002_B | upper right | \(1/12\) | classical/LIS/EIS simulation and CR bounds |
| FIG002_C | middle left | \(1/3\) | classical/LIS/EIS simulation and CR bounds |
| FIG002_D | middle right | \(1/24\) | classical/LIS/EIS simulation and CR bounds |
| FIG002_E | lower left | \(1/6\) | classical/LIS/EIS simulation and CR bounds |
| FIG002_F | lower right | \(1/48\) | classical/LIS/EIS simulation and CR bounds |

The complete machine-readable decision set is
`figure_coverage.json`, where each Fig. 2 panel is an explicit
`figure_panel` item and each table is a `table` item.
