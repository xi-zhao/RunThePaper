# Similarity Scorecard

## Case Score

- Overall score: generated from `outputs/checks/similarity_scorecard.json`.
- Similarity level: numerical feature reproduction.
- Interpretation: the central paper results reproduce with author-data-backed
  metrics; appendix mismatches and absent pixel registration cap the case.

## Figure Scores

| Figure | Weight | Feature | Numeric | Scope | Expected score |
| --- | ---: | ---: | ---: | ---: | ---: |
| Figure 5 | 2.0 | 46/50 | 30/35 | 15/15 | capped at 89 |
| Figure 6 | 2.0 | 45/50 | 26/35 | 15/15 | 86 |
| Figure 8 | 0.5 | 30/50 | 18/35 | 7.5/15 | 55.5 |
| Figure 9 | 0.5 | 38/50 | 22/35 | 7.5/15 | 67.5 |

The central figures receive four fifths of the weight because they carry the
paper's main claim. Appendix failures are scored independently and remain
visible rather than being averaged into one bundled target.

## Evaluation Metadata

All generated values use independent numerics and paper parameters. Author CSV
data are comparison-only. The artifact stage remains `exploratory`: exact
source solver/index conventions and registered source panels are unavailable,
so a high scientific score cannot be promoted to paper-exact presentation.

## What Prevents A Higher Score

- Figure 5 D and F are feature-level, not uniformly strict pointwise matches.
- Figure 6 has nonzero sorted TVD despite semantic fidelity agreement.
- Figure 8 curve E/F and distribution E are named numeric failures.
- Figure 9 distribution H is a named numeric failure.
- Figure 7 is blocked by conflicting Omega inputs.
- No registered source-panel pixel comparison exists.

## Machine-Readable Record

`outputs/checks/similarity_scorecard.json`
