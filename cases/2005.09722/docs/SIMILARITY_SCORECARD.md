# Similarity Scorecard

## Case Score

- Overall score: `69.53/100`
- Similarity level: `numerical_feature_reproduction`
- Coverage: `31/31` numerical axes
- Atomic final disposition: `120 reproduced / 1 externally_blocked / 0 attempted_not_reproduced / 0 pending`
- Lifecycle meaning: exploratory reduced-scale evidence; not paper-exact and not complete.

## Score Summary

| Target group | Targets | Score range | Main reason |
| --- | --- | ---: | --- |
| Entropy/CFT main results | T001-T008, T010 | 68-70 | key weak/strong-monitoring features present; smaller L |
| BKT transforms | T009, T011 | 64 | transform implemented, thermodynamic collapse not established |
| MI/correlation main results | T012-T017 | 66-70 | phase-discriminating features present; L and seeds differ |
| QJ/QSDc supplement | T018-T022 | 66-68 | protocol contrast present; smaller systems and ensembles |
| autocorrelation/density identity | T023-T024 | 64-69 | robust window trend and Wick identity pass; noisy far tail |
| random hopping | T025 | 68 | transition direction present at L=64 |
| trajectory histograms | T026-T031 | 62 | 192 trajectories capture coarse structure, not 5000-sample detail |
| no-display analytic claims | T033-T036 | 90 | independently checked analytic references; no pixel observable |

T032 is excluded from score aggregation and finalized as `externally_blocked`:
the publication does not disclose the numerical values and operational
criterion required to instantiate its crossover-length relation.

## Scoring Model

Each numerical axis receives feature match `/50`, numeric closeness `/35`, and paper-scope coverage `/15`. The harness then applies the strictest evidence cap. Every current target is capped by `parameter_match=reduced_scale` and uses `reference_comparison=source_figure_only`.

The 31 displayed numerical targets use `independent_numerics`; T033–T036 use independently checked `analytic_reference` evidence. Paper pixels are reference-only. The displayed stochastic curves still need a scientific-region render contract; the four no-display analytic claims are intrinsically `not_comparable` to pixels.

## What Prevents A Higher Score

- Run L=200-800 where specified by the paper.
- Increase histogram ensembles from 192 to 5000 and density-identity ensembles to at least 250+250.
- Declare and sensitivity-test all fit windows and trajectory counts that the paper leaves implicit.
- Compare paper-exact output to author data, digitized scientific curves, or a genuinely registered render.
- Obtain an independent fresh-context falsification review.

Machine-readable record: `outputs/checks/similarity_scorecard.json`.

Final-disposition evidence: `outputs/checks/final_disposition_evidence.json`.
