# Numerical Methods

| Method | Targets | Feature run | Paper-scale path | Principal risk |
| --- | --- | --- | --- | --- |
| Analytic quadrature/random matrices | T001–T002 | local CPU | larger seeded GOE ensemble | exact GOE convention in source plot unstated |
| Event-driven collision ensemble | T003–T005 | local vectorized CPU | sharded NumPy/CuPy ensemble with checkpoint/resume | withheld microscopic MD settings |
| Gaussian density/classical loss | T006 | local analytic | identical | absolute density during figure unstated |
| Absorbing radial ODE | T007–T017 | local SciPy CPU | denser energy grid with cached per-wave solutions | asymptotic matching and atom-dimer scale |
| Monte Carlo energy averaging | T007–T016 | local seeded batches | A100-capable sharded batches | withheld author distributions and f-wave parameters |

All stochastic outputs carry seed, configuration hash, implementation hash,
sample count, and convergence diagnostics.  Scientific arrays are frozen before
the source-image-aware RenderContract lane begins.
