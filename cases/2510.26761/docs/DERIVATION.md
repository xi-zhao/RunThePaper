# Derivation

This note records the equations that authorize the public numerical
reproduction of arXiv:2510.26761. The implementation is in
[`wigner_gme.py`](../code/src/wigner_gme.py).

## 1. Equal-coordinate slice

For three modes, evaluate the Wigner function on

\[
(\alpha_1,\alpha_2,\alpha_3)=(\alpha,\alpha,\alpha).
\]

The orthogonal collective coordinates contain one center-of-mass mode,
\(\alpha_+=\sqrt{3}\alpha\), while both relative coordinates vanish. A
correlated three-mode slice therefore reduces to one center-of-mass Wigner
function multiplied by the relative-mode parity.

For the tripartite W state, the center-of-mass mode contains one excitation.
Using the paper's \(2/\pi\) convention gives

\[
W_{W_3}(\alpha\mathbf 1)
=
\left(\frac{2}{\pi}\right)^3
\left(12|\alpha|^2-1\right)e^{-6|\alpha|^2}.
\]

The sign change occurs at \(r=1/(2\sqrt 3)\), but this is not the certification
radius. The witness integrates the absolute negative volume over a disk.

## 2. Finite-disk witness

Radial integration gives the disk volume

\[
\mathcal N_{\Omega_r}
=
\begin{cases}
\tfrac13-e^{-6r^2}(2r^2+\tfrac13), & r\leq 1/(2\sqrt3),\\
e^{-6r^2}(2r^2+\tfrac13)-\tfrac16+\tfrac{1}{\sqrt e},
& r>1/(2\sqrt3).
\end{cases}
\]

Solving
\(\mathcal N_{\Omega_r}=1/(2\sqrt2)\) yields

\[
r_{\mathrm{crit}}=0.6991953293441805.
\]

At the paper's \(r=0.7\),

\[
\mathcal N_{\Omega_{0.7}}=0.354135475043561,
\qquad
\frac1{2\sqrt2}=0.353553390593274,
\]

so the positive certification margin is \(5.8208445\times10^{-4}\).

## 3. Finite characteristic-function witness

For the same W state,

\[
\chi_{W_3}(\xi\mathbf1)
=
\left(1-3|\xi|^2\right)e^{-3|\xi|^2/2}.
\]

The seven source points define a \(7\times7\) Hermitian matrix through their
pairwise differences. Symmetry reduces the 49 entries to 19 distinct complex
differences and ten independent measurements. Its only negative eigenvalue is

\[
\lambda_{\min}=-0.0175803756480382,
\]

which reproduces the paper's characteristic witness
\(\mathcal N_C=0.0176\).

## 4. Fig. 1 source inconsistency

The six printed collective-Fock amplitudes are normalized. Their relative-mode
parity is

\[
\langle\Pi_-\rangle=-\frac{13}{25},
\]

so the signed equal-slice integral is

\[
\int d^2\alpha\,W(\alpha\mathbf1)
=-\frac{52}{75\pi^2}.
\]

Substitution into the paper's theorem gives the state-dependent bound

\[
\frac{75\sqrt2+52}{600}
=0.263443361963304.
\]

The End Matter instead prints \(75\sqrt2+56\), corresponding to
0.270110028629970. Independent quadrature converges to

\[
\mathcal N_{2D}=0.263699570681490.
\]

The result exceeds the bound derived from the printed state by
\(2.5620872\times10^{-4}\), but it does not exceed the separately printed
\(+56\) bound. Both values are retained: the reproduction does not tune the
numerics to erase a source-level contradiction.

The second Fig. 1 witness is independent of this ambiguity. Gaussian smoothing
of the reduced center-of-mass Wigner function gives exactly

\[
\widetilde W(0)=-\frac7{16\pi}
=-0.139260575205408,
\]

matching the numerical convolution at machine precision.
