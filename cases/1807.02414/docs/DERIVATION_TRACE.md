# Derivation Trace

## From the paper to the numerical object

1. Set `gamma=pi/ell`, enumerate the `ell` root-of-unity strings, and build the
   bare density/scattering kernels (EQ001).
2. Solve the infinite-temperature Y-system constants (EQ002).
3. Discretize the TBA equation and dress the energy derivative to obtain
   positive densities and odd effective velocities (EQ003).
4. Use the normalized spin susceptibility density to propagate the weak wall
   along each velocity, producing the three Euler curves (EQ004).
5. Dress the two-body scattering kernel and evaluate the positive double
   integral for `(D C)_SzSz` (EQ005-EQ006).
6. Project the full spectral diffusion operator onto the conserved spin mode,
   `D_spin=(D C)_zz/chi`, and broaden each Euler contact with the heat kernel
   implied by the factor `1/2` in Eq. (13) (EQ007).
7. Build the complete non-diagonal `D_tilde` kernel from the independently
   dressed scattering matrix, solve Eq. (13) for the full species/rapidity
   perturbation with Fourier-space Strang splitting, and project the evolved
   occupation response back to magnetization (EQ009).
8. For the independent tDMRG markers, factor the printed product density matrix
   as a product purification `|sqrt(rho_0)>`, group each physical spin with its
   inert ancilla, and evolve the physical legs with a second-order even/odd
   TEBD decomposition of the printed XXZ bond Hamiltonian (EQ008). Retain only
   the three requested magnetization snapshots; certify dt, bond, and
   finite-size convergence before treating them as reproduced markers.

## Important convention checks

- The final string has negative parity and negative rapidity orientation.
- `h^dr=ell/2` only for the final two boundary strings at zero field.
- The computed susceptibility converges to `chi=1/4` for ell=3,4,7.
- The charged-mode maximum speed at ell=7 is `0.43388365`, giving the paper's
  light-cone scale without fitting a curve coordinate.
- The projected heat-kernel denominator is `sqrt(2 D_spin t)` because the
  paper writes `partial_t n = (1/2) D partial_x^2 n`.

## Scope boundary

EQ007 remains the already-run reduced projection and is not relabelled as the
full operator solution. EQ009 supplies a distinct code-ready paper-scale lane
for the complete operator; its four final convergence variants are not claimed
as executed. T003 is also independently implemented rather than left as a
prose plan; its paper-time computation remains honestly deferred.
