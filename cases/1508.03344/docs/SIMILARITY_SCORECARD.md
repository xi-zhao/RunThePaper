# Similarity Scorecard

## Result

- Overall score: **72.86/100**.
- Level: `numerical_feature_reproduction`.
- Scientific checks: **12/12 passed**.
- Paper-exact target: T003 only.
- Reduced-scale targets: T001, T002, T004-T007.

| Target | Scientific-region pixel score | Result | Evidence cap / cause |
| --- | ---: | --- | --- |
| T001 | 89.3573 | accepted render; feature reproduced | 70, paper-scale compute not run |
| T002 | 85.3926 | accepted render; feature reproduced | 70, paper-scale compute not run |
| T003 | 95.8781 | high-fidelity, paper-exact analytic map | 90, analytic reference |
| T004 | 85.5990 | accepted render; feature reproduced | 70, paper-scale compute not run |
| T005 | 91.0185 | high-fidelity render; feature reproduced | 70, spectral definition underspecified |
| T006 | 85.8648 | accepted render; feature reproduced | 70, duration convention underspecified |
| T007 | not comparable | 12/12 quantitative checks | 70, paper-scale compute not run |

Scores compare complete predeclared scientific regions after numerical data was
frozen. Source pixels were not numerical inputs. Foreground-only/SSIM values
are secondary diagnostics; whole-canvas layout is not a completion gate. Render
tuning changed only axes, typography, line styles, palette and layout, and the
render manifest verifies that all five frozen data hashes remained unchanged.

The machine-readable schema-v4 record includes direct cause, root cause,
code-fault assessment, alternative hypotheses, affected scope and next test for
all six limited targets:
`outputs/checks/similarity_scorecard.json`.
