# Similarity Scorecard

## Case Result

- Overall score: **62.76/100**
- Level: `numerical_feature_reproduction`
- Scientific-region pixel mean: **46.9946/100**
- Full-canvas pixel mean: **88.1633/100**, layout diagnostic only
- Passed essential scientific targets: **8/9**
- Manual interventions in scientific data: **0**

The score uses the declared scientific foreground crop as the primary pixel
metric.  It does not reward source-image reuse: the source panels were available
only to the post-freeze RenderContract path.

## Target Scores

| Target | Feature | Pixel-derived closeness | Scope | Final score | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| T001 | 26/50 | 22.57/35 | 15/15 | 63.57 | feature reproduced |
| T002 | 34/50 | 11.75/35 | 15/15 | 60.75 | feature reproduced |
| T003 | 34/50 | 11.89/35 | 15/15 | 60.89 | feature reproduced |
| T004 | 42/50 | 17.42/35 | 15/15 | 70.00 | reduced-scale cap |
| T005 | 38/50 | 16.68/35 | 15/15 | 69.68 | feature reproduced |
| T006 | 30/50 | 17.64/35 | 15/15 | 62.64 | feature reproduced |
| T007 | 18/50 | 12.82/35 | 7.5/15 | 38.32 | feature failed |
| T008 | 36/50 | 18.02/35 | 15/15 | 69.02 | feature reproduced |
| T009 | 38/50 | 19.25/35 | 15/15 | 70.00 | reduced-scale cap |

T007 receives half panel-scope credit because the panel is fully rendered but
its joint generated-data asymptotic check fails.  All targets are capped at 70
because the executed parameters are reduced scale and the paper-scale A100
campaign is unrun.

## Interpretation

- `90-100`: complete reproduction, subject to lifecycle gates.
- `60-89`: numerical feature reproduction.
- `0-59`: feature not accepted.

The aggregate enters the feature-reproduction band, but it must not be read as
a strict lifecycle completion claim.  Atomic disposition is 8/9 reproduced and
1/9 attempted but not reproduced; paper-scale execution and fresh independent
review remain separate fidelity and lifecycle gaps.

The machine-readable authority for these numbers is
`outputs/checks/similarity_scorecard.json`.
