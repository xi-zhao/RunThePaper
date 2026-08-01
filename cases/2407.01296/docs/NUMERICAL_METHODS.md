# Numerical methods

## Core model

The reproduction separates the hopping model from the finite geometry. A
geometry is an explicit set of integer lattice sites; open boundaries retain a
hopping only when both endpoints belong to that set. This makes square,
rhombic, and ratio-controlled cuts different boundary conditions on the same
Hamiltonian rather than separate ad-hoc models.

For Fig. 2, Eq. (11) is evaluated on a 40-by-40 square (`N=1600`) and a radius-30
rhombus (`N=1861`). Complete right eigensystems provide the complex spectra and
aggregate right-eigenvector density. The geometry-adaptive potential uses the
minimum of two cylindrical root potentials on the paper's `101 x 101` energy
grid with 200 momentum samples.

For Fig. 3, the generalized Brillouin-zone characteristic equations are solved
for a deterministic cover of 256 independently computed OBC energies per
geometry. Regular momentum grids are used for the beta-plane projections, and
periodic interpolation is used for the two three-dimensional surfaces.

For Fig. 4, the reciprocal critical model is evaluated through six distinct
checks: complete boundary density, scale-free Gaussian localization, spectral
density from the geometry-adaptive potential, boundary-ratio spectra, a
paper-size disordered spectrum, and finite-size spectral-potential scaling.

For Supplementary Fig. S4, Eq. (S24) is built directly under PBC and OBC. The
caption lengths `L=20,40,60,80` are diagonalized, both extremal-energy states
are inspected at `L=80`, and the central-state inverse localization length is
regressed against `1/L` over nine sizes. The additional `L=160` spectrum is a
declared large-size proxy, not an exact thermodynamic-limit curve.

For Supplementary Fig. S6, Eq. (S28) is evaluated as an unwrapped phase winding
on 240 midpoint slices with 4096 samples per loop. Midpoints avoid slices where
the point gap closes and the winding is undefined. Fermi points are solved from
the real and imaginary parts of the Bloch Hamiltonian, and their charges are
computed from the local Jacobian determinant.

## Reproducibility layers

The public quick runner uses reduced matrices so it can execute on an ordinary
laptop. It exercises the same site-set, Hamiltonian, spectrum, density, and
symmetry logic as the paper-scale calculations. The published paper-scale CSV,
NPZ, PNG, and JSON artifacts are the durable record of the expensive runs.

Pixel registration is an audit layer after numerical computation. It fixes the
canvas dimensions and layout but does not alter the generated numerical arrays.
The public package omits source-publication assets required to rerun that audit;
only limited attributed comparison boards and the resulting metrics are kept.

## Commands

```bash
cd cases/2407.01296/code
python scripts/run_reproduction_smoke.py
```

The component runners are also available:

```bash
python scripts/run_fig2_geometry.py --scale smoke
python scripts/run_fig2_potential.py --scale smoke --output-root ../outputs
python scripts/run_fig4_boundary_ratio.py --scale smoke
python scripts/run_supplementary_fig4.py
python scripts/run_supplementary_fig6.py
```

The first and third component scripts write relative to the code package when
called directly; the public quick runner redirects them to the case-level
output directories used by the catalog.
