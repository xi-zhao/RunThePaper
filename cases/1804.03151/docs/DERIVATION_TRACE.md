# Derivation Trace

## EQ001-EQ002: continuum Hamiltonian

The six first-shell Fourier components occur in conjugate pairs. With three
independent reciprocal vectors this gives
`Delta(r)=2V sum_j cos(b_j.r+psi)`. In a plane-wave basis, kinetic energy is
diagonal and a first-shell reciprocal displacement contributes `V exp(±i psi)`.
Complete hexagonal shells preserve inversion and C3 symmetry at every cutoff.

Numerical parameters are transcribed from the paper: `a0=0.332 nm`,
`m*=0.35 me`, `(V,psi)=(6.6 meV,-94 deg)` and `theta=2 deg`. This yields
`aM=9.511 nm`. Cutoffs 5 and 6 agree below `0.001 meV` on the reported path.

## EQ003: tight-binding coefficients

For each of the first three triangular-lattice neighbor shells, inversion pairs
reduce the dispersion to `2 t_n sum_R cos(k.R)`. A linear least-squares fit to
independently computed top-band energies returns the onsite offset and `t1,t2,t3`.
No points or parameters are read from the published curve.

## EQ004: Wannier function

At each sampled momentum, the highest-band eigenvector is phase aligned so its
value at a moire-potential maximum is real and positive. The discrete Bloch sum
then produces a localized orbital. Direct real-space quadrature normalizes it to
one; the target stores the amplitude and probability density.

## EQ005: interactions

Fourier transformation of the printed image-charge potential gives
`2*pi*e^2*(1-exp(-qD))/q`. Multiplying this kernel by the squared Fourier transform
of the Bloch-derived Wannier density and applying the phase for separations
`0`, `a1`, and `a1+a2` yields `epsilon U0,U1,U2`. This is a numerical projection
of the printed interaction, not a Gaussian surrogate. A harmonic helper is kept
only for an independent sanity estimate and is not used by target data.

## EQ006-EQ008: observables

The DOS is a declared Gaussian approximation to the delta functions over four
computed bands and includes the valley factor two. The full-hole density follows
from `2/A_M`. The printed `t/U` expressions map independently fitted hoppings and
projected `U0` to `J1,J2,J3`. The three-quarter-hole Fermi energy is the appropriate
quantile of computed top-band states inside the first Brillouin zone.

## EQ009: mismatch system

For aligned WSe2/MoS2, the supplement gives `aM=a0/delta` with `delta=0.039`,
so `aM=8.5128 nm`. The same derivation is rerun with `(V,psi)=(5.1 meV,-71 deg)`.
For finite twist the top axis follows `theta=sqrt((a0/aM)^2-delta^2)`.

## Formula-to-target map

| Formula | Targets |
| --- | --- |
| EQ001 | T001, T009 |
| EQ002 | T002-T004, T008, T010 |
| EQ003 | T002, T005-T007, T010-T012 |
| EQ004 | T004, T006, T012 |
| EQ005 | T006-T007, T012 |
| EQ006 | T003 |
| EQ007 | T007 |
| EQ008 | T008 |
| EQ009 | T009-T012 |
