# Similarity Scorecard

## Case Score

- Overall scientific score: `95/100`
- Similarity level: `complete_reproduction`
- Pixel-fidelity score: `85.72/100`
- Final-reproduction ready: yes, for both numerical targets

The 95-point scientific ceiling comes from comparison against curves
digitized after generation rather than machine-readable author arrays. Pixel
fidelity is reported separately and cannot raise the scientific score.

## Figure Scores

| Figure | Weight | Feature match | Numeric closeness | Scope coverage | Evidence cap | Final |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Main Fig. 2 | 1.0 | 50/50 | 34/35 | 15/15 | 95 | 95 |
| Main Fig. 3 | 1.0 | 50/50 | 35/35 | 15/15 | 95 | 95 |

## Why Main Fig. 2 Passes

- Derived analytic curve and direct Liouvillian differ by only
  \(3.33\times10^{-16}\).
- The independently constructed HPTP processor decomposes into
  \(p_+=1.49999989\), \(p_-=0.49999989\), so \(\kappa=1.99999977\).
- All quasi-sampling points fall within three recorded standard errors.
- The source-marker comparison gives correlation 0.99919.

## Why Main Fig. 3 Passes

- Both 41-point curves use the disclosed \(\Gamma=0.1\), \(H=0/Z\), and
  \(\epsilon=0:0.005:0.2\).
- Each fixed-retrieval solution is certified on all 1000 source times.
- Positivity, trace, signed-weight, diamond-error, monotonicity, and branch
  ordering checks all pass.
- Post-generation curve correlations are 0.99974 and 0.99998.

## Pixel Evidence

| Figure | Axis-bbox IoU | Ink overlap | Pixel score | Contract |
| --- | ---: | ---: | ---: | --- |
| Main Fig. 2 | 0.9872 | 0.6000 | 85.06 | passed |
| Main Fig. 3 | 0.9873 | 0.6193 | 86.38 | passed |

## T005 Author-Repair Status

- C06/C31 now execute the six paper maps with coefficients
  \((1,1,1,1,-1/2,-1/2)\), sampling overhead \(\kappa=5\), and program
  dimension 12.
- The reconstructed CNOT is checked on all 16 matrix units, and the resulting
  amplitude-damping channel is checked against its Kraus form at boundary and
  interior damping probabilities.
- This is author-side repair evidence only. T005 remains excluded from the
  scientific score until a different fresh-context reviewer adjudicates the
  rebuilt bundles; C05/C30 are outside this repair.

## Machine-Readable Record

`outputs/checks/similarity_scorecard.json`
