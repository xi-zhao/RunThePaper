# Derivation Trace

The final executable target is the paper's analytic fidelity-response object,
with a separate reconstructed lane for direct Rydberg dynamics. This document
fixes both equation-to-code chains and prevents the diagnostic pulse from being
mistaken for the undisclosed Fig. 15 trajectory.

## D001: Infinite-Blockade Gate Dynamics (`EQ001`, `EQ002`)

Each atom has states `|0>`, `|1>`, and `|r>`. The laser couples `|1>` and
`|r>` globally. In the limit `B -> infinity`, the doubly excited state `|rr>`
is projected out, leaving an eight-dimensional Hilbert space. The ideal drive is

```text
H0(t) = Omega/2 * sum_i [exp(-i phi(t)) |1_i><r_i| + h.c.].
```

The cited primary implementation prints the generic time-optimal pulse

```text
phi(t) = A cos(omega t - phi0) + delta0 t,
A = 2*pi*0.1122,
omega = 1.0431 Omega,
phi0 = -0.7318,
delta0 = 0,
T = 2*pi*1.215/Omega.
```

The diagnostic implementation uses normalized units `Omega=1`. This changes
units, not the dimensionless diagnostic trajectory. The exact optimized phase
trajectory behind Fig. 15 is not printed in the current paper or source archive.
Hermiticity follows because every lowering term is paired with its Hermitian
conjugate.

## D002: Noise Operators (`EQ004`)

Frequency noise is expressed in Hz, so a fluctuation `delta_nu(t)` shifts each
Rydberg level by `-2*pi*delta_nu(t)`. Its operator is

```text
O_nu = -2*pi * sum_i |r_i><r_i|.
```

For relative intensity noise `h_I`, optical intensity changes the Rabi
amplitude as `delta Omega/Omega = h_I/2` to first order. Therefore

```text
O_I(t) = Omega/4 * sum_i [exp(-i phi(t)) |1_i><r_i| + h.c.].
```

Both are Hermitian. Their dimensions explain why frequency response carries
time squared while the intensity response is dimensionless.

## D003: Haar-Averaged Response (`EQ003`)

Along the ideal trajectory,

```text
O_H(t) = U(t)^dagger O(t) U(t).
```

For a `D`-dimensional input subspace with projector `P`, Appendix Eq. (G7)
gives the connected response averaged over Haar-random input states:

```text
I(f) = integral dt dtau cos[2*pi*f*(t-tau)] * {
  Tr[O_H(t) O_H(tau) P]/D
  - [Tr(O_H(t) P O_H(tau) P)
     + Tr(O_H(t)P) Tr(O_H(tau)P)]/[D(D+1)]
}.
```

The full-Haar projector spans `|00>, |01>, |10>, |11>` (`D=4`). The symmetric
projector spans `|00>, (|01>+|10>)/sqrt(2), |11>` (`D=3`).

## D004: Fourier Factorization (`EQ003`)

Define

```text
A(f) = integral_0^T exp(i*2*pi*f*t) O_H(t) dt.
```

Since `O_H(t)` is Hermitian, the double integral becomes

```text
I_avg(f) = Tr[A A^dagger P]/D
           - {Tr[A P A^dagger P] + |Tr[A P]|^2}/[D(D+1)].
```

Expanding `A` and `A^dagger` recovers the original cosine kernel; the sine part
vanishes because each displayed trace is real. This is an algebraic
factorization of Appendix Eq. (G7), not an alternative physical model.

## D005: Universal Scaling (`EQ005`)

Let `s=t/T`, with `T proportional to 1/Omega`. The frequency-noise operator is
independent of `Omega`, so two time integrals produce `Omega^-2`. The intensity
operator is proportional to `Omega`, canceling the two time factors. With
`x=2*pi*f/Omega`,

```text
I_nu(f; Omega) = Omega^-2 g_nu(x),
I_I(f; Omega) = g_I(x).
```

This is the collapse tested by `T002` at `3.0 MHz` and `7.7 MHz`.

## D006: Paper-Exact Analytic Target (`EQ006`)

Appendix L provides smooth six-parameter approximations for all four universal
curves. Because every coefficient is published, these functions generate the
final `T001` data and, through `EQ005`, the final `T002` data. Their provenance
is `analytic_reference`; they are paper-exact analytic reproductions rather
than independent numerical trajectories.

The direct diagnostic does not call these functions. It compares against them
after generation and exposes the missing-trajectory limitation: despite a
converged high-fidelity CZ, its response NRMSE is too large for a paper-exact
claim.

## Formula-Gate Acceptance Conditions

- all six formulas trace to this paper or the explicitly cited pulse source;
- the Hamiltonian and both noise operators are Hermitian;
- the Fourier form expands exactly to Appendix Eq. (G7);
- dimensions reproduce the paper's `Omega^-2` and `Omega^0` laws;
- final targets depend only on `EQ005-EQ006`;
- `EQ002` remains reconstructed and may feed only the exploratory diagnostic;
- numerical code is allowed only after the reusable formula gate reports all
  six cards open under their declared evidence level.
