# Derivation Trace

This case follows a strict derivation-first lane. The numerical implementation
is allowed to evaluate only formulas traced and independently checked below.
The generated equation inventory is `DERIVATION.md`; this file supplies the
reasoning between those equations.

## 1. Convention and collective coordinates (`EQC001`--`EQC002`)

The paper uses

\[
W_\rho(\vec\alpha)=\left(\frac2\pi\right)^M
\operatorname{tr}\!\left[\rho\,e^{i\pi|\vec a-\vec\alpha|^2}\right].
\]

Consequently, for one mode,

\[
W_{|0\rangle}(\alpha)=\frac2\pi e^{-2|\alpha|^2},
\qquad
\chi_{|0\rangle}(\xi)=e^{-|\xi|^2/2}.
\]

For three modes we choose the orthonormal coordinates

\[
a_+=\frac{a_1+a_2+a_3}{\sqrt3},\qquad
a_-=\frac{2a_1-a_2-a_3}{\sqrt6},\qquad
a_\perp=\frac{a_2-a_3}{\sqrt2}.
\]

Their coefficient vectors are mutually orthogonal and have unit norm, so this
is a passive canonical transformation. On the paper's equal-coordinate slice,

\[
(\alpha_1,\alpha_2,\alpha_3)=(\alpha,\alpha,\alpha)
\quad\Longrightarrow\quad
(\alpha_+,\alpha_-,\alpha_\perp)=(\sqrt3\alpha,0,0).
\]

This step is the core simplification: the apparently correlated three-mode
slice is a center-of-mass coordinate while both relative modes are evaluated
at the origin.

## 2. Why the tripartite W state becomes one collective excitation (`EQC007`)

The normalized state is

\[
|W_3\rangle=\frac{|100\rangle+|010\rangle+|001\rangle}{\sqrt3}
=a_+^\dagger|000\rangle
=|1\rangle_+|0\rangle_-|0\rangle_\perp.
\]

The one-mode Fock Wigner functions are

\[
W_0(\gamma)=\frac2\pi e^{-2|\gamma|^2},
\qquad
W_1(\gamma)=\frac2\pi(4|\gamma|^2-1)e^{-2|\gamma|^2}.
\]

Evaluating the relative vacua at zero and setting
\(\gamma=\sqrt3\alpha\) therefore gives

\[
\begin{aligned}
W_{W_3}(\alpha\mathbf1)
&=W_1(\sqrt3\alpha)W_0(0)^2\\
&=\left(\frac2\pi\right)^3
  (12|\alpha|^2-1)e^{-6|\alpha|^2}.
\end{aligned}
\]

The negative central disk ends at

\[
r_0=\frac1{2\sqrt3}=0.288675\ldots,
\]

which is distinct from the larger measurement radius \(r\approx0.7\): the
latter must include enough of the positive annulus for the *absolute* volume
to cross the finite-region GME threshold.

## 3. Finite-disk absolute volume (`EQC006`--`EQC009`)

For \(M=3\), the finite-region definition and polar measure give

\[
\begin{aligned}
\mathcal V_{2D}(r)
&=\left(\frac\pi2\right)^2
  \int_{|\alpha|\le r}d^2\alpha\,|W_{W_3}(\alpha\mathbf1)|\\
&=4\int_0^r ds\,s\,|12s^2-1|e^{-6s^2}.
\end{aligned}
\]

Splitting the integral at \(r_0\) yields

\[
\mathcal V_{2D}(r)=
\begin{cases}
\big[(1+12r^2)e^{-6r^2}-1\big]/3,&r<r_0,\\[1mm]
\big[4e^{-1/2}-(1+12r^2)e^{-6r^2}-1\big]/3,&r\ge r_0.
\end{cases}
\]

The three-mode GME threshold is \(1/(2\sqrt2)\). Solving the second
branch rather than reading the dashed circle from the image gives

\[
r_{\rm crit}=0.6991953293441807.
\]

At the displayed radius,

\[
\mathcal V_{2D}(0.7)=0.354135475043561,
\qquad
\mathcal V_{2D}(0.7)-\frac1{2\sqrt2}
=5.8208445\times10^{-4}.
\]

Thus the rounded statement \(r\gtrsim0.7\) is quantitatively correct, though
the certification margin is small.

## 4. Characteristic-function witness (`EQC010`--`EQC011`)

Because the W state is a single excitation of \(a_+\),

\[
\chi_{W_3}(\xi\mathbf1)
=\chi_1(\sqrt3\xi)
=(1-3|\xi|^2)e^{-3|\xi|^2/2}.
\]

The paper chooses

\[
\xi_0=0.425+0.735i,\qquad
\Xi=\{0,\pm(\xi_0+\xi_0^*),\pm\xi_0,\pm\xi_0^*\}.
\]

There are seven points in \(\Xi\) and 19 unique pairwise differences. Central
symmetry reduces the independently measured set to ten points, including zero.
For \(M=3\) and a vacuum filter,

\[
\begin{aligned}
[C\circ K]_{nn'}
&=\frac17\chi_{W_3}\big((\xi_n-\xi_{n'})\mathbf1\big)
  \chi_0(\xi_n-\xi_{n'})\\
&=\frac17\left(1-3|\delta_{nn'}|^2\right)
  e^{-2|\delta_{nn'}|^2}.
\end{aligned}
\]

Direct Hermitian diagonalization gives

\[
\operatorname{eig}(C\circ K)=
(-0.01758038,\ 0.11728308,\ 0.11735684,\ 0.18902857,\
0.18915406,\ 0.20060104,\ 0.20415679).
\]

Therefore

\[
\mathcal N_C=0.017580375648\ldots,
\]

which reproduces the paper's \(0.0176\).

## 5. General Fock-basis Wigner matrix element

The Fig. 1 example contains Fock coherences. For \(m\ge n\), the required
single-mode matrix element in the paper's convention is

\[
W_{|m\rangle\langle n|}(\alpha)=
\frac2\pi(-1)^n\sqrt{\frac{n!}{m!}}\,
(2\alpha^*)^{m-n}L_n^{m-n}(4|\alpha|^2)e^{-2|\alpha|^2},
\]

with
\(W_{|m\rangle\langle n|}=W_{|n\rangle\langle m|}^*\) for the reversed
indices. Three checks fix the orientation and normalization:

1. \(m=n=0\) gives the normalized vacuum;
2. \(m=n\) gives \((2/\pi)(-1)^nL_n(4|\alpha|^2)e^{-2|\alpha|^2}\);
3. explicit truncated displaced-parity matrices agree for all
   \(0\le m,n\le4\) used here.

## 6. Expansion and normalization of the Fig. 1 state (`EQC012`)

Applying each normalized creation monomial to vacuum rewrites the printed state
as

\[
|\psi\rangle=
\frac1{5\sqrt2}(|1\rangle_++|3\rangle_+)
 (|0\rangle_-+\sqrt{19}|1\rangle_-)
+\frac1{\sqrt{10}}(|2\rangle_++|4\rangle_+)|2\rangle_-,
\]

with the \(a_\perp\) mode in vacuum. The six nonzero probabilities sum to

\[
\frac2{50}+\frac{38}{50}+\frac2{10}=1.
\]

The stated three-dimensional cut is

\[
W_\psi(\alpha_+,\alpha_-,0)
=W_0(0)\sum_{n_\pm,m_\pm}
c_{n_+,n_-}c^*_{m_+,m_-}
W_{|n_+\rangle\langle m_+|}(\alpha_+)
W_{|n_-\rangle\langle m_-|}(\alpha_-).
\]

The source does not disclose its positive/negative isosurface levels, mesh, or
camera. The numerical field itself is exact; only those rendering choices are
reconstructed.

## 7. Equal-coordinate slice polynomial and negative volume

Let \(\gamma=\sqrt3\alpha\), \(t=4|\gamma|^2\), and
\(R=\operatorname{Re}(\gamma^2)\). The unnormalized odd and even center-of-mass
cats produce

\[
\begin{aligned}
P_{13}
={}&-2+4t-\frac32t^2+\frac16t^3
-\frac8{\sqrt6}R(3-t),\\
P_{24}
={}&2-6t+\frac72t^2-\frac23t^3+\frac1{24}t^4
+\frac4{\sqrt3}R\left(6-4t+\frac12t^2\right).
\end{aligned}
\]

At the relative origin, odd relative number contributes negative parity.
Combining the \(n_-=0,1,2\) sectors therefore gives

\[
W_\psi(\alpha\mathbf1)=
\left(\frac2\pi\right)^3e^{-2|\gamma|^2}
\left[-\frac9{25}P_{13}+\frac1{10}P_{24}\right].
\]

Polar Gauss--Legendre integration of its negative part converges as follows:

| radial × angular points | \(\mathcal N_{2D}\) |
| ---: | ---: |
| \(160\times360\) | 0.263735048 |
| \(360\times1080\) | 0.263704963 |
| \(640\times2048\) | 0.263699240 |
| \(800\times3072\) | 0.263699571 |
| \(1200\times6144\) | 0.263699033 |

The accepted value is \(0.263699\) with a \(5\times10^{-6}\) numerical
tolerance. This convergence test is independent of the exact signed integral
derived next.

## 8. The source's numerator inconsistency (`EQC013`)

Supplemental S1 proves, for \(M=3\),

\[
\int d^2\alpha\,W_\rho(\alpha\mathbf1)
=\frac13\left(\frac2\pi\right)^2
  \operatorname{tr}(\rho\Pi_-).
\]

For the printed state, the probabilities in relative Fock sectors
\(n_-=0,1,2\) are \(2/50,38/50,2/10\). Hence

\[
\langle\Pi_-\rangle
=\frac2{50}-\frac{38}{50}+\frac2{10}
=-\frac{13}{25}
\]

and

\[
\int d^2\alpha\,W_\psi(\alpha\mathbf1)
=-\frac{52}{75\pi^2}.
\]

Substitution into Theorem 1 gives

\[
\mathcal N_{2D}^{\rm GME}
=\frac1{4\sqrt2}
-\frac{\pi^2}{8}\left(-\frac{52}{75\pi^2}\right)
=\frac{75\sqrt2+52}{600}
=0.263443361963\ldots.
\]

The End Matter instead prints

\[
\frac{75\sqrt2+56}{600}=0.2701100286\ldots.
\]

That printed value cannot follow from the displayed normalized state. The
independent negative-volume integral \(0.263699\) clears the state-derived
bound by about \(2.56\times10^{-4}\), but it does not clear the printed bound.
The reproduction therefore:

- preserves the source value as provenance;
- flags it as internally inconsistent;
- evaluates the physical claim against the formula derived from the printed
  state;
- does not describe the printed inequality itself as reproduced.

## 9. Reduced center-of-mass state and exact smoothing (`EQC014`)

Tracing over the relative modes gives

\[
\rho_+=
0.4(|1\rangle+|3\rangle)(\langle1|+\langle3|)
+0.1(|2\rangle+|4\rangle)(\langle2|+\langle4|).
\]

The trace is \(0.4\times2+0.1\times2=1\). At the origin, the radial kernel
\(K(\beta)=8e^{-6|\beta|^2}/\pi\) removes all off-diagonal Fock coherences by
angular integration. The remaining Laguerre integral is

\[
\int d^2\beta\,W_n(\beta)K(\beta)
=\frac{(-1)^n2^{1-n}}{\pi}.
\]

Using diagonal populations
\((p_1,p_2,p_3,p_4)=(0.4,0.1,0.4,0.1)\),

\[
\begin{aligned}
\widetilde W_{\rho_+}(0)
&=0.4\left(-\frac1\pi\right)
 +0.1\left(\frac1{2\pi}\right)
 +0.4\left(-\frac1{4\pi}\right)
 +0.1\left(\frac1{8\pi}\right)\\
&=-\frac7{16\pi}.
\end{aligned}
\]

This independently reproduces the paper's second Fig. 1 witness without a
grid-dependent convolution at the validation point.

## 10. Companion-paper sampling counts (`EQC015`)

The Letter quotes about 76,000 and 78 phase-space measurements but delegates
the numerical-integration details to its companion study. That public paper
states a circular integration region and a square grid, so the leading count
is determined without any author array:

\[
N_{\rm grid}\simeq\frac{\pi r^2}{\Delta^2}.
\]

For the rigorous error bound, (r\simeq0.9) and
(\Delta=0.0058) give (N\simeq75{,}645), which rounds to 76,000. For the
coarse example, (r=1) and (\Delta=0.2) give (N\simeq78.54), consistent
with the paper's explicitly approximate 78-point statement. This is a formula
recomputation, not a count read from the plotted grid.

## 11. Families for every finite mode count (`EQC016`)

For the first theorem, a balanced multiport maps a one-mode Fock input to an
(M)-mode family with

\[
\mathcal V_{2D}(\mathcal U_M(|n\rangle))
=\frac1M\int d^2\alpha\,|W_n(\alpha)|.
\]

The absolute Fock-state Wigner volume is independently integrated by splitting
at the Laguerre roots. For every declared test value (3\le M\le12), the code
finds a finite (n\le32) whose volume exceeds (M/(2\sqrt{M-1})). The general
all-finite-(M) statement additionally depends on the proof that these volumes
are unbounded with (n); that quantifier is reserved for fresh proof review.

For the second theorem, the lossy (M)-mode W family has the exact lower bound

\[
d_{\rm GME}\ge\frac{1-M\eta}{M-1}.
\]

It is therefore detected whenever (\eta<1/M), giving an explicit family for
every finite (M\ge3).

## 12. Robustness versus mode count (`EQC017`)

The same exact law gives

\[
\eta_{\max}(M)=\frac1M,
\qquad
\frac{d\eta_{\max}}{dM}=-\frac1{M^2}<0.
\]

Thus at least the theorem-2 W-state family makes the paper's decreasing-
robustness statement directly executable; no curve pixels or author data are
needed.

## Formula Gate Decision

- `EQC001`--`EQC012` and `EQC014`--`EQC017`: source-traced and independently
  verified.
- `EQC013`: independently reconstructed from the printed state; numerical work
  is allowed only with an explicit `source_inconsistency` flag.
- No formula remains `source_only` or blocked.
- Target `T002` is eligible for paper-exact execution.
- Target `T001` is eligible for exact field evaluation, while its source
  comparison remains feature-level because rendering parameters are missing
  and one quoted source value is inconsistent.
- Targets `T003`--`T005` have executable formula and finite-falsification
  artifacts; general proof acceptance remains a fresh-context review decision.
