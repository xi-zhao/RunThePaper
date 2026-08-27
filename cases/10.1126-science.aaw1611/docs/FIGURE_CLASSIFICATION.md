# Figure Classification

The full article and supplement are inventoried at panel level in `figure_coverage.json`.

| Class | Count | Treatment |
| --- | ---: | --- |
| Theoretical numerical target | 38 | Independently generated from formulas/model and scored atomically |
| Experimental numerical measurement | 41 | Excluded from the numerical runner; may serve as contextual reference only |
| Source parameter table | 1 | Table S1 supplies declared parameters but is not counted as a reproduced result |
| Non-numeric figure/panel | 12 | Excluded from the reproduction denominator |

## Included target families

| Family | Paper items | Atomic targets | Status |
| --- | --- | ---: | --- |
| One-photon density | Main Fig. 2D-F; S14B-S16B | 6 | generated and checked |
| Information spreading | Main Fig. 3C theory; S12; S17B | 3 | generated and checked |
| Two-photon theory | S18B; S19B-C; S20H-S | 15 | generated; S20 printed-time comparison unresolved |
| Double occupancy | S8 | 1 | generated and threshold checked |
| Disorder ensembles | S9A-F; S10A-F | 12 | 50-sequence paper-declared ensembles generated and checked |
| Coupling precision | S11 | 1 | method-level reconstruction; exact author realization unavailable |

Mixed paper figures are split: experimental pixels/points are excluded while independently computable theory regions are represented by their own target. No source pixels or digitized values enter the scientific numerical runner.
