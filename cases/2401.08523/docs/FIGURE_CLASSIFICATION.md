# Figure Classification

The full arXiv v2 source and supplement were searched before implementation.
There are exactly two main figures, no tables, and no supplementary figures.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 | `numeric_reproduction` | yes, T001 | Every plotted point is the closed Fermi-Dirac occupation. |
| Main Fig. 2(a) | `numeric_reproduction` | yes, T002 | Three covariance determinants are exact quadratics. |
| Main Fig. 2(b) | `numeric_reproduction` | yes, T002 | Three Shannon branches are the `r -> 1` entropy limit. |
| Main Fig. 2(c) | `numeric_reproduction` | yes, T002 | Five Rényi branches use the printed orders. |

Coverage is `4/4` numerical panels. No experimental or schematic panel is
mixed into these figures. The reference figures are retained only for terminal
pixel comparison and do not count as scientific coverage by themselves.
