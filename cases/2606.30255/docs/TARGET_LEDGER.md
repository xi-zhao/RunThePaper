# Target Ledger

The frozen scope contains four authorization boundaries. A runner must receive
one explicit target ID and may write only that target's data, checks, and
figure.

| Target ID | Paper item | Observable | Formula dependencies | Method dependency | Paper parameters | Status | Planned outputs |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `T-FIG003` | Figure 3 theory bundle | Three \(P_{++}\) curves, \(\mathcal W\), \(-0.125\) line vs relative spacing | `EQC-MEASUREMENT`, `EQC-SOURCE-STATE`, `EQC-DENSITY`, `EQC-BORN`, `EQC-WIGNER`, `EQC-SINGLET-LIMIT`, `EQC-FIDELITY` | `MTH-SCANS` | \(w=0.50,v=0.98,\xi=\pi,\theta_A=\theta_B=0^\circ,\phi\in[0,360^\circ]\) | `reproduced` | `outputs/data/fig003_theory.csv`, `outputs/figures/fig003_theory.png`, `outputs/checks/fig003_theory_scientific.json` |
| `T-FIG004` | Figure 4 theory bundle | Three \(P_{++}\) curves, \(\mathcal W\), \(-0.125\) line vs common absolute rotation | same seven cards | `MTH-SCANS` | \(w=0.36,v=0.99,\xi=\pi,\phi=30^\circ\); plotted central angle \(\Theta\in[0,360^\circ]\), basis start \(\Theta-\phi\) | `reproduced` | `outputs/data/fig004_theory.csv`, `outputs/figures/fig004_theory.png`, `outputs/checks/fig004_theory_scientific.json` |
| `T-FIG005A` | Figure 5 top theory bundle | Three \(P_{++}\) curves, \(\mathcal W\), \(-0.183\) line vs Bob rotation | same seven cards | `MTH-SCANS` | \(w=0.35,v=0.89,\xi=\pi,\phi=30^\circ,\theta_A=0^\circ,\theta_B\in[0,360^\circ]\) | `reproduced` | `outputs/data/fig005a_theory.csv`, `outputs/figures/fig005a_theory.png`, `outputs/checks/fig005a_theory_scientific.json` |
| `T-FIG005B` | Figure 5 bottom theory bundle | Three \(P_{++}\) curves, \(\mathcal W\), \(-0.183\) line vs Alice rotation | same seven cards | `MTH-SCANS` | \(w=0.41,v=0.90,\xi=\pi,\phi=30^\circ,\theta_B=0^\circ,\theta_A\in[0,360^\circ]\) | `reproduced` | `outputs/data/fig005b_theory.csv`, `outputs/figures/fig005b_theory.png`, `outputs/checks/fig005b_theory_scientific.json` |

## Acceptance Contract

Each target must:

- pass the formula and scan-method gates;
- run at `final_reproduction` with an exact paper-to-generated parameter map;
- generate all five theory sequences without reading source pixels or measured
  data;
- pass density-matrix, Born-probability, Wigner-identity, range, periodicity,
  and target-specific analytic checks;
- bind its structured CSV to the guarded execution run;
- produce one independent theory-only plot and one labelled source-vs-generated
  comparison;
- bind to passing pixel evidence after the scientific gate.
