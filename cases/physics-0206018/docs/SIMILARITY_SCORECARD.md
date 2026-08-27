# Similarity Scorecard

## Result

- Primary raw scientific-region mean: `73.3528/100`.
- Harness-normalized mean: `64.23/100`.
- Scientific gates: passed for `3/3` targets.
- Render gates: high fidelity `1/3`, needs repair `1/3`, rejected `1/3`.
- Parameter state: `paper_subset`, solely because prose and Fig. 4 disagree on
  the displacement sign.

| Target | Primary pixel score | Full canvas | Normalized target score | Reading |
| --- | ---: | ---: | ---: | --- |
| Fig. 5 | 69.0193 | 99.0456 | 69.02 | Complete scientific curve; sparse foreground remains below 80. |
| Fig. 6 | 97.3720 | 97.3720 | 70.00 | High-fidelity field; normalized score is capped by source-only reference evidence. |
| Fig. 7 | 53.6671 | 97.1944 | 53.66 | Physics and symmetry pass; typography/subpixel curve placement remains poor. |

The score is computed only after the independent NPZ is frozen. Source pixels
may tune presentation properties but never physical parameters, mesh, branch,
samples, numerical arrays, or the declared scoring region.

Machine-readable sources:

- `outputs/checks/pixel_evidence.json`;
- `outputs/checks/render_similarity.json`;
- `outputs/checks/similarity_scorecard.json`.
