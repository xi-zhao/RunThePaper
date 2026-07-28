# Similarity Scorecard

## Case Score

- Overall score: `85/100`
- Similarity level: `numerical_feature_reproduction`
- Main Fig. 1: `80/100`, feature-level numerical reproduction
- Main Fig. 2: `90/100`, complete analytic reproduction

The score measures scientific and numerical agreement. Fonts, color choices,
line widths, and page composition are not treated as physics mismatches.

## Figure Scores

| Figure | Feature match | Numeric closeness | Scope coverage | Raw total | Evidence cap | Final |
| --- | --- | --- | --- | ---: | ---: | ---: |
| Main Fig. 1 numerical surfaces | `47/50` — sign topology and both theorem demonstrations present | `31/35` — all state-derived invariants pass; one source value is inconsistent | `13/15` — exact field, reconstructed 3D rendering | 91 | 80, reconstructed formula | 80 |
| Main Fig. 2 W-state panels | `50/50` — both fields, disk, and 19 points present | `35/35` — exact radius and eigenspectrum | `15/15` — both panels and both witnesses covered | 100 | 90, analytic reference | 90 |

## Evaluation Metadata

| Figure | Stage | Parameters | Data provenance | Formula gate | Physics status |
| --- | --- | --- | --- | --- | --- |
| Main Fig. 1 | exploratory | paper-exact state and kernel | independent numerics | reconstructed | passed |
| Main Fig. 2 | final reproduction | paper exact | analytic reference | verified | passed |

## Why The Case Is 85 Instead Of 100

- The source does not report the isosurface thresholds, mesh, or camera for its
  three-dimensional Fig. 1 rendering.
- More importantly, its printed Fig. 1 state implies a threshold numerator of
  52 while the End Matter prints 56. The independently integrated
  \(\mathcal N_{2D}\) clears the former and fails the latter.
- Main Fig. 2 has no corresponding ambiguity and reaches the analytic-reference
  cap of 90.

The normalized machine record is
`outputs/checks/similarity_scorecard.json`.
