# Derivation trace — 4D Z_N lattice gauge theory

## EQ001: Wilson action

For integer links `s_mu(x) in {0,...,N-1}`, define
`U_mu(x)=exp(2 pi i s_mu(x)/N)`. The oriented plaquette curl is

```text
r_{mu nu}(x) = s_mu(x) + s_nu(x+mu) - s_mu(x+nu) - s_nu(x).
```

Mapping this integer to `-N/2 < f <= N/2` leaves the Wilson phase unchanged.
The code evaluates `S_W=-beta sum_p cos(2 pi f_p/N)`. A cold field therefore
has action `-beta * 6 * L^4`, which is tested exactly up to floating precision.

## EQ002: modified Z4 action

The second harmonic is
`-beta_tilde sum_p cos(4 pi f_p/N)`. It shares the same plaquette field and is
included term-by-term in the local action delta. Random single-link proposals
are compared against a full-action recomputation in the unit tests.

## EQ003-EQ004: monopole suppression

Choose the principal representative `f=ds+N m`. Since `d^2 s=0`,
`df=N dm`; hence each oriented cube charge `q_c=(df)_c/N` is integer. The Z3
action adds `mu sum_c q_c^2`. The discrete Bianchi divisibility and a pure-gauge
single-link configuration are tested. Local deltas for the monopole action are
also checked against brute-force total-action differences.

## EQ005: action susceptibility

For generated action samples `S_i`, the estimator used for the plot anchor is

```text
chi_S = mean((S_i - mean(S))^2) / L^4.
```

This matches the paper's population variance definition. Error estimation and
autocorrelation control are method-level obligations; the current smoke result
is not accepted as the critical peak.

## EQ006: finite-torus Coulomb ratio

The paper's long-distance curve is

```text
C_asym(n) = K [n^-4 + (L-n)^-4].
```

The unknown K cancels in `C(n)/C(n+1)`. For L=16 and n=7 the independently
evaluated ratio is `1.1651254643492104`. This exact analytic curve is a valid
reference target, while the paper's Monte Carlo points remain a distinct open
target.

## Numerical gate conclusion

Every formula used by `src/zn_lgt.py` is source-traced and has either an exact
identity, limiting case, or local-versus-global action test. The formula gate is
open; remaining blockers are sampling scale and missing run metadata.
