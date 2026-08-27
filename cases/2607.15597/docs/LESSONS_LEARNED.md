# Lessons Learned

## Case Summary

- Paper: Deterministic atom-shuttle interconnects via ultrafast atom-ion entangling gate
- PaperID: `2607.15597`
- Current status: numerical feature reproduction, 73.61/100 after quarantining the non-closing T010 Fowler projection
- Main reproduced targets: Fig. 2, Tables S1/S2/S7, 10-ion mode spectrum and closure feature
- Main blockers: MQDT inputs, qLDPC simulator/decoder metadata, full open-system coefficients

## What Worked

- Treating the conditional-force gate as one deep model generated phase space, populations, concurrence, operating-point tables and circular-state approximations.
- Closed-form coherent-state overlaps gave a stronger formula gate than pixel comparison.
- The ion-chain Hessian independently recovered every printed mode frequency; a deterministic constrained optimizer then demonstrated simultaneous closure.
- CSV-first generation made every plotted claim auditable.

## Generalized Experience

| Lesson | Why it matters | Recommendation |
| --- | --- | --- |
| Compare captions/formulas with plotted monotonicity | source figures can contradict their stated model | add a semantic source-consistency gate before imitating a raster |
| Separate existence from identity | an independent closing schedule proves feasibility, not recovery of the author waveform | label parameter provenance per target |
| Inventory scientific inputs inside source archives | TeX and vector figures do not imply simulation reproducibility | count code, raw data, matrices and metadata separately |
| Compare through the same rasterizer | PDF backend and anti-aliasing differences can dominate pixel metrics | rasterize both vector lanes with the same engine, DPI, and font fingerprint |

## Common Pitfalls And Pain Points

The repeated pattern was not numerical instability; it was missing or internally conflicting source metadata.

## New Failure Modes

| Failure mode | Evidence | Detection |
| --- | --- | --- |
| formula/raster direction conflict | Fig. 4(b): `2p_T/N_ops` decreases while raster rises | derivative/sign check against plotted trend |
| cross-section metadata conflict | Fig. S1 prose/figure says 25 segments; Table S4 says 17 | cross-reference every reused parameter |
| stated parameter range excludes adopted table value | circular-state `C4` prose vs Table S13 | unit-aware range validation |
| renderer misses `\\graphicspath` | source figures were under `figures/` | resolve TeX graphic search paths automatically |

## Recommended Practices

Keep exact, reconstructed, proxy, and source-only lanes separate at target level; run source-consistency checks before visual comparison.

Pixel similarity must remain a presentation diagnostic. Exact canvas registration and high axis-bbox overlap can be achieved independently, but missing author data, fonts, or editor transforms prevent a justified pixel-exact claim; copying the source raster would only counterfeit success.

## Reusable Checks Or Tools

| Candidate | Evidence | Destination |
| --- | --- | --- |
| caption/formula monotonicity checker | prevented false Fig. 4(b) pixel imitation | harness experience/checker backlog |
| `\\graphicspath`-aware source renderer | initial render needed explicit subdirectory | `render_source_figures.py` backlog |
| analytic piecewise mode integrals | 25-segment closure in seconds | keep case-local until a second use |

## Harness Backlog Items

- `copied_to_backlog`: `render_source_figures.py` should resolve `\\graphicspath`.
- `copied_to_backlog`: add formula/caption/raster monotonicity and cross-section parameter checks.

## Workflow Change

After source extraction, run three gates before implementation: scientific-input inventory, cross-section parameter consistency, and qualitative formula-to-raster direction checks. Conflicts remain evidence; they must not be silently repaired or copied into the model.
