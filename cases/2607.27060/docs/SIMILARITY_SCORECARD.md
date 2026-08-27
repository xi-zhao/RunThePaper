# Similarity Scorecard

## Result

- Scientific score: **90/100** for every one of the eight critical targets.
- Case score: **90/100**, `complete_reproduction` under the scorecard rules.
- Pixel-fidelity score: **100/100**, reported separately and never used to
  increase the scientific score.

## Why the Scientific Score Is 90

Each target earns the full raw component score:

- feature match: 50/50;
- numeric closeness: 35/35;
- paper-scope coverage: 15/15.

All target parameters are paper-exact, all generated data is independent, all
formula gates are verified, all 32 visible theory sequences are present, and
all threshold certificates pass.  The final score is capped at 90 because the
strict scientific comparator is the paper-derived analytic reference.  The
frozen source bundle deliberately excludes author result JSON, and source PNG
pixels are not digitised into numerical reference curves.

## Per-Target Status

| Target | Panel | Raw score | Evidence cap | Final score | Pixel score |
| --- | --- | ---: | ---: | ---: | ---: |
| T-FIG002A | Fig. 2a | 100 | 90 | 90 | 100 |
| T-FIG002B | Fig. 2b | 100 | 90 | 90 | 100 |
| T-FIG002C | Fig. 2c | 100 | 90 | 90 | 100 |
| T-FIG002D | Fig. 2d | 100 | 90 | 90 | 100 |
| T-FIG003A | Fig. 3a | 100 | 90 | 90 | 100 |
| T-FIG003B | Fig. 3b | 100 | 90 | 90 | 100 |
| T-FIG003C | Fig. 3c | 100 | 90 | 90 | 100 |
| T-FIG003D | Fig. 3d | 100 | 90 | 90 | 100 |

Machine-readable source: `outputs/checks/similarity_scorecard.json`.
