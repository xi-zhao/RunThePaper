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
grid with 200 momentum samples. Fig. 2(d) independently computes all 317 printed
probe locations as sparse finite-OBC `log|det(H_L-E)|/N` values and independent
Eq. (10) targets. Three LU orderings provide an objective floating-stability
audit; unreliable large-size tail points remain visible and are not silently
discarded.

For Fig. 3, the generalized Brillouin-zone characteristic equations are solved
for a deterministic cover of 256 independently computed OBC energies per
geometry. Regular momentum grids are used for the beta-plane projections, and
periodic interpolation is used for the two three-dimensional surfaces.

For Fig. 4, the reciprocal critical model is evaluated through six distinct
checks: complete boundary density, scale-free Gaussian localization, spectral
density from the geometry-adaptive potential, boundary-ratio spectra, a
paper-size disordered spectrum, and finite-size spectral-potential scaling.

For Supplementary Fig. S2, Eq. (S18) separability turns the nominal `N=5625`
diagonalization into pairwise sums of two 75-state OBC spectra. Eqs. (S19)-(S22)
are evaluated from batched quartic roots and a 192-point arcsine quadrature.
The Amoeba potential uses a Jensen reduction of the inner momentum integral;
the two caption energies are classified from formula-generated zero loci and
integer torus winding, not source-image segmentation.

For Supplementary Fig. S4, Eq. (S24) is built directly under PBC and OBC. The
caption lengths `L=20,40,60,80` are diagonalized, both extremal-energy states
are inspected at `L=80`, and the central-state inverse localization length is
regressed against `1/L` over nine sizes. The additional `L=160` spectrum is a
declared large-size proxy, not an exact thermodynamic-limit curve.

For Supplementary Fig. S5, the printed Eq. (S27) is expanded into eight
directed hoppings. Exact OBC spectra are computed for the caption geometries
`N=6400/6385`. Normal A and scale-free B states are selected as the narrowest
and widest states in declared local shift-invert windows over 11 sizes, so the
choice is algorithmic and independent of source pixels. The two `101 x 161`
densities are obtained by evaluating Eq. (10) separately in the square and
rhombus cut bases. The differently parameterized legacy model in the author
release is not used as generated input.

For Supplementary Fig. S6, Eq. (S28) is evaluated as an unwrapped phase winding
on 240 midpoint slices with 4096 samples per loop. Midpoints avoid slices where
the point gap closes and the winding is undefined. Fermi points are solved from
the real and imaginary parts of the Bloch Hamiltonian, and their charges are
computed from the local Jacobian determinant.

For Supplementary Fig. S7, the clean OBC Hamiltonian is diagonalized with
paired left/right eigenvectors. The site-resolved kernel
`<L_i|n_j|R_i>/<L_i|R_i>` evaluates Eq. (S29) for 100 fresh `U[0,1]` onsite
samples at each of six paper sizes. Released curves and paper pixels are absent
from the generation path; author slopes are a separate post-generation
validation. The exact `r=43` diamond has 925 sites, exposing the caption's
printed `N=935` as a source discrepancy.

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
python scripts/run_fig2d_finite_size.py --scale smoke
python scripts/run_fig4_boundary_ratio.py --scale smoke
python scripts/run_supplementary_fig2.py --scale smoke
python scripts/run_supplementary_fig4.py
python scripts/run_supplementary_fig5.py --scale smoke --workers 4
python scripts/run_supplementary_fig6.py
python scripts/run_supplementary_fig7.py --scale paper
```

The first and third component scripts write relative to the code package when
called directly; the public quick runner redirects them to the case-level
output directories used by the catalog.
