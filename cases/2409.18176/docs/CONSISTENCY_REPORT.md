# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| feature_match | 4 | T003, T004, and T010 reproduce their declared scientific features; T002 reproduces the resonance feature but still awaits quantitative convergence. |
| proxy_partial | 2 | T001 and T005 are runnable, but indispensable sign/linewidth or phonon calibration is absent. |
| pending | 4 | T006--T008 lack the fitted operating densities; T009 awaits the full multi-method convergence campaign. |
| non_numeric_excluded | 4 | Device/process sketches and the diagrammatic figure are contextual only. |

All eleven numerical targets are generated from formulas.  The isolated runs
are attested and the post-freeze comparison lane proves that original pixels did
not modify any CSV.  The current target score is `53.55/100`; this case is
honestly classified partial.  The historical score records the frozen feature
run; it is not evidence that the unresolved targets are scientific failures.

## Per-target consistency

| Target | Paper item | Level | Main evidence | Remaining difference |
| --- | --- | --- | --- | --- |
| T001 | Main Fig. 1(b), right | proxy_partial | three printed sign conventions evaluated | sign, linewidth, and plotting parameters are incomplete |
| T002 | Main Fig. 1(c) | pending | peak at `0.6175`; four series present | paper-scale quantitative convergence unexecuted; peak height remains low |
| T003 | Main Fig. 2 | feature_match | drag changes sign across resonance | detailed amplitudes differ |
| T004 | Main Fig. 3 main | feature_match | nonmonotonic temperature curves | peak positions/amplitudes differ |
| T005 | Main Fig. 3 inset | proxy_partial | many-body plus Bloch--Grüneisen crossover | absolute phonon calibration omitted by paper |
| T006 | Main Fig. 4(a) | pending | direct/corrected three-fluid parity passes | fit-point species densities are not printed; reconstructed closure leaves gap `0.404613` |
| T007 | Main Fig. 4(b) | pending | reconstructed curves have gap `0.021102` | same missing fit-point densities prevent paper-exact promotion |
| T008 | Main Fig. 4(c) | pending | both complex responses generated | same missing fit-point densities; reconstructed closure leaves gap `0.190012` |
| T009 | Supplement Fig. 6 | pending | direct and Schur-eliminated full Boltzmann lanes plus two leading-order regularizations are implemented | frozen paper-scale convergence is unexecuted; feature-run gap `11.277640` is not attributed to the paper |
| T011 | Main Fig. 3 inset, dash-dot | proxy_partial | asymptotic Drude-plus-phonon identity passes in an isolated run | absolute acoustic-phonon calibration is not printed |
| T010 | Supplement Fig. 7 | feature_match | positive trion drag and all three series | peak position/amplitude differs |

## Paper audit

The source has two formal audit leads and one reproduction discrepancy.  None
is promoted to a paper error without fresh-context review:

- the vacuum T-matrix sign/linewidth convention is incomplete;
- the supplemental three-fluid closed form appears dimensionally inconsistent
  with the main velocity equations;
- the Kubo/Boltzmann difference is far too large in the feature run, but the
  complete full/leading-order method split, production convergence, and fresh
  review are not complete.

See `PAPER_REVIEW_PROTOCOL_V2.md` and
`outputs/checks/paper_consistency_checks.json`.
