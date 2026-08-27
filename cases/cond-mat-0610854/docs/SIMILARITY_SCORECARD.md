# Similarity Scorecard

The auditable machine scorecard is
`outputs/checks/similarity_scorecard.json`.

| Target | Primary scientific-region pixel score | Evidence score | Reason for cap |
| --- | ---: | ---: | --- |
| T001 Main Fig. 1 | 95.7100 | 70 | paper-scale L=16/GOE campaign not run |
| T002 Main Fig. 2 top | 94.7262 | 70 | L=16 and production statistics not run |
| T003 Main Fig. 2 bottom | 96.2829 | 70 | L=16 and production statistics not run |
| T004 crossing drift | not applicable | 70 | exact source grid/sample counts unavailable |

Overall score: **70/100, numerical feature reproduction**.  The direct pixel
metric is primary for rendered scientific regions, but scientific provenance,
parameter scale and execution evidence remain hard caps.  Full-canvas SSIM is
kept only as a layout diagnostic and is not used as the scientific score.
