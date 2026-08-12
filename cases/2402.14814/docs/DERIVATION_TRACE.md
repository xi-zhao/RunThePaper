# Derivation trace

| Formula | Source | Independent derivation/check | Code |
| --- | --- | --- | --- |
| EQ001 | Supplement Eqs. S1-S2 | rotating-frame subtraction and LLL degeneracy | `model.py::ho_energy` |
| EQ002 | Supplement Eq. S3 | Laguerre normalization; LLL `k=0` reduction | `model.py::ho_density_2d` |
| EQ003 | Main Eqs. 1, 2a, 2b; Supplement S5-S9 | polynomial coordinate transform and coefficient norm | `model.py::laughlin_single_particle_density` |
| EQ004 | Main Fig. 2(d) caption | two-level observable with endpoints 2 and 0.5 | `model.py::rabi_occupation` |
| EQ005 | Main text after Fig. 4(c); Supplement angle derivation | independent numerical normalization and peak check | `model.py::angle_correlation` |
| EQ006 | Supplement Eqs. S10 and surrounding text | relative-only interaction and confined-delta root | `model.py::interaction_shift` |
| EQ007 | Supplement Eqs. S11-S12 and printed basis identities | Gaussian expansion, LLL moments, orthogonal basis transform | `model.py::two_particle_spectrum` |
| EQ008 | Supplement Eqs. S13-S14 | rotating-frame three-state unitary propagation | `model.py::driven_occupation` |
| EQ009 | Supplement Fig. S3 and time-evolution section | exact +/-2 coherent state and damped Ramsey envelope | `model.py::ramsey_occupation`, `evolving_relative_density` |
| EQ010 | Supplement Fig. S6 legends and imaging section | normalized Gaussian profiles with printed sigmas | `model.py::gaussian_profile` |

All formula checks precede any source-figure comparison. The scientific runner
has no path to `raw/`, `references/`, or authored figures.
