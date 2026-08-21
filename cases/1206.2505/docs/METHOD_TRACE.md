# Method Trace

| ID | Method | Inputs | Outputs | Independent checks |
| --- | --- | --- | --- | --- |
| NUM001 | dense momentum evaluation of Fisher lines/rates | printed quenches, EQ002-EQ005 | Fisher CSV, DQPT rate | analytic `k*`, half occupation, same-phase sign |
| NUM002 | monotone saddle inversion | printed work quench, EQ006-EQ007 | work curves/surface | normalization, nonnegativity, mean-work derivative, `w=0` identity |
| NUM003 | sparse exact-spin Krylov evolution | printed quenches, declared `N=12` | trajectories/postselection | Hermiticity and norm preservation |
| NUM004 | Majorana covariance plus pivoted Pfaffian | printed quenches, declared `N/r` grids | longitudinal correlations | exact-spin parity, antisymmetry, imaginary residual, three-size convergence |
| NUM005 | analytic sector and normalization audit | supplement formulas | Loschmidt matrix and formula-check CSVs | direct amplitude and partition identities |
| NUM006 | unitary midpoint ramp evolution | declared linear/smoothstep ramps | mode occupations | norm preservation, endpoint contrast, half-mode existence |

The implementations read no paper asset. Source figures are available only to
the separate renderer after generated data hashes are frozen.
