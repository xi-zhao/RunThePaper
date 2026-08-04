# Derivation Trace

This trace records the independent reasoning that authorizes the numerical
implementation. `DERIVATION.md` is generated from the corresponding equation
cards.

## EQ001 — Finite-width Fresnel field

The aperture is the disjoint union
\[
[-d/2-a/2,-d/2+a/2]\cup[d/2-a/2,d/2+a/2].
\]
On that finite support the propagation kernel is continuous and bounded, so
the field is evaluated as the sum of two ordinary finite integrals. Expanding
the phase confirms that all retained terms are dimensionless. Global
source-independent Fresnel prefactors are omitted consistently and only set an
overall scale.

Independent checks: dimensional phase check; convergence under doubled
Gauss--Legendre order; conjugation-free direct evaluation on both slits.

## EQ002 — Differentiation under the integral

For \(q_t=x/W\) and \(q_f=(x/W)^2\), the finite aperture gives an integrable
parameter-independent bound. Dominated differentiation therefore yields
\[
\left.\partial_{\theta_\mu}E\right|_0
=i\int K(x,y)q_\mu(x)\,dx=iM_\mu(y).
\]
A central finite-difference derivative of the full perturbed field is an
independent numerical check, not the implementation used to create the scores.

## EQ003 — Exact local scores

From \(R=EE^*\),
\[
\partial_{\theta_\mu}R
=2\operatorname{Re}\!\left(E^*\partial_{\theta_\mu}E\right)
=2\operatorname{Re}(iE_0^*M_\mu)
=-2\operatorname{Im}(E_0^*M_\mu).
\]
This fixes the sign and shows why only the quadrature component changes
intensity at first order. In the point-slit limit \(q_f(\pm W)=1\), hence
\(M_f=E_0\) and \(g_f=0\), while \(q_t(\pm W)=\pm1\) remains differential.

Independent checks: finite-difference score agreement; real-valued output;
narrow-slit suppression of the defocus Fisher term.

## EQ004 — Full local Fisher information

With locally independent shot-noise samples and regularized variance density
\(N=R_0+B\), the linear response Jacobian is \(g_\mu\), giving
\[
F_{\mu\nu}^{\rm full}=\int g_\mu g_\nu/N\,dy.
\]
The matrix is a Gram matrix of \(g_\mu/\sqrt N\), hence it must be symmetric
positive semidefinite. This property is checked numerically.

## EQ005 — Optimized source codes

The Cauchy--Schwarz inequality in the \(N\)-weighted inner product makes
\(g_\mu/N\) the single-channel matched filter. Projecting first against the
constant nuisance mode and then against the already projected tilt direction
is ordinary Gram--Schmidt:
\[
\widetilde w_t=s_t-\frac{\langle s_t,1\rangle_N}{\langle1,1\rangle_N},\qquad
\widetilde w_f=s_f-\frac{\langle s_f,1\rangle_N}{\langle1,1\rangle_N}
-\frac{\langle s_f,\widetilde w_t\rangle_N}
{\langle\widetilde w_t,\widetilde w_t\rangle_N}\widetilde w_t .
\]
Normalization forces unit covariance and the three orthogonality residuals
must be near machine precision.

## EQ006 — Coded Fisher information and retention

Linear coded means have Jacobian \(G_{m\mu}=\int w_mg_\mu dy\), and their
covariance is \(\Sigma_{mn}=\langle w_m,w_n\rangle_N\). The Gaussian/local
Fisher form therefore gives \(F^{\rm code}=G^T\Sigma^{-1}G\).
Whitening by the symmetric eigendecomposition of \(F^{\rm full}\) makes the
retention eigenvalues basis independent. The projection theorem requires each
eigenvalue to lie in \([0,1]\), up to quadrature roundoff.

## EQ007 — Gaussian toy-code baseline

The toy coordinate uses the independently generated baseline:
\[
\xi=(y-\bar y)/\sigma_y,\quad
h_t^{(0)}=\xi,\quad h_f^{(0)}=(\xi^2-1)/\sqrt2.
\]
Applying the identical nuisance projection and normalization isolates the
effect of the subspace choice. Thus optimized-versus-toy retention compares
models, not normalization conventions.

## EQ008 — Finite-width defocus mechanism

Writing \(x=sW+u\) inside a slit gives
\[
q_f=1+2s(u/W)+(u/W)^2.
\]
The common term cannot change intensity to first order; only finite-\(u\)
variation contributes. Repeating the complete Fresnel and Fisher calculation
at \(a=\{20,40,80,150,250\}\,\mu{\rm m}\) yields the plotted ratio
\(\rho=F_{ff}^{\rm full}/F_{tt}^{\rm full}\). The direct narrow-slit limit and
monotonic growth are independent checks.

## Numerical Authorization

All eight cards have a source trace and at least one independent symbolic,
limiting-case, dimensional, normalization, or numerical-sanity check. No
source-only card is used. MTH001 specifies deterministic quadrature and
convergence checks. Therefore all five paper-exact targets may enter guarded
final execution.
