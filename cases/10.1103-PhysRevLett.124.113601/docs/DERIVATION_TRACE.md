# Derivation Trace

## Causal chain

1. `EQ001-EQ002` define the AA/GAA eigenstates and their localization state.
2. `EQ003` converts an atomic density overlap into a steady cavity amplitude.
3. `EQ004` expresses the weak-field atomic response in the unperturbed
   eigenbasis.
4. `EQ005` closes the atomic and cavity responses and yields the finite
   superradiant threshold.
5. `EQ006` adds the resonant diagonal channel of a localized state, forcing the
   susceptibility to diverge and the threshold to zero.
6. `EQ007` resolves the same response into the momentum-space channels plotted
   in Fig. 3.
7. `EQ008` retains the nonlinear cavity potential and produces Fig. 4(a) and
   Fig. S1 by fixed-point continuation.

## Linear threshold derivation

Let `C_jj=cos(2*pi*gamma_c*j)` and let `|0>` be the unperturbed AA ground
state. In the normal extended phase `<0|C|0>=0`. The cavity perturbation is

```text
delta H = eta (a + a*) C.
```

First-order non-degenerate perturbation theory gives

```text
|delta psi> = -eta (a+a*) sum_{alpha>0}
              |alpha> <alpha|C|0> / (epsilon_alpha-epsilon_0).
```

Therefore the single-particle density overlap is

```text
Theta = <psi|C|psi>
      = -2 eta (a+a*) f1,
f1    = sum_{alpha>0} |<alpha|C|0>|^2/(epsilon_alpha-epsilon_0).
```

Writing the steady cavity response as

```text
a = eta N Theta / (barDelta_c + i kappa)
```

gives

```text
a+a* = 2 eta N Theta barDelta_c/(barDelta_c^2+kappa^2).
```

A nonzero solution requires

```text
1 = -4 eta^2 N f1 barDelta_c/(barDelta_c^2+kappa^2),
```

which is `EQ005`. Red effective detuning, `barDelta_c<0`, makes the threshold
real.

## Localized-state limit

For an extended state, a generic diagonal cavity overlap vanishes with system
size. For a state localized near `j_l`, however,

```text
<alpha|C|alpha> -> cos(2*pi*gamma_c*j_l).
```

The response then includes a diagonal transition with zero excitation energy.
Its susceptibility is resonant, so the thermodynamic threshold tends to zero.
At finite `L`, the implementation uses IPR to decide whether this self-channel
is physical; it does not promote a small open-boundary overlap of an extended
state into a false zero threshold.

## Source-convention discrepancy

The published Eq. (7) uses the literal one-factor shift
`barDelta_c=Delta_c-U N h0`, so that is the only convention used to generate
scientific arrays.  At the independently calculated clean response
`f1=0.361863...`, it gives `eta_c/J=0.206406`, while Fig. 3(a) gives `0.2768`.
An undeclared factor-two shift gives `0.276810` and likewise explains the
Fig. 4(b) midpoint.  That branch is retained solely in the post-freeze
falsification record; it is never tuned into the numerical runner.

## Nonlinear fixed point

For a normalized orbital `psi`, calculate `a(psi)` from `EQ003`, then solve the
ground state of

```text
H_eff = H_AA + 2 eta Re(a) C + U |a|^2 C^2.
```

Mix the old and new orbital/projector and iterate until both the cavity field
and density converge. The nonzero branch is followed by continuation from high
pump toward the threshold. This reproduces the physical state object, while
the solver tolerance and the under-specified Fig. S1 pump samples remain
disclosed case-local reconstruction choices.
