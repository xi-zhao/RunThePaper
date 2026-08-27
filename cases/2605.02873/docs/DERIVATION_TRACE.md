# Derivation Trace

This trace records the independent reasoning that opens the numerical gate for
arXiv:2605.02873v1. `DERIVATION.md` is generated from the equation cards and
must not be edited by hand.

## EQC001 - Finite aperture

Each `rect` term has unit support where its argument has magnitude at most
\(1/2\). The two supports are therefore
\([-d/2-a/2,-d/2+a/2]\) and
\([d/2-a/2,d/2+a/2]\). Splitting the integral into these intervals is exact
and avoids an arbitrary truncation of the slit-plane coordinate.

## EQC002 - Field and baseline

At \((\theta_t,\theta_f)=(0,0)\), the aberration factor is one. The remaining
kernel contains the two Fresnel phases and the finite aperture. Its modulus
square is real and nonnegative. Any omitted global propagation prefactor would
multiply all field moments by the same constant; it changes the absolute
intensity scale but not normalized panels or Fisher-retention ratios.

## EQC003 - Local response derivatives

For either generator \(q_\mu\),

\[
\partial_{\theta_\mu}e^{i\theta_\mu q_\mu}
=iq_\mu e^{i\theta_\mu q_\mu},
\]

so differentiation under the finite integral gives
\(\partial_{\theta_\mu}E|_0=iM_\mu\). Then

\[
\partial_{\theta_\mu}|E|^2
=2\operatorname{Re}\!\left(E^*\partial_{\theta_\mu}E\right)
=2\operatorname{Re}(iE_0^*M_\mu)
=-2\operatorname{Im}(E_0^*M_\mu).
\]

This checks the paper's sign and factor without fitting a plotted curve. In
the point-slit limit \(q_f(\pm W)=1\), hence \(M_f=E_0\) and \(g_f=0\);
\(q_t(\pm W)=\pm1\) remains differential.

## EQC004 - Full Fisher matrix

With \(s_\mu=g_\mu/N\),
\(\langle s_\mu,s_\nu\rangle_N=\int N(g_\mu/N)(g_\nu/N)dy\), which reduces
exactly to the full Fisher integral. Since \(B>0\), this is a positive
semidefinite Gram matrix and is safe to whiten when it is positive definite
for the paper geometry.

## EQC005 - Optimal codes

For any trial code \(w\), the squared local SNR is proportional to
\((\langle w,g/N\rangle_N)^2/\langle w,w\rangle_N\). Cauchy--Schwarz is
saturated by \(w\propto g/N\). The two explicit subtractions are ordinary
Gram--Schmidt in the same noise metric. Algebraically they impose

\[
\langle w_t,1\rangle_N=\langle w_f,1\rangle_N
=\langle w_t,w_f\rangle_N=0,\qquad
\|w_t\|_N=\|w_f\|_N=1.
\]

These four residuals will be checked numerically before Fig. 1(c) is accepted.

## EQC006 - Coded information and retention

The coded means change as \(G\theta\) and have covariance \(\Sigma\), so the
Gaussian/local Fisher expression is \(G^\mathsf{T}\Sigma^{-1}G\). Under a
nonsingular code-basis change \(A\), \(G\to AG\) and
\(\Sigma\to A\Sigma A^\mathsf{T}\); all \(A\) factors cancel. The result
depends only on the code subspace.

Whitening by the symmetric eigendecomposition of \(F^{\rm full}\) gives a
basis-independent retention matrix. Because the coded score directions are
orthogonal projections of the full directions, exact retention eigenvalues
cannot exceed one. Tiny excess from floating-point roundoff will be clipped
only for presentation, while raw values remain in the check artifact.

## EQC007 - Toy comparator

The toy coordinate is constructed from the independently generated \(R_0\),
not from a fitted Gaussian or the source image. Its odd/even templates are
processed with the identical nuisance projection and normalization used by the
optimized codes. Therefore the comparison isolates the missing
fringe-structured subspace instead of confounding it with different noise or
normalization rules.

## EQC008 - Finite-width origin

Writing \(x=sW+u\) shows

\[
(x/W)^2=1+2su/W+(u/W)^2.
\]

The constant term creates only a global phase. The remaining terms vanish as
the slit width shrinks, proving the narrow-slit suppression independently of
Fig. S1. The numerical width scan must rebuild all fields and Fisher matrices
at each of the five paper widths; Table S1 is withheld from generation and
used only afterward as an exact comparison.

## Numerical Translation and Verification Plan

- Gauss--Legendre quadrature is applied separately to each finite slit.
- A single source grid and trapezoidal weights are reused for all \(y\)
  integrals within a target.
- Higher-order slit quadrature and denser source grids provide convergence
  checks independent of the paper's reported values.
- Panel normalization is applied only after physical quantities are computed:
  \(R_0/\max R_0\), and \(g_t/\max|g_t|\),
  \(g_f/\max|g_f|\) separately.
- All source PNGs remain outside the numerical code path.

All eight cards have passed a source trace plus at least one independent
symbolic, limiting, normalization, dimensional, or sanity check. They are
eligible for `final_reproduction` readiness once the current generated
`DERIVATION.md` exists and the project parameter contracts validate.
