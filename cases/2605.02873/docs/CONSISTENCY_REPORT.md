# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| `complete_reproduction` | 5 | Full frozen theory scope generated independently and all required checks passed |
| `partial_match` | 0 | No in-scope target has a failed scientific component |
| `blocked` | 0 | No scientific, pixel, external-resource, or human boundary remains |
| `not_in_scope` | 1 class | Non-numerical schematic/context remains inventoried but excluded |

Case-level scientific score: **91.6/100**. Pixel lane: **complete**, 5/5,
score **79.52**. The two scores are deliberately independent.

## Per-Target Consistency

| Target | Paper item | Scientific level | Evidence | Disclosed difference |
| --- | --- | --- | --- | --- |
| `T-FIG001A` | Fig. 1(a), one baseline series | `complete_reproduction` (90) | nonnegative; unit normalized; converged; all visible peaks and shoulders | no released author array for pointwise residual |
| `T-FIG001B` | Fig. 1(b), two score series | `complete_reproduction` (90) | direct field finite differences agree at \(8.03\times10^{-11}\); both branch identities retained | no released author array |
| `T-FIG001C` | Fig. 1(c), four code series | `complete_reproduction` (90) | unit noise norm, zero mean, pair inner products \(2.78\times10^{-17}\); expected oscillation hierarchy | no released author code arrays; thin neighboring-panel content in source crop |
| `T-FIG001D` | Fig. 1(d), four retention bars | `complete_reproduction` (90) | Fisher matrices agree at \(1.12\times10^{-6}\); all retention values and bounds pass | raster's second toy label differs slightly from paper text |
| `T-FIGS001` | Fig. S1, five-point width scan | `complete_reproduction` (98) | strictly increasing; five converged values; Table S1 hybrid tolerance passes | smallest near-null row differs by \(4.25\times10^{-7}\) absolute / 2.43% relative |

## Pixel Consistency

| Pixel target | Contract | Axis-box IoU | Density ratio | Ink overlap | Pixel score |
| --- | --- | ---: | ---: | ---: | ---: |
| `PXT-FIG001A` | passed | 0.968276 | 0.948702 | 0.639761 | 87.12 |
| `PXT-FIG001B` | passed | 0.972932 | 1.131631 | 0.516652 | 81.35 |
| `PXT-FIG001C` | passed | 0.948879 | 0.960730 | 0.284791 | 72.87 |
| `PXT-FIG001D` | passed | 0.946145 | 1.021330 | 0.463395 | 78.63 |
| `PXT-FIGS001` | passed | 0.988668 | 0.941020 | 0.458037 | 77.64 |

Every source crop is reference-only and every generated crop traces to an
independent numerical CSV.

## Numerical Reference Checks

- Full Fisher matrix relative Frobenius error:
  \(1.11447\times10^{-6}\).
- Optimized Fisher matrix relative Frobenius error:
  \(1.11772\times10^{-6}\).
- Optimized retention maximum absolute error:
  \(7.71785\times10^{-9}\).
- Toy retention maximum absolute error against paper text:
  \(1.13523\times10^{-4}\).
- Fig. S1 convergence maximum relative error:
  \(8.52298\times10^{-6}\).
- Fig. S1 maximum table-relative error:
  2.428% at the rounded near-null first row; all rows pass the declared
  \(5\times10^{-7}+0.006|\mathrm{reference}|\) tolerance.
