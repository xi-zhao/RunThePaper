# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| feature_match | 5 | T002--T004, T007, and T010 reproduce their declared scientific features. |
| proxy_partial | 2 | T001 and T005 are runnable, but indispensable sign/linewidth or phonon calibration is absent. |
| failed | 3 | T006, T008, and T009 fail paper-level scientific comparisons. |
| non_numeric_excluded | 4 | Device/process sketches and the diagrammatic figure are contextual only. |

All ten numerical targets are generated from formulas.  The isolated run is
attested and the post-freeze comparison lane proves that original pixels did
not modify any CSV.  The aggregate score is `54.90/100`, so this case is
honestly classified `feature_not_accepted`.

## Per-target consistency

| Target | Paper item | Level | Main evidence | Remaining difference |
| --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(b), right | proxy_partial | three printed sign conventions evaluated | sign, linewidth, and plotting parameters are incomplete |
| T002 | Main Fig. 1(c) | feature_match | peak at `0.6175`; four series present | peak height `3.17` versus paper's visibly larger curve |
| T003 | Main Fig. 2 | feature_match | drag changes sign across resonance | detailed amplitudes differ |
| T004 | Main Fig. 3 main | feature_match | nonmonotonic temperature curves | peak positions/amplitudes differ |
| T005 | Main Fig. 3 inset | proxy_partial | many-body plus Bloch--Grüneisen crossover | absolute phonon calibration omitted by paper |
| T006 | Main Fig. 4(a) | failed | analytic three-fluid parity passes | kinetic/fit gap `0.404613` |
| T007 | Main Fig. 4(b) | feature_match | kinetic/fit gap `0.021102` | fine line-shape difference |
| T008 | Main Fig. 4(c) | failed | both complex responses generated | kinetic/fit gap `0.190012` |
| T009 | Supplement Fig. 6 | failed | two independent numerical lanes | max difference `11.277640`, not a few percent |
| T010 | Supplement Fig. 7 | feature_match | positive trion drag and all three series | peak position/amplitude differs |

## Paper audit

The source has two formal audit leads and one reproduction discrepancy.  None
is promoted to a paper error without fresh-context review:

- the vacuum T-matrix sign/linewidth convention is incomplete;
- the supplemental three-fluid closed form appears dimensionally inconsistent
  with the main velocity equations;
- the Kubo/Boltzmann difference is far too large in our independent run, but
  unprinted numerical choices and remaining method gaps have not been excluded.

See `PAPER_REVIEW_PROTOCOL_V2.md` and
`outputs/checks/paper_consistency_checks.json`.
