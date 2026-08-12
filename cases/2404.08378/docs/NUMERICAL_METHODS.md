# Numerical Methods

## Core numerical model

The main quantum calculation is finite-dimensional and deterministic. `U_MZI(theta)` is evaluated directly and lifted to the two-boson Fock basis by creation-operator algebra. No optimization, figure fitting, random seed or author point array is involved. The surface grid uses 81 points per phase axis, cuts use 361 points, and all acceptance checks are evaluated from generated arrays.

## Device-mode reconstruction

The transverse scalar Helmholtz operator is discretized on a rectangular finite-difference grid with zero-field outer boundaries. The dominant guided eigenpair is found with SciPy sparse eigensolvers; intensity is normalized with the grid-cell area. Electrode loss is a declared perturbative overlap observable, not a replacement claim for the unpublished vector FEM.

Numerical risks are controlled by checking physical effective-index ordering, normalization and monotonic loss. Missing sidewall angle, material-dispersion table and vector boundary conditions remain parameter-provenance gaps rather than tuned constants.

## HOM, bandwidth and brightness

Reflectivity-dependent HOM visibility is computed from distinguishable and indistinguishable coincidence probabilities. Spectral weighting uses an explicit public-endpoint reconstruction and is labelled `proxy_model`. The 71.9 fs width is converted under more than one named convention so an unstated convention cannot silently enter the result. Brightness is direct two-photon loss correction and unit conversion.

## Two-lane execution contract

1. `scripts/run_reproduction.py` is the scientific numerical lane. Its isolated run can read only declared source code/configuration and cannot read `raw/`, references, the network or spawn subprocesses.
2. `scripts/render_frozen.py` is a post-freeze rendering lane. It verifies every generated-data hash before and after rendering.
3. `scripts/build_postfreeze_comparisons.py` may read published pages only after freezing. It creates source/reproduction boards but cannot modify physical parameters or numerical arrays.

This separation was enforced after the first attempted isolated run correctly blocked Matplotlib's font-discovery subprocesses. Rendering was removed from the runner instead of weakening isolation.

## Efficiency and reuse

- Runtime bottleneck: the two sparse scalar mode solves; still far below one second in the attested campaign.
- Complexity: exact Fock propagation is constant-size per grid point; scalar mode solve scales with sparse grid dimension.
- Optimization: one CPU thread is sufficient. GPU dispatch, sharding and checkpoints would add complexity without scientific value.
- Reusable pattern: frozen-array verification plus a separate RenderContract lane belongs in the Harness; optical models remain case-local.
