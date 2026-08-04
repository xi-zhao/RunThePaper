# Corrected derivation

Let (s=|k|^2), (q=\hat G(k)=e^{-σ^2s/2}), and (M_0=ρ_0(1-ρ_0)). Linearization of the source chemical potential gives

$$
\lambda(k)=-|k|^2\left[T-M_0\left((1+\alpha)u'\hat G(k)+\alpha\rho_0u''\hat G(k)^2\right)\right].
$$

\[
\delta\mu_k=\left[\frac{T}{M_0}-(1+\alpha)u' q-\alpha\rho_0u''q^2\right]\delta\rho_k,
\]

and therefore

\[
\lambda(k)=-s\left[T-M_0\{(1+\alpha)u'q+\alpha\rho_0u''q^2\}\right].
\]

## Task 1

In the unstable density sector (ρ_0<1/2), the discrete critical temperature is the attained maximum

\[
T_c=\max_{k\in(2\pi/L)\mathbb Z^d\setminus\{0\}}M_0\left[(1+\alpha)u'q+\alpha\rho_0u''q^2\right].
\]

For (ρ_0>1/2), both (u') and (u'') are negative. Every finite-mode contribution is negative and the sequence tends to zero from below as (|k|\to\infty). Hence the displayed `max` does not exist. The nonnegative critical-temperature convention uses the supremum (T_c=0); if the problem insists on (T>0), only the infimum is zero.

## Task 2

For ((α,σ,L,ρ_0)=(0.6,10,1000,0.37)), the destabilizing term is a concave quadratic (D(q)=M_0(aq+bq^2)). Its continuum vertex corresponds to the real shell

\[
m_{\rm cont}=32.99995598798843.
\]

Because (q) is monotone in the integer shell (m=n_x^2+n_y^2), the discrete maximum is bracketed by representable shells on either side. The guaranteed representable axis shell \(\lceil\sqrt{m_{\rm cont}}\rceil^2=36\) is therefore a rigorous finite upper bound. Searching every lattice mode with (m\le36) gives

\[
m_*=34,\quad (n_x,n_y)=(-5,-3)\;\text{up to symmetry},\quad
T_c=0.0944939203368691,
\]

\[
|k_*|^2=34(2\pi/1000)^2=0.001342266198548153.
\]

The frozen shell 40 and (T_c=0.052140879463) do not follow from its displayed formula or code.

## Task 3

Below the cusp,

\[
u'=\frac32\sqrt{\frac12-\rho_0},\qquad
u''=-\frac34\left(\frac12-\rho_0\right)^{-1/2}.
\]

The interior vertex is

\[
q_*=\frac{1+\alpha}{\alpha}\frac{1/2-\rho_0}{\rho_0}.
\]

A strictly finite onset requires (q_*<1), hence

\[
\boxed{\rho_0>\frac{1+\alpha}{2+4\alpha}}.
\]

The frozen denominator (2+3α) is an algebra error. For the Task 2 point, (0.37>4/11) gives a finite mode, while the frozen threshold (8/19) incorrectly predicts no finite mode.

## Task 4

The reduced source ODE is

\[
(\log R')'=-\frac{(1-\alpha)u''}{(1+\alpha)u'+2\alpha\rho u''}.
\]

Using (u'/u''=2(ρ-1/2)), not (2(1/2-ρ)), the regular singular point is

\[
\rho_m=\frac{1+\alpha}{2+4\alpha}.
\]

Residue integration gives

\[
R\sim\operatorname{sgn}(\rho-\rho_m)|\rho-\rho_m|^\xi,
\qquad \xi=\frac{1+5\alpha}{2+4\alpha}.
\]

Thus the frozen ξ is valid, but the frozen ρ_m is not. The source SM gives the same result through its general formula (ρ_m=ρ^*/[1+2α(γ-1)/(α+1)]).

## Task 5

Expanding the exact bracket (T-M_0(aq+bq^2)=A_0+A_2s+A_4s^2+⋯) yields

\[
A_2=\frac{M_0\sigma^2}{2}[a+2b],\qquad
\boxed{A_4=-\frac{M_0\sigma^4}{8}[a+4b]},
\]

where (a=(1+α)u') and (b=αρ_0u''). The frozen (A_4) has the opposite sign and is incompatible with its own assumption (A_2<0<A_4) at the finite-(k) parameters.

At (A_0=0), conserved dynamics gives (λ(s)=-A_2s^2-A_4s^3). Its unique positive maximum is

\[
s_*=\frac{-2A_2}{3A_4},\qquad
\boxed{k_{\rm sel}=\sqrt{\frac{-2A_2}{3A_4}}}.
\]

The frozen solution itself derives this stationary point, then replaces it with the nonconserved factor (\sqrt{-A_2/(2A_4)}).
