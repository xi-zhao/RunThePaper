# Figure Classification

The full frozen paper and supplement contain one four-panel main figure, one
supplementary numeric table, and one supplementary numeric figure. Every
visible plotted series is theoretical and independently generable. The five
frozen execution items exactly equal the complete theory-numerical figure
scope.

| Paper item | Item type | Visible series | Scientific role | Selected? | Decision | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| FIG001A / Fig. 1(a) | `figure_panel` | normalized \(R_0(y)\) | `theory_numerical` | yes | `target` -> T-FIG001A | Direct finite-width Fresnel baseline |
| FIG001B / Fig. 1(b) | `figure_panel` | normalized \(g_t(y)\), normalized \(g_f(y)\) | `theory_numerical` | yes | `target` -> T-FIG001B | Exact differentiated Fresnel moments |
| FIG001C / Fig. 1(c) | `figure_panel` | optimized \(w_t,w_f\); toy \(h_1,h_2\) | `theory_numerical` | yes | `target` -> T-FIG001C | Noise-metric constructions from independently evaluated scores |
| FIG001D / Fig. 1(d) | `figure_panel` | toy/optimized principal retention, modes 1/2 | `theory_numerical` | yes | `target` -> T-FIG001D | Fisher projection from independent matrices; panel is visible although omitted from caption enumeration |
| TABLES001 / Table S1 | `table` | five width/ratio rows | numeric reference context | no | `excluded` | Tables are outside `numerical_figures_only`; values remain strict reference evidence for Fig. S1 |
| FIGS001 / Fig. S1 | `figure` | \(\rho(a)=F_{ff}/F_{tt}\), five markers joined by one line | `theory_numerical` | yes | `target` -> T-FIGS001 | Independent repeated Fresnel/Fisher calculations |

There are no experimental series, experimental images, schematics, workflow
diagrams, or literature-derived plot panels. Source PNGs and PDF crops remain
reference-only and never feed the generated datasets.
