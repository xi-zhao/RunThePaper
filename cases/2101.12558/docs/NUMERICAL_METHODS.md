# Numerical Methods

## Feature validator

An inversion-symmetric layered p-d Hamiltonian is solved with an independent
Hubbard-I DMFT fixed point. Positive Matsubara frequencies determine layer
occupancies; the same final solution is evaluated on a retarded frequency
grid. Checks cover Hermiticity, inversion, convergence, self-energy causality,
nonnegative spectra, spectral weight, surface sensitivity, KMS reflection of
chi(tau), and the slab surface-energy formula.

## Paper-scale channel

Four atomic work units cover relaxed and bulk-terminated (001)/(110) slabs.
Each writes QE, pw2wannier90, Wannier90, CT-HYB, charge-feedback,
continuation, and observable contracts. Work units are shardable; completed
outputs bind the configuration hash, implementation hash, and output hashes.
The repository now owns the complete Wannier-Hamiltonian to observable path:
the printed three-/four-impurity layer symmetry, lattice Dyson projection,
inner DMFT fixed point, FLL update, eight-chain CT-HYB aggregation, direct
insertion sampling of both reconstructed $e_g$ moment correlators, MaxEnt/Pade
continuation, and layer/k projection. The outer charge loop is also internal.
Only the backend-specific operation that injects the computed correlated
density correction into a public plane-wave restart remains configurable.
Execution fails closed until that unpublished convention and the exact public
inputs are supplied; it is not replaced by a guessed density transformation.

The renderer is downstream of frozen NPZ data. It cannot change physical
parameters or numerical arrays.
