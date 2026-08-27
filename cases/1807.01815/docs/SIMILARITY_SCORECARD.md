# Similarity Scorecard

## Case Score

- Panel-weighted capped score: **67.08/100**
- Similarity level: `numerical_feature_reproduction`
- Scientific summary: Thirteen of fifteen independently generated numerical subpanels reproduce their declared scientific feature; Supplement Fig. S2(a,b) has one shared stable difference currently classified as parameter_ambiguity; it is not eligible for paper_error_candidate.
- Post-freeze mean foreground pixel similarity: **55.89/100**
- Full-canvas layout diagnostic: 87.39/100
- Pixel note: panels are independently replotted, so resized pixel differences are diagnostic; source pixels never enter numerical generation.

## Per-Panel Scores

| Target | Paper panel | Parameter match | Physics | Pixel diagnostic | Final score |
| --- | --- | --- | --- | ---: | ---: |
| T_FIG1A | Main Fig. 1(a) | reduced_scale | passed | 54.65 | 70.00 |
| T_FIG1B | Main Fig. 1(b) | reduced_scale | passed | 44.25 | 70.00 |
| T_FIG2A | Main Fig. 2(a) | reduced_scale | passed | 46.22 | 66.18 |
| T_FIG2B | Main Fig. 2(b) | reduced_scale | passed | 43.35 | 70.00 |
| T_FIG2C | Main Fig. 2(c) | reduced_scale | passed | 43.68 | 70.00 |
| T_FIG4A | Main Fig. 4(a) | reduced_scale | passed | 63.34 | 70.00 |
| T_FIG4B | Main Fig. 4(b) | reduced_scale | passed | 48.75 | 70.00 |
| T_FIG4C | Main Fig. 4(c) | reduced_scale | passed | 56.52 | 70.00 |
| T_FIG4D | Main Fig. 4(d) | reduced_scale | passed | 46.54 | 70.00 |
| T_FIGS1_HM020 | Supplement Fig. S1, h/Omega=-0.2 | paper_exact | passed | 66.19 | 70.00 |
| T_FIGS1_H000 | Supplement Fig. S1, h/Omega=0 | paper_exact | passed | 66.09 | 70.00 |
| T_FIGS1_H020 | Supplement Fig. S1, h/Omega=0.2 | paper_exact | passed | 65.68 | 70.00 |
| T_FIGS1_H040 | Supplement Fig. S1, h/Omega=0.4 | paper_exact | passed | 66.15 | 70.00 |
| T_FIGS2A | Supplement Fig. S2(a) | unknown | failed | 64.06 | 50.00 |
| T_FIGS2B | Supplement Fig. S2(b) | unknown | failed | 62.95 | 50.00 |

## Main Scientific Result

The undeformed TDVP periods and integrated leakages reproduce all three printed spin anchors. Reduced-size exact dynamics reproduces the special Z2 revivals, suppressed entanglement growth, and thermal behavior of the all-zero quench. Supplement Fig. S1 is regenerated directly from the printed deformed flow. Fig. 2(b,c) also has a code-ready L=30 MPS campaign, but that paper-scale computation was not run and is not included in this score.

Supplement Fig. S2(a,b) remains a declared failed target: the independently constructed deformed Hamiltonian projects back to the printed flow within 3.9e-4, and the residual curves converge from L=10 to 14 within 1.4e-7, but the generated minimum differs from the source panel. Because the closed deformed residual procedure is omitted, protocol-v2 assigns parameter_ambiguity. It is not eligible for paper_error_candidate because paper_exact and fresh_independent_review fail.
