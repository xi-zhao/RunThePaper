# Method Trace

## MTH001 — complete-shell plane-wave diagonalization

- Source: main Eqs. (1)-(2)
- Inputs: moire period, effective mass, `V`, `psi`, reciprocal cutoff and k points
- Output: ordered continuum eigenvalues/eigenvectors
- Algorithm: enumerate a complete hexagonal reciprocal shell, assemble kinetic diagonal and conjugate first-shell links, call Hermitian eigensolver
- Checks: exact Hermiticity, reciprocal/direct duality, cutoff 5-to-6 convergence
- Code: `src/moire_hubbard/model.py::SingleBandContinuum`
- Status: verified

## MTH002 — Bloch-derived effective Hubbard parameters

- Source: Fig. 2 discussion, image-charge paragraph, main Eqs. (3)-(5)
- Inputs: independently diagonalized top band and its eigenvectors
- Output: `t1,t2,t3`, Wannier density and `epsilon U0,U1,U2`
- Algorithm: linear triangular-shell fit; smooth center gauge; discrete Bloch sum; FFT Coulomb convolution
- Checks: Wannier normalization, dominant `|t1|`, ordered interactions, positive exchange scale
- Code: `tight_binding_fit`, `wannier_amplitude`, `screened_interactions`
- Status: verified

## MTH003 — observables and sweeps

- Source: Figs. 2-4 and Supplement Fig. 5 captions
- Inputs: continuum eigenpairs and Hubbard parameters
- Output: DOS, density axes, exchange ratios, energy/Fermi contours and period sweeps
- Algorithm: declared k grids, Gaussian DOS broadening, printed exchange expansion and filling quantile
- Checks: reported bandwidths, density mapping and spin-liquid threshold
- Code: `src/moire_hubbard/reproduction.py`
- Status: verified

## MTH004 — post-freeze render comparison

- Source: visual contracts declared after scientific data freeze
- Inputs: hashed NPZ files and original figure panels
- Output: generated panels, comparison boards and pixel metrics
- Algorithm: verify every NPZ hash; render without changing arrays; compare predeclared scientific crops
- Checks: render-contract hash audit and harness-owned pixel evidence
- Code: `scripts/render_figures.py`, `scripts/build_comparisons.py`
- Status: pending final render pass
