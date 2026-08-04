# Derivation trace

## 1. Complex AAH potential and PT symmetry

Starting from main Eqs. (1)-(4),

\[
H\psi_n=J(\psi_{n+1}+\psi_{n-1})+
V\cos(2\pi\alpha n+\theta+ih)\psi_n .
\]

At `theta=0`, expansion of the cosine gives

\[
V_n=V\cos(2\pi\alpha n)\cosh h
-iV\sin(2\pi\alpha n)\sinh h,
\qquad V_{-n}=V_n^*.
\]

This corrects the extra minus sign printed after main Eq. (4).  Together with
real symmetric hopping, `V_{-n}=V_n^*` is the PT condition.

## 2. Fourier duality and the critical phase

Apply Supplement Eqs. (S-4)-(S-6):

\[
\phi_m=L^{-1/2}\sum_n\psi_n e^{2\pi i\alpha nm},
\]

so multiplication by the quasiperiodic cosine becomes asymmetric nearest-
neighbor hopping in the dual basis,

\[
E\phi_m={V\over2}(e^{-h}\phi_{m+1}+e^h\phi_{m-1})
+2J\cos(2\pi\alpha m)\phi_m .
\]

At `h=0` and `V<2J`, this dual AAH problem is localized with the common
Lyapunov exponent

\[
\gamma=\log(2J/V).
\]

The imaginary gauge factor multiplies a localized tail by `exp(hm)`.  It
overcomes `exp(-gamma |m|)` at `h=gamma`; hence

\[
h_c=\gamma=\log(2J/V).
\]

Dual states delocalize above `h_c`; Fourier duality therefore makes the
original states localized.  At the same point the PT-symmetric real spectrum
becomes complex.

## 3. Winding number

Main Eq. (5) follows the determinant as `theta` advances:

\[
w={1\over2\pi i}\int_0^{2\pi}\partial_\theta
\log\det[H(\theta/L,h)-E_B]d\theta .
\]

The similarity transform in Supplement Eq. (S-11) moves the phase into a
boundary link.  In the large-`L` limit,

\[
f(\theta,h)=A_L(h)e^{-i\theta}+D_L,
\quad |A_L|=(V/2)^L e^{hL},
\quad |D_L|=(V/2)^L e^{\gamma L}.
\]

The circle traced by `f` encloses the origin only if `h>gamma`.  Its clockwise
orientation gives

\[
w=0\;(h<h_c),\qquad w=-1\;(h>h_c).
\]

## 4. Localization observable

For every right eigenvector, use the paper's definition

\[
\mathrm{IPR}(\psi)=
{\sum_n|\psi_n|^4\over(\sum_n|\psi_n|^2)^2}.
\]

It approaches `1/L` for extended states and order one for localized states.
The minimum and maximum over the full eigensystem generate Main Fig. 1(c) and
Supplement Fig. S1(c).

## 5. Open-boundary edge states

Supplement S.3 removes only the two ring corner hoppings.  Edge identity is
assigned from normalized right-eigenvector probability: a state is left/right
localized when the corresponding boundary window contains a dominant fraction
of its norm and its center of mass lies in that window.  The threshold is fixed
once from the `h=0` analytic localization pattern, not fitted separately at
each `h`.

## 6. Frequency-domain laser

Main Eqs. (8)-(9) give

\[
i\dot\psi_n=J(\psi_{n+1}+\psi_{n-1})+
V_0e^{2\pi i\alpha n+i\theta}\psi_n+i\mathcal L_n(g)\psi_n,
\]

\[
\mathcal L_n(g)=-\gamma+{g\over1+4n^2\omega_m^2/\Delta\omega_g^2},
\qquad
\dot g=\gamma_\parallel[g_0-g(1+I)].
\]

At a stationary single-lasing-mode solution, the selected eigenmode has zero
net growth and gain saturation sets its intensity.  Solving this neutral-growth
condition is the fixed-point reduction of the printed dynamics and avoids
inventing the omitted transient duration.  Its plotted bandwidth is the RMS
axial-mode displacement `sqrt(sum(n^2 p_n))` from the gain-line center.  The
transition follows from
`J=Delta_FM/2`: `J=V0` implies `Delta_FM=2V0`.

## 7. Etalon transmission

Supplement Eqs. (S-27)-(S-29) give

\[
t_{et}(\omega)={1-R\over1-Re^{2i\delta+i\phi}},\qquad
R=\left({n_1-1\over n_1+1}\right)^2,
\]

and, to first order in `R`,

\[
t_{et}(\omega)\simeq1-R+Re^{2i\delta+i\phi}.
\]

Using `L=3 cm`, `n1=2.2321`, and four free-spectral ranges generates both
real and imaginary axes of Supplement Fig. S2.
