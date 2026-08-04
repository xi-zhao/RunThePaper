# Derivation Trace

## 1. Physical State Space — EQ001

Parity superselection sets the coherence `lambda` in the most general `2 x 2`
density matrix to zero. Therefore

```text
rho = (1-n) a a† + n a† a,                 0 <= n <= 1.
```

Using `y^(a†a)=1+(y-1)a†a` gives the Gaussian thermal form with
`exp(nu)=n/(1-n)` and `nu=-epsilon/T`. Solving for `n` yields

```text
n = 1 / (1 + exp(epsilon/T)).
```

This is Figure 1 directly. Its particle-hole identity `n(x)+n(-x)=1` explains
the positive/negative temperature symmetry and the `n=1/2` meeting point.

## 2. Coherent States And Phase-Space Supernumbers — EQ002

Expanding the nilpotent displacement operator terminates after
`alpha alpha*`. The characteristic-function Fourier transform and the coherent
state matrix elements give

```text
P = -n       + alpha alpha*
W = 1/2 - n  + alpha alpha*
Q = 1 - n    + alpha alpha*.
```

All three souls are identical and their coefficient is one, so each Berezin
integral is normalized. Only the bodies differ. Numerically, the code stores
those bodies; it does not pretend that a Grassmann variable is a float.

## 3. Majorization — EQ003

For `z=z_B+alpha alpha*`, nilpotency truncates an analytic functional:

```text
f(z) = f(z_B) + f'(z_B) alpha alpha*.
```

Berezin integration therefore returns `f'(z_B)`. Since `f` is concave,
`f'` decreases, so ordering the bodies proves the paper's complete
majorization chains. The numerical audit checks the body intervals and fixed
half-unit separations; no numerical optimizer is needed.

## 4. Covariance Determinants — EQ004

The fermionic covariance matrix is `gamma(z)=z_B sigma_y`. Because
`det(sigma_y)=-1`,

```text
det gamma(P) = -n^2
det gamma(W) = -(1/2-n)^2
det gamma(Q) = -(1-n)^2.
```

Their exact lower bounds are `-1`, `-1/4`, and `-1`. These three quadratics
generate Figure 2(a), including the exact crossings at `n=1/4,1/2,3/4`.

## 5. Rényi Entropies — EQ005 And EQ006

Nilpotency also gives

```text
int Dalpha |z|^r = r |z_B|^(r-1),
S_r(z) = ln(r)/(1-r) - ln|z_B|.
```

The continuous `r=1` limit is `S(z)=-1-ln|z_B|`. Maximizing the body
magnitude produces the exact uncertainty bounds. This one equation generates
all P/W/Q Shannon curves in Figure 2(b) and all five Wigner Rényi curves in
Figure 2(c). True zero-body singularities remain infinite in generated data.

## 6. Thermal Loss Channel — EQ007

Appendix B obtains the same result in the Fock and phase-space pictures:

```text
n_out = tau n_in + (1-tau) n_env.
```

For the frozen audit values `(n_in,tau,n_env)=(0.1,0.6,0.6)`, `n_out=0.3` and
`S_2(W_out)=ln(2.5)=0.9162907319`. This checks that the static formulas compose
correctly into the paper's Gaussian channel application.

## 7. Appendix A Scientific Audit

The single-mode no-cloning restriction is absent because the only physical
pure states, `|0>` and `|1>`, are orthogonal. A number measurement followed by
preparation therefore has fidelity one; diagonal mixed states can be
broadcast. The paper's separate no-go result for a *linear displacement-
covariant* cloner does not contradict the nonlinear fermionic CNOT
construction. This appendix has no numerical figure and is documented rather
than converted into an artificial plot.

## Gate And Code Pointers

- Machine-readable cards: `EQUATION_CARDS.json`.
- Generated formula narrative: `DERIVATION.md`.
- Gate: `outputs/checks/formula_verification.json` (`7/7` open).
- Implementation: `src/fermionic_phase_space.py`.
- Tests: `tests/test_fermionic_phase_space.py`.
- Full run: `scripts/run_reproduction.py`.
