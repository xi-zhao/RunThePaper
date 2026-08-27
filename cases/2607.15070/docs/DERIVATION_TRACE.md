# Derivation Trace

This trace separates faithful reproduction of the plotted integrals from
validation of the field-theory derivation that precedes them.

## EQC001 - Radial operator

From the stated mass profile and separated Klein-Gordon equation,

\[
R''+\rho^{-1}R'
-\frac{l^2}{\rho^2}R-\alpha^2\rho^2R+\lambda R=0,
\qquad \lambda=\omega^2-m^2-k^2 .
\]

Set \(x=\alpha\rho^2\) and
\(R=\rho^{|l|}e^{-x/2}F(x)\). Direct differentiation gives

\[
xF''+(|l|+1-x)F'
+\left[\frac{\lambda}{4\alpha}-\frac{|l|+1}{2}\right]F=0.
\]

Polynomial termination at degree \(n\) therefore requires

\[
\lambda=2\alpha(2n+|l|+1).
\]

An especially short independent check is the ground state:
\(R=e^{-\alpha\rho^2/2}\) obeys
\([-\rho^{-1}\partial_\rho(\rho\partial_\rho)+\alpha^2\rho^2]R
=2\alpha R\). Paper Eq. (11) instead gives \(\lambda=\alpha\) for this
state. The difference is a real factor-two inconsistency, not a plotting
choice.

## EQC002-EQC003 - Conditional plotted objects

The numerical reproduction treats paper Eqs. (25) and (27) as the definitions
of the plotted, dimensionless boundary terms:

\[
\mathcal E_L=-\alpha_0\sum_{j\ge1}\int_0^\infty
\frac{\tau^{-3}e^{-m_0^2\tau^2-j^2/\tau^2}}
{\sinh(\alpha_0\tau^2)}\,d\tau ,
\]

\[
\mathcal E_c=-2\alpha_0\sum_{j\ge1}\int_0^\infty
\frac{\tau^{-3}e^{-m_0^2\tau^2-j^2/\tau^2}}
{\sinh(\alpha_0\tau^2)(e^{\alpha_0\tau^2}-1)}\,d\tau .
\]

After \(\tau\mapsto L\tau\), every denominator must contain
\(\alpha_0\tau^2\). The bare \(\alpha\tau^2\) in the first line of printed
Eq. (27) is dimensionally inconsistent and is treated as a notation typo.

## EQC004 - Independent Bessel representation

Use

\[
\frac1{\sinh x}=2\sum_{n=0}^\infty e^{-(2n+1)x},
\qquad
\frac1{\sinh x(e^x-1)}
=2\sum_{r=2}^\infty\left\lfloor\frac r2\right\rfloor e^{-rx},
\]

and

\[
\int_0^\infty \tau^{-3}e^{-a\tau^2-j^2/\tau^2}\,d\tau
=\frac{\sqrt a}{j}K_1(2j\sqrt a).
\]

This produces the two positive-term Bessel sums in EQC004. They are evaluated
at selected points as an independent check of the primary quadrature. Source
figure paths never enter either calculation.

## EQC005 - Small coupling

For the Landau-like term,
\(\alpha_0/\sinh(\alpha_0\tau^2)\to\tau^{-2}\), so

\[
\mathcal E_L\to-\sum_{j\ge1}\frac{m_0^2}{j^2}K_2(2jm_0).
\]

At \(m_0=0\), this is \(-\pi^4/180\).

For the additional term the product denominator starts at
\((\alpha_0\tau^2)^2\). The surviving integral is therefore proportional to
\(\tau^{-7}\), not \(\tau^{-5}\):

\[
\mathcal E_c\sim-\frac2{\alpha_0}
\sum_{j\ge1}\frac{m_0^3}{j^3}K_3(2jm_0).
\]

At \(m_0=0\), this is \(-2\zeta(6)/\alpha_0\). Paper Eq. (36) prints \(K_2\);
that result does not follow from its own denominator and would incorrectly
remove the mass dependence of the leading ratio.

## EQC006 - Strong coupling

The \(f=1\) and \(f=2\) leading terms reduce to

\[
2f\alpha_0\frac{\sqrt{m_0^2+f\alpha_0}}{j}
K_1\!\left(2j\sqrt{m_0^2+f\alpha_0}\right).
\]

With \(K_1(z)\sim\sqrt{\pi/(2z)}e^{-z}\), the exponent is
\(-2j\sqrt{m_0^2+f\alpha_0}\). The final line of paper Eq. (31) instead prints
\(-2jf\alpha_0\) and also uses the wrong leading power. The qualitative claim
of exponential suppression remains true; its printed asymptotic formula does
not.

## EQC007 - Ratio

Because both dimensionless energies carry the same overall normalization,

\[
E_0^{\rm ren}/E_L^{\rm ren}=1+\mathcal E_c/\mathcal E_L.
\]

The additional sector has \(f=2\) rather than \(f=1\) in the strong-coupling
exponent, so the ratio approaches unity.

## Equation-to-Code Map

| Card | Code |
| --- | --- |
| EQC001 | `src/casimir_effective_mass.py::radial_ground_eigenvalue` |
| EQC002 | `dimensionless_landau_energy` |
| EQC003 | `dimensionless_correction_energy` |
| EQC004 | `landau_energy_bessel`, `correction_energy_bessel` |
| EQC005 | `standard_landau_limit`, `correction_small_alpha_leading` |
| EQC006 | `strong_coupling_leading` |
| EQC007 | `energy_ratio` |

All cards are independently checked and may authorize final numerical
execution. “Verified” for EQC002-EQC003 means the displayed integrals and their
implementation are verified conditional objects; it is not a claim that the
paper's inconsistent Eq. (11) follows from the action.
