# Derivation Trace

## EQ001 — PT-symmetric eigenproblem

Starting from Eq. (1), `p=-i d/dx` gives

`-psi''(x) + [m^2 x^2 - (i x)^N] psi(x) = E psi(x)`.

For a real eigenvalue, PT symmetry permits the normalization
`psi(-x)^*=psi(x)`. At the origin this implies real `psi(0)` and purely
imaginary `psi'(0)`, equivalently
`Re[psi'(0)/psi(0)] = 0`.

## EQ002 — admissible complex contour

Eq. (3) gives the anti-Stokes ray centers

`theta_L=-pi+(N-2)pi/[2(N+2)]`,
`theta_R=-(N-2)pi/[2(N+2)]`,

with wedge opening `2pi/(N+2)`. A smooth PT-symmetric contour used for finite
differences is

`x(t)=cos(alpha)t-i sin(alpha)(sqrt(t^2+a^2)-a)`,

where `alpha=(N-2)pi/[2(N+2)]`. It passes through the origin and approaches the
two anti-Stokes directions at large `|t|` without using any source-figure
geometry.

The chain rule gives

`d_x^2 = x'(t)^(-2)d_t^2 - x''(t)x'(t)^(-3)d_t`,

which defines the contour finite-difference matrix.

## EQ003 — WKB spectrum

Deforming the phase integral through the two turning points in Eq. (4) gives

`E_n ~ [Gamma(3/2+1/N) sqrt(pi)(n+1/2) /
        (sin(pi/N) Gamma(1+1/N))]^(2N/(N+2))`.

At `N=2`, gamma identities reduce this expression to the exact harmonic
oscillator result `E_n=2n+1`.

## EQ004 — near-N=1 exact patching

On the positive real axis, integrate the logarithmic derivative
`y=psi'/psi` backward from a large boundary:

`y'=V(x)-E-y^2`, `V(x)=-(ix)^N`.

The decaying WKB boundary condition is
`y(X)=-sqrt(V(X)-E)-V'(X)/[4(V(X)-E)]` with the square-root branch chosen to
have positive real part. Exact real eigenvalues solve `Re y(0)=0`.

## EQ005 — printed N=1+epsilon asymptotic equation

Equation (11) is evaluated as a log-domain scalar root:

`0=log(epsilon)-3/2 log(E)+4/3 E^(3/2)
   +log([sqrt(3)log(2sqrt(E))+pi-(1-gamma)sqrt(3)]/8)`.

This avoids overflow while preserving the paper's equation exactly.

## EQ006 — massive N=1 check

For positive printed `m^2`, complete the square:

`m^2 x^2-i x = m^2[x-i/(2m^2)]^2 + 1/(4m^2)`.

Thus the full spectrum at `N=1` is analytically

`E_n=(2n+1)sqrt(m^2)+1/(4m^2)`.

This is an independent anchor for all three Fig. 3 target families.
