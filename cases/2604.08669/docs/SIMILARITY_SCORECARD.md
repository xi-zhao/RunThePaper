# Similarity scorecard

This scorecard is intentionally conservative. The case has started a two-stage reproduction and now treats Fig. 3 as a retrained model artifact, but it has not reached paper-scale.

| Target | Current level | Main cap |
| --- | --- | --- |
| T001 / Fig. 3 | Reduced retrained-model reproduction | small lattices, small dataset, CPU decoder only |
| T002 / Fig. 4 | Reduced numeric reproduction | small grid, few stochastic samples, no Zhuifeng source |
| T003 / Fig. 5 | Timing model reproduction | analytic model only, no GPU timing campaign |
| T004 / Fig. 3-5 interface | Software assembly reproduction plus sweep | reduced scale, local timing only |

The normalized scorecard lives at `outputs/checks/similarity_scorecard.json`.
