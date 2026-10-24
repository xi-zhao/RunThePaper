# Model and independent derivation, fixed quant-ph/0202029v2

Source: supplied fixed PDF (16 Apr 2002), equation (1), equation (2), Figures 1–4.
Only this revision is used. No external code or reference ordinates enter generation.

## Coordinate and symmetry

The plotted critical coordinate is lambda=1. We calculate
H/h = -sum_i {lambda/2 [(1+gamma) X_i X_(i+1) + (1-gamma) Y_i Y_(i+1)] + Z_i}.
This convention has quasiparticle energy 2h sqrt((1-lambda cos k)^2+(lambda gamma sin k)^2).
A uniform pi/2 spin rotation interchanges X and Y and cannot change concurrence.
The printed Eq. (1) has no brackets around the two exchange terms, writes (1-gamma)
on X and (1+gamma) on Y, and defines lambda=J/(2h) despite the exchange coefficient
J/2 with Pauli matrices. Under the natural common-prefactor reading it is critical
at J/h=1, hence at printed lambda=1/2. This factor is exposed, not silently corrected.
The figure coordinate is therefore an explicit interpretation, not literal support
for every character of Eq. (1). The printed xi ~ |lambda-lambda_c|^nu also lacks
the minus sign required by the adjacent word 'diverges'.
If sigma were instead intended as S=Pauli/2, lambda=J/(2h) would be consistent
with the plotted transition. This is a possible convention repair, but it differs
from the source's explicit statement that sigma denotes Pauli matrices; it is not
evidence about which convention the author's implementation actually used.

## Covariance and reduced state

Jordan–Wigner maps a parity-symmetric ground state to paired free fermions. In the
even spin-parity sector of a periodic chain, k=(2m+1)pi/N, m=0,...,N-1. Let
epsilon=sqrt((lambda cos k-1)^2+(lambda gamma sin k)^2), and
G_r=<[(lambda cos k-1)cos(rk)+lambda gamma sin k sin(rk)]/epsilon>_k.
For the infinite chain the average is the integral from 0 to pi divided by pi.
m_z=-G_0; xx(r)=det[G_(1+i-j)]; yy(r)=det[G_(-1+i-j)]; zz(r)=G_0^2-G_r G_-r.
The r by r determinants follow Wick contraction of the Jordan–Wigner string.
In the Z basis, rho has diagonals (1+2m+zz,1-zz,1-zz,1-2m+zz)/4,
rho14=(xx-yy)/4 and rho23=(xx+yy)/4. Equation (2) then reduces to
C=max(0,(|xx-yy|+zz-1)/2,(|xx+yy|-sqrt((1+zz)^2-4m^2))/2).
This is checked separately by direct spin-Hamiltonian diagonalization and spin flip.

For r=1, xx=G_1, yy=G_-1. For r=2, xx=G_1^2-G_0 G_2 and
yy=G_-1^2-G_0 G_-2. Derivatives are analytic derivatives of these products and
of u/sqrt(q): f'=u'/sqrt(q)-u q'/(2q^(3/2));
f''=-u'q'/q^(3/2)-u q''/(2q^(3/2))+3u(q')^2/(4q^(5/2)).
No finite-difference data are used to generate the main curves.

At lambda=gamma=1, G_r=2/[pi(2r-1)]. This independently supplies critical C(r).
The singular part of G'_r is -(ln|lambda-1|)/pi for every fixed r. In C1' its
coefficient is (2G0-G1-G-1)/2 times -1/pi = 8/(3pi^2).
The small-k gap is 2h|1-lambda| and velocity 2h gamma, hence xi proportional
to gamma/|1-lambda| near criticality for fixed gamma>0. This gives nu=1 independently
of a finite-size curve fit. An infrared cutoff k~1/N replaces ln|lambda-1| by -ln N.

## Checks and numerical resolution chosen before numerical judgment

Small-chain two-point functions and concurrence: direct Hilbert-space eigensolver
versus covariance, absolute agreement 1e-9 (states up to N=11, deterministic initial
vector, residual measured). First/second derivatives: finite-difference step convergence,
target errors 1e-6/1e-4 away from the infinite-chain singularity.
Asymptotic slopes are assessed using changing fit windows, not rounded equality;
agreement within 0.003 with 8/(3pi^2) suffices to distinguish the stated logarithmic
amplitude from a different coefficient, but all observed errors will be retained.
EPS coordinates have 4 decimal places: extraction quantization is at most 0.00005
in each normalized page coordinate. Use coordinate uncertainty and local derivative
when comparing references; drawing linewidth is not a numerical uncertainty estimate.
Finite-size collapse is quantified over the full plotted x range [-0.2,0.2]; residual
finite-size corrections are reported, not tuned away or asserted to be exact collapse.
Other analytic claims receive explicit asymptotic/definition checks and are not promoted
from a finite sample to a general proof.

## Exact critical Ising values and all-distance range

Write a=2/pi. At criticality G0=-a, G1=a, G(-1)=-a/3, G2=a/3,
G(-2)=-a/5. Thus
C1 = 4/(3pi) + 8/(3pi^2) - 1/2,
C2 = 224/(45pi^2) - 1/2.
The Cauchy determinant gives
xx(r)=(2/pi)^r product_(j=1)^(r-1) [1-1/(4j^2)]^(j-r),
yy(r)=-xx(r)/(4r^2-1), zz(r)=(4/pi^2)[1+1/(4r^2-1)].
The Wallis product shows xx(r+1)/xx(r)<1. Both xx(r) and
1+1/(4r^2-1) decrease with r. Hence the entangling branch
{[1+1/(4r^2-1)] [xx(r)+4/pi^2] -1}/2 decreases with r.
It is positive for r=2 and negative for r=3, so remains negative for all r>=3.
The other concurrence branch cannot be positive: positivity of rho requires
|xx+yy|<=1-zz, and sqrt((1+zz)^2-4m^2)>1-zz because zz-m^2>0.
This proves the infinite-chain critical entanglement range is exactly two sites,
while xx(r) decays algebraically. Finite-N off-critical range claims receive
separate direct checks; the critical proof is not mislabelled as an all-parameter proof.

## Why C2 is stationary at the critical point, including finite N

For gamma=1, the critical symbol is i exp(ik/2), and its lambda derivative is
exp(ik/2) cot(k/2)/2. Put A=G1=-G0, B=G2=-G(-1), C=G3=-G(-2).
Writing T=G0'=G1', U=G2'=G(-1)', V=G3'=G(-2)', the pointwise trigonometric
identity gives T-U=(A+B)/2 and U-V=(B+C)/2. The derivative of the C2 polynomial
is (U-T)(B+C)+(U-V)(A+B)=0. This works for the finite antiperiodic sum too.
The computed negative second derivative and full inset establish the maximum
within the plotted parameter/size range. The direct spin check corroborates the
finite-chain state, rather than assuming boundary conditions from continuum theory.

## C2 logarithmic coefficient and elliptic check

For fixed r, the common singular coefficient in G_r' is -1/pi. At criticality
the second derivative integrand is
-cos[(r-1/2)k] cot(k/2)/2 - sin[(r-1/2)k] cot^2(k/2)/4,
whose 1/k coefficient is -(r+1/2). Thus its logarithmic coefficient is
(r+1/2)/pi; the common 1/(lambda-1) term in the infinite-limit derivatives cancels
in C2''. The finite differences of the regular parts b_r of G_r' obey the same
identities above. Choose their irrelevant common part so b0=b1=0,
b2=b(-1)=-4/(3pi), b(-2)=-28/(15pi). Substituting in the C2 polynomial gives
the product-of-first-derivatives contribution -16/(3pi^2) and the
G_r G_s'' contribution 32/(5pi^2). Their sum is 16/(15pi^2)=0.1080759292...,
consistent with the paper's rounded 0.108.

A distinct infinite-chain calculation uses complete elliptic integrals:
m=4lambda/(1+lambda)^2, I0=<epsilon>=2(1+lambda)E(m)/pi,
F0=<1/epsilon>=2K(m)/[pi(1+lambda)],
F1=[(1+lambda^2)F0-I0]/(2lambda),
F_(r+1)=[r(1+lambda^2)F_r-lambda(r-1/2)F_(r-1)]/[lambda(r+1/2)],
G_r=lambda F_|r-1|-F_|r|.
The recurrence follows by integrating d[sin(rk)epsilon]/dk. Arbitrary-precision
differentiation of this elliptic expression checks the singular amplitudes without
the generating adaptive quadrature or its double-precision cancellation.

## Finite-size shift and anisotropy: precise scope

C1''(lambda=1) has logarithmic coefficient 1/pi-4/(3pi^2), so its finite-size
value has a negative ln N term. The curvature of C1' grows proportionally to N^2
from the small-k denominator. Expanding the stationarity equation therefore gives
lambda_m-1 proportional to (a ln N+b)/N^2, not a universal pure power 1.87.
The source's fitted 1.87 is assessed on its finite-size window, with new larger
sizes used only to test that original scaling statement.

At fixed gamma>0, the same small-k gap yields nu=1. The singular amplitude of C1'
is [G1+G(-1)-2G0]/(2pi gamma), while the finite-size depth has its negative as the
coefficient of ln N. This supplies a check of gamma=0.5 beyond visual collapse.

For gamma approaching zero at lambda=1, k=gamma q makes the symbol tend to
(-q/2+i)/sqrt(1+q^2/4), so the long-distance kernel depends on gamma*r.
This supports a range proportional to 1/gamma provided the concurrence kernel
has a finite positivity boundary. The determinant calculation checks that boundary
over decreasing gamma; it is an asymptotic scaling argument plus finite evidence,
not a uniform rigorous error bound for every real gamma.
The paper does not explicitly attach a lambda to its sentence sum_n C(n)<0.2.
We report the critical interpretation separately from an unrestricted interpretation,
which is contradicted already by the nearest-neighbour maximum in its own Fig.1 inset.

## Numerical reference interpretation

Literal EPS path vertices were separated from independent generation. All five finite
N Fig.1 main curves agree within propagated four-decimal coordinate resolution.
The two infinite-curve edge vertices have y=0.1499 next to a plot border y=0.1500;
their fractional x steps differ from the otherwise uniform sampling. They are
clipped line-segment intersections, not function evaluations. Their 0.17 vertical
residuals are preserved in the initial comparison. All other 200 infinite-chain
vertices agree within the coordinate bound. This diagnosis concerns rendering;
it does not identify the author's quadrature, finite-difference scheme or precision.
The original source does not carry raw numerical tables or explicit per-curve N
labels for every collapse marker. Extra size-grid comparisons therefore distinguish
an inferred compatible N from authenticated author parameter metadata.
