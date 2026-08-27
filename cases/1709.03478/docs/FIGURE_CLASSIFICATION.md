# Figure Classification

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 | `schematic_context` | No | No numerical data; conceptual CDW/phase schematic. |
| Main Fig. 2(a) | `experimental_measurement` | Excluded; reference for T002 | Laboratory FWHM traces require raw in-situ widths, calibration and SEM inputs. |
| Main Fig. 2(b) | `numeric_reproduction` | T002 | Edge-density dynamics from the continuum Hamiltonian. |
| Main Fig. 3(a) | `experimental_measurement` | Excluded; reference for T003 | Measured imbalance/expansion sweep at \(V_p=4\); shot data and fit inputs are unavailable. |
| Main Fig. 3(b) | `experimental_measurement` | Excluded; reference for T003 | Measured imbalance/expansion sweep at \(V_p=6\); shot data and fit inputs are unavailable. |
| Main Fig. 3(c) | `experimental_measurement` | Excluded; reference for T003 | Measured imbalance/expansion sweep at \(V_p=8\); shot data and fit inputs are unavailable. |
| Main Fig. 3(d) | `numeric_reproduction` | T003 | Continuum imbalance/edge-density sweep at \(V_p=4\). |
| Main Fig. 3(e) | `numeric_reproduction` | T003 | Continuum imbalance/edge-density sweep at \(V_p=6\). |
| Main Fig. 3(f) | `numeric_reproduction` | T003 | Continuum imbalance/edge-density sweep at \(V_p=8\). |
| Main Fig. 4 theory, main axes | `numeric_reproduction` | T004 | Tube-averaged 0.015-threshold boundaries derived from T003. |
| Main Fig. 4 theory, inset | `numeric_reproduction` | T004 | Central-tube 0.015-threshold boundaries derived from T003. |
| Main Fig. 4 experimental points | `experimental_measurement` | Excluded; reference for T004 | Experimental boundary-fit inputs and covariances are unavailable. |
| Supp. Fig. S1(a) | `numeric_reproduction` | T005 | FWHM traces without weak confinement. |
| Supp. Fig. S1(b) | `numeric_reproduction` | T005 | Edge-density traces without weak confinement. |
| Supp. Fig. S1(c) | `numeric_reproduction` | T005 | RMS cloud-size traces without weak confinement. |
| Supp. Fig. S1(d) | `numeric_reproduction` | T005 | FWHM traces with the stated weak trap. |
| Supp. Fig. S1(e) | `numeric_reproduction` | T005 | Edge-density traces with the stated weak trap. |
| Supp. Fig. S1(f) | `numeric_reproduction` | T005 | RMS cloud-size traces with the stated weak trap. |
| Supp. Fig. S2 theory | `numeric_reproduction` | T006 | 3000-tau theoretical imbalance/edge-density sweep at \(V_p=4\). |
| Supp. Fig. S2 experiment | `experimental_measurement` | Excluded; reference for T006 | Underlying 200-tau measurements, uncertainties and fit inputs are unavailable. |

The inventory contains 20 atomic displayed items: 13 independently calculable
theory items and 7 experimental/schematic items excluded from the theory
denominator.  The experimental rows remain visible as comparison evidence;
they are not deferred scientific-compute targets.  Machine-readable decisions
are in `figure_coverage.json`.
