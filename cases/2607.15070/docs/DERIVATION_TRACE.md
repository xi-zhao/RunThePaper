# Derivation Trace

Use this file for formula-heavy papers. Every implemented equation should map
back to a source equation or an explicit derivation step.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until every dependency is independently checked.
`source_only` proves transcription, not understanding, and never authorizes a
numerical command. After generating `DERIVATION.md`, run the target through:

```bash
python private validation harness/scripts/run_target.py \
  case/<paper-id> <target-id> --stage exploratory -- python scripts/<runner>.py
```

## Equation Cards

### EQC001 - confined spectrum

- Source: paper Eqs. (2), (9)-(15).
- Chain: substitute `m_eff^2=m^2+alpha^2 rho^2` and the separated ansatz into
  the cylindrical Klein-Gordon equation. With `s=alpha rho^2/2`, regularity
  gives Kummer's equation. Polynomial termination at `-n` yields
  `omega^2=k^2+m^2+alpha(2n+|l|+1)`. Dirichlet plates replace
  `k` by `j*pi/L`.
- Independent checks: every term has mass dimension two; `alpha>0` is needed
  for normalizability; the nonrelativistic transverse energy spacing is
  harmonic-oscillator-like.
- Numerical role: establishes the mode labels and the sums from which the
  proper-time expressions are derived.

### EQC002 - Landau-like proper-time integral

- Source: paper Eq. (36).
- After the Mellin representation and Poisson resummation, retain only the
  boundary-induced `j>=1` images. With `tau -> L tau`,

  `Y_L = 8*pi^2*L^3*E_L^ren/A
       = -alpha_0 sum_j int_0^inf tau^-3
         exp(-m_0^2 tau^2-j^2/tau^2)/sinh(alpha_0 tau^2) d tau`.

- The integrand is negative only through the overall sign; its magnitude is
  positive and absolutely convergent for `alpha_0>0`.
- At `alpha_0 -> 0`, `alpha_0/sinh(alpha_0 tau^2) -> tau^-2`,
  recovering the standard massive Dirichlet-plate integral.

### EQC003 - additional proper-time integral

- Source: paper Eq. (37), derived from the `l>=1` sector.
- The dimensionless form is

  `Y_c = -2*alpha_0 sum_j int_0^inf tau^-3
         exp(-m_0^2 tau^2-j^2/tau^2)
         /[sinh(alpha_0 tau^2)(exp(alpha_0 tau^2)-1)] d tau`.

- The printed first denominator factor uses `alpha` after the variable change;
  dimensional consistency requires `alpha_0`. The implementation uses
  `alpha_0`.
- The second sum in paper Eq. (26) must start at `n=0`, not `n=1`, for this
  denominator to follow from the original mode sum.

### EQC004 - independent Bessel-series numerical form

Use

`1/sinh(x)=2 sum_(r>=0) exp[-(2r+1)x]`

and

`1/(exp(x)-1)=sum_(l>=1) exp(-l x)`.

The identity

`int_0^inf tau^-3 exp(-q^2 tau^2-j^2/tau^2) d tau
 = (q/j) K_1(2jq)`

then gives the positive magnitudes `S_L=-Y_L` and `S_c=-Y_c`:

`S_L = 2 alpha_0 sum_(j>=1,r>=0)
       q_r K_1(2j q_r)/j`,

`q_r^2=m_0^2+(2r+1)alpha_0`,

and, after grouping `k=2r+l+1`,

`S_c = 4 alpha_0 sum_(j>=1,k>=2)
       floor(k/2) q_k K_1(2j q_k)/j`,

`q_k^2=m_0^2+k alpha_0`.

All terms are positive. Truncation is therefore monotone and can be bounded
by the exponentially decaying Bessel tail. The production path evaluates
these series; an adaptive log-coordinate quadrature of EQC002-EQC003 is an
independent method check.

### EQC005 - small-coupling limits

For the Landau sector,

`S_L -> sum_(j>=1) m_0^2 K_2(2jm_0)/j^2`,

with massless value `zeta(4)/2=pi^4/180`.

For the correction sector, direct expansion of both denominator factors gives
an extra `tau^-2` relative to the Landau sector:

`S_c ~ (2/alpha_0) sum_(j>=1) m_0^3 K_3(2jm_0)/j^3`.

For `m_0=0`, this is `2 zeta(6)/alpha_0`. The paper's Eq. (42) instead repeats
the `K_2` Landau integral. That expression does not follow from Eq. (37) and
is not used. The plotted qualitative claim - a singular correction sector -
remains correct.

### EQC006 - large-coupling limits

The leading denominator exponent is indexed by `f=1` for `S_L` and `f=2` for
`S_c`:

`S_f ~ 2 f alpha_0 sqrt(m_0^2+f alpha_0)
       K_1(2j sqrt(m_0^2+f alpha_0))/j`, with `j=1` dominant.

Thus the suppression is
`exp[-2j sqrt(m_0^2+f alpha_0)]`, not
`exp[-2jf alpha_0]` as printed in the last line of paper Eq. (39).
The correction sector has the larger exponent and becomes negligible relative
to the Landau sector.

### EQC007 - ratio observable

Because `E_0^ren=E_L^ren+E_c^ren` and both contributions share the same
negative prefactor,

`R=E_0^ren/E_L^ren=1+S_c/S_L`.

Positivity of both series gives `R>1`; EQC006 gives `R -> 1` at large
`alpha_0`.

## Gate Outcome

Every numerical dependency has a source trace and at least one independent
symbolic, limiting, dimensional, or numerical check. The corrected identities
above, rather than the inconsistent printed asymptotic substeps, define the
verified numerical forms.
