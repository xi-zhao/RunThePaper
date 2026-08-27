# Target ledger

| Targets | Scope | Evidence | Parameter status |
| --- | --- | --- | --- |
| T001-T005 | exact model, classical map, minima, harmonic and WKB identities | formula_checks.csv | paper_exact |
| T006-T007 | separatrix scaling and Main Fig. 1 | fig1_spacing_*.csv | mixed: unpublished grid/selector |
| T008-T010 | critical k and N exponents, Main Fig. 2 | fig2_critical_spectrum.csv; critical_n_scaling.csv | paper_exact |
| T011-T012 | super-scar weights and indices | super_scar_checks.csv | mixed: unpublished N values |
| T013 | tunnelling | tunneling_checks.csv | paper_exact |
| T014 | energy-resolved normal-phase spacing | normal_spacing_profile.csv | paper statement lacks the intended energy interval |
| T015 | outlined Eq. (16) method | derivation evidence | publication underspecified |
| T016 | threshold excitation | formula_checks.csv | paper_exact |
| T017 | self-adjoint coordinate-ordering comparison | ordering_comparison.csv | two explicit reconstructions; author ordering unavailable |
| T018-T020 | complex-lambda exceptional-point claims | exceptional_points.csv; exceptional_point_summary.csv | finite-size feature campaign; no author root inventory or N-to-infinity proof |

All targets have runnable code and the configured finite campaigns have been
executed. No target is deferred for compute. T017-T020 remain evidence-limited
because the paper does not define a unique ordering or publish an exceptional-
point dataset; this is not represented as a code or compute failure.
