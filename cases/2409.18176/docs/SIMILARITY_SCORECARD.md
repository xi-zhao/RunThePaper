# Similarity Scorecard

## Case score

- Overall score: `53.55/100`
- Similarity level: `feature_not_accepted`
- Score model: formula/numerics first, frozen-source visual comparison second

The score does not reward copied or digitized source pixels.  Original panels
are read only after numerical arrays are attested and hash-frozen.

## Target scores

| Target | Feature /50 | Numeric /35 | Scope /15 | Effective score | Main boundary |
| --- | ---: | ---: | ---: | ---: | --- |
| T001 | 25 | 15 | 10 | 50 | proxy parameters |
| T002 | 35 | 16 | 12 | 63 | amplitude mismatch |
| T003 | 41 | 20 | 14 | 70 | source-only cap |
| T004 | 37 | 20 | 13 | 70 | source-only cap |
| T005 | 27 | 13 | 10 | 50 | phonon proxy |
| T006 | 24 | 10 | 7 | 41 | missing fitted densities; pending |
| T007 | 43 | 20 | 12 | 55 | missing fitted densities; pending |
| T008 | 24 | 10 | 7 | 41 | missing fitted densities; pending |
| T009 | 13 | 4 | 7 | 24 | paper-scale method convergence pending |
| T010 | 42 | 20 | 13 | 70 | source-only cap |
| T011 | 50 | 5 | 15 | 55 | formula limit implemented; absolute phonon calibration unavailable |

The effective scores include parameter, reference-evidence, formula, and
pending-science caps enforced by the Harness. A low score is not by itself a
paper-error verdict.

T011 is now an ordinary scored target.  It evaluates the paper-stated
`Delta/Delta_star -> infinity` limit directly, rather than guessing a finite
detuning or reading source pixels.  Whole-paper implementation coverage is
`30/30 = 100%`; the item-weighted fidelity is `53.01`, giving a reproduction
degree of `53.01` at evidence grade `E1`.

## Pixel status

`not_applicable`.  The source and generated panels do not yet share a
registered same-geometry scientific-region contract.  The boards in
`comparison-artifacts/` are diagnostic evidence, not raw-canvas pixel scores.

## Machine record

`outputs/checks/similarity_scorecard.json` contains component reasons,
parameter levels, critical roles, failure types, physics assertions, panel
coverage, and evidence links for all eleven targets.
