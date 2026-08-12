# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| `paper_exact_model` | 12 | Printed equation/trend is independently reproduced at the declared parameters. |
| `feature_or_subset` | 3 | Printed scalars/features match but point arrays or conventions are incomplete. |
| `proxy_model` | 3 | Transparent independent reconstruction replaces unpublished solver/spectral details. |
| `missing_author_data` | 9 items | Exact experimental arrays are unavailable and are not digitized. |
| `non_numeric` | 4 items | Schematics or microscopy, intentionally excluded. |

## Per-Target Consistency

| Targets | Level | Main evidence | Remaining boundary |
| --- | --- | --- | --- |
| T002–T008 | `paper_exact_model` | MZI unitarity, Fock-lift unitarity, normalized surfaces, bunch/antibunch limits | measured powers/coincidences unavailable |
| T010–T013 | `paper_exact_model` | Supplement Eqs. (1)-(2), physical density matrices | none for the theory curves |
| T015 | `paper_exact_model` | exact 3.010 dB and printed 0.25 dB excess trends | measured camera points unavailable |
| T001 | `proxy_model` | guided normalized modes at both wavelengths | vector FEM mesh/material details absent |
| T009 | `feature_or_subset` | printed 0.832 visibility and 71.9 fs width | coincidence array and width convention absent |
| T014 | `proxy_model` | exact HOM functional; LNOI ordering recovered | measured reflectivity/grating spectra absent |
| T016 | `proxy_model` | monotonic evanescent-overlap loss | unpublished vector FEM absent |
| T017–T018 | `feature_or_subset` | brightness and bandwidth arithmetic | rounded inputs and convention ambiguity |

## Review Observations

- Brightness arithmetic closes at `2.309021589e8 pairs/s/mW`.
- Dividing this by the printed normalized brightness `7.7e6` implies `29.99 nm`, whereas another paragraph describes an approximately `50 nm` photon bandwidth.
- A 71.9 fs Gaussian width gives `49.92 nm` under the 0.441 pulse convention and `70.64 nm` under an HOM-autocorrelation convention.
- These are explicit `inconclusive` convention/rounding observations. No paper-error candidate is emitted without protocol-v2 fresh review.
