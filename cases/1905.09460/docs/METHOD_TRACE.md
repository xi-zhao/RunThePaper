# Method trace

| Target | Paper method | Independent implementation | Verification |
| --- | --- | --- | --- |
| T001 | Dense diagonalization of the `L=610` periodic AAH matrix; determinant winding | SciPy complex eigensolver on the matrix built directly from Eqs. (1)-(4); stable unwrapped determinant circle from S.2 | Hermitian limit, PT potential identity, Fourier-dual spectrum, `h_c=ln 2`, winding orientation |
| T002 | Time integration of laser Eqs. (8)-(9) after random-noise switch-on | Neutral-growth stationary-mode reduction of the same equations using all printed physical parameters | zero residual modal growth, normalized spectra, threshold `Delta_FM=2V0`; omitted transient settings disclosed |
| T003 | Dense diagonalization of the `L=500` open AAH matrix and edge-state counting | Same equation builder with only corner hoppings removed; boundary probability identifies left/right states | exactly 0 left and 3 right states at `h=0`, normalization and IPR bounds |
| T004 | Closed-form exact and first-order etalon transmission | Direct complex evaluation of Eqs. (S-27)-(S-29) | `R=0` limit, periodicity, recorded approximation error |

All source EPS/PNG files remain outside these methods.  They are read only by
the terminal comparison script after numerical generation is complete.
