# Figure Classification

Every numerical figure in the main paper and official supplement is covered
by an executable target.

| Paper item | Class | Target | Decision and reason |
| --- | --- | --- | --- |
| Main Fig. 1 | `numeric_reproduction` | T001 | Energy-flow panel; retained as partial because its plotted normalization and relaxation rate conflict with the printed model. |
| Main Fig. 2 | `numeric_reproduction` | T002 | Exact and small-\(q\) Dirichlet-energy trajectories. |
| Main Fig. 3, initial | `numeric_reproduction` | T003 | Initial trace-condition-deviation map. |
| Main Fig. 3, exact at \(T_{\rm short}\) | `numeric_reproduction` | T003 | Exact-flow trace-condition-deviation map. |
| Main Fig. 3, small-\(q\) at \(T_{\rm short}\) | `numeric_reproduction` | T003 | Small-\(q\) trace-condition-deviation map. |
| Supplemental Fig. 1, initial | `numeric_reproduction` | T001 | Initial small-\(q\) trace-deviation field. |
| Supplemental Fig. 1, final | `numeric_reproduction` | T001 | Small-\(q\) trace-deviation field at \(t=15\). |
| Supplemental Fig. 2, initial | `numeric_reproduction` | T001 | Initial metric and curvature fields. |
| Supplemental Fig. 2, final | `numeric_reproduction` | T001 | Small-\(q\) metric and curvature fields at \(t=15\). |
| Supplemental Fig. 3, energy | `numeric_reproduction` | T002 | Exact and small-\(q\) Dirichlet-energy trajectories. |
| Supplemental Fig. 3, Chern number | `numeric_reproduction` | T002 | Same-mesh numerical-Chern trajectories. |
| Supplemental Fig. 4, initial | `numeric_reproduction` | T003 | Initial metric and curvature profiles. |
| Supplemental Fig. 4, exact at \(T_{\rm short}\) | `numeric_reproduction` | T003 | Exact-flow metric and curvature profiles. |
| Supplemental Fig. 4, small-\(q\) at \(T_{\rm short}\) | `numeric_reproduction` | T003 | Small-\(q\) metric and curvature profiles. |
| Supplemental Fig. 5, exact metric/curvature | `numeric_reproduction` | T002 | Exact-flow geometry at \(t=8\). |
| Supplemental Fig. 5, exact curvature | `numeric_reproduction` | T002 | Exact-flow Berry-curvature sign change at \(t=8\). |
| Supplemental Fig. 5, small-\(q\) metric/curvature | `numeric_reproduction` | T002 | Small-\(q\) geometry at \(t=8\). |
| Supplemental Fig. 6, fixed-\(U\) energy | `numeric_reproduction` | T004 | Dirichlet-energy sweep over all published \(V\) values. |
| Supplemental Fig. 6, fixed-\(U\) Chern number | `numeric_reproduction` | T004 | Numerical-Chern sweep over all published \(V\) values. |
| Supplemental Fig. 6, fixed-\(V\) energy | `numeric_reproduction` | T004 | Dirichlet-energy sweep over all published \(U\) values. |
| Supplemental Fig. 6, fixed-\(V\) Chern number | `numeric_reproduction` | T004 | Numerical-Chern sweep over all published \(U\) values. |

The 21 published numerical panels are now separate inventory items. The
independent finite-\(q\) jump and detector studies (`V001`, `V002`) are
case extensions. They do not substitute for paper-figure coverage.
