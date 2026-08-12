# Derivation

## Rotating oscillator

Transforming a two-dimensional isotropic oscillator to a frame rotating at
`Omega_rot` gives `H_rot = H_0 - Omega_rot L_z`. For shell `n` and angular
momentum `m`,

$$
\frac{E_{n,m}}{\hbar\omega}=n+1-m\frac{\Omega_{\mathrm{rot}}}{\omega}.
$$

At `Omega_rot=omega`, all lowest-Landau-level states `n=m>=0` have energy
`hbar omega`. This supplies T001 and T008 without diagonalizing a fitted model.

## Two-particle Laughlin state

For two particles and filling `nu=1/2`,

$$
\psi_{1/2}\propto (z_\uparrow-z_\downarrow)^2
\exp\!\left[-\frac{|z_\uparrow|^2+|z_\downarrow|^2}{2}\right].
$$

With `z_rel=(z_up-z_down)/sqrt(2)`, this is `|0>_com |2>_rel`. Expanding the
polynomial gives the normalized one-particle decomposition

$$
|\psi_{1/2}\rangle=\frac{|0\rangle|2\rangle+|2\rangle|0\rangle}{2}
-\frac{|1\rangle|1\rangle}{\sqrt{2}}.
$$

Therefore either particle has orbital weights `(1/4,1/2,1/4)` for
`m=(0,1,2)`. The normalized LLL density is

$$
\rho_m(p)=\frac{p^{2m}e^{-p^2}}{\pi m!}.
$$

In the paper's radial-density units `1/(2 pi p_HO^2)`, the curve is
`n_m(p)=2 p^(2m) exp(-p^2)/m!`. It follows analytically that the relative
`m=2` density peaks at `p=sqrt(2) p_HO`.

## Angle correlation

Integrating the two-particle probability over both radii and the absolute
angle leaves the printed normalized function

$$
g_{1/2}(\phi)=\frac{6-3\pi\cos\phi+4\cos^2\phi}{16\pi}.
$$

Direct quadrature gives unit integral and a maximum at `phi=pi`.

## Rabi and Ramsey dynamics

The measured ground-orbital occupation is two initially and one half in the
ideal Laughlin state. A resonant two-level oscillation with the printed
`0.42 kHz` rate is therefore

$$
n_0(t)=1.25+0.75\cos(2\pi\,0.42\,t_{\mathrm{ms}}).
$$

For the anisotropic Ramsey sequence, `|+>` and `|->` are split eigenstates and
`|2>=(|+>+|->)/sqrt(2)`. Their relative phase produces coherent `m=+2` to
`m=-2` evolution. The plotted fit envelope is represented by the standard
damped two-level observable using each printed frequency and coherence time.
The paper does not print fit amplitude or phase, so those two display-only
quantities remain a normalized convention rather than a paper-exact claim.

## Interaction and Gaussian reconstruction

The supplement separates center-of-mass and relative motion in a harmonic
trap. Only the relative `m=0` sector interacts. The implementation maps the
published broad lithium-6 resonance parameters to a confined one-dimensional
delta problem and solves its even-parity gamma-function equation. This is a
physically controlled reconstruction, not the authors' omitted coupled-channel
calculation.

Expanding the printed Gaussian potential fixes the dimensionless quartic
coefficient without the unpublished tweezer power:

$$
\alpha=-\frac{1}{2}\left(\frac{l_{\mathrm{HO}}}{W}\right)^2.
$$

The printed single-particle/COM-relative basis transformations then determine
the complete `M=2` and `M=4` quartic matrices. At the zero crossing the `M=2`
gap is exactly `2|alpha|`, independently recovering the reported approximately
`1.4 kHz` anharmonicity. Keeping the factor of two here is essential: `alpha`
is the coefficient of each single-particle `r^4` term, whereas the avoided
crossing contains two coupled two-particle basis states.

Finally the printed rotating perturbation is applied to the reconstructed
three-state `M=0 -> M=2` model in the rotating frame. Since the supplement
omits its drive amplitude, the main-text `0.42 kHz` Rabi rate is used as a
declared proxy; T011 is never labeled paper-exact.
