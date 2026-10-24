# Independent derivation and applicability (fixed 1805.06492v2)

The matrix convention is H[A_n,B_n]=a=f_-=t+gamma/2,
H[B_n,A_n]=b=f_+=t-gamma/2, H[B_n,A_(n+1)]=c=g_+,
H[A_(n+1),B_n]=c=g_-, with diagonals +d on A and -d on B.
All energy units use the paper's t2=1 (SSH), delta=Delta=1 (Rice-Mele).
This is an independent implementation; no reference ordinates enter generation.
NumPy/SciPy are existing general linear algebra libraries, mpmath supplies independent
arbitrary-precision arithmetic. No paper-specific code is used or installed.

## Eqs. (3)-(4), termination and exact spectra

The B row with zero B amplitudes gives b A_n+c A_(n+1)=0, so r_R=-b/c.
The adjoint equation gives r_L=-a*/c*. The exact energy is d, including complex d.
Using powers n-1 instead of n removes the removable singularity at r=0 without
changing a nonzero normalized state. Residuals can be checked on the physical matrix.

Reordering into A/B blocks gives H=[[d I,T],[S,-d I]]. For an odd chain with
N A and N-1 B sites, ST has diagonal ab+c^2 and upper/lower entries ac,bc.
The sine eigenvectors after a diagonal similarity give
E_m^2=d^2+ab+c^2+2c sqrt(ab) cos(m pi/N), m=1,...,N-1, plus E=d.
For an even 2N chain a diagonal similarity changes intracell hopping to sqrt(ab)
and leaves c unchanged. This avoids the exponentially ill-conditioned skin basis.
The transformation preserves characteristic polynomials, including ab<0 by complex
square roots; at ab=0 the eigenvalue multiset is its continuous limit, although the
eigenvectors need not remain complete. This is not a Hermitian replacement model.

For B termination with coordinates increasing left to right, the A row instead gives
a B_n+c B_(n-1)=0, hence r_R,B=-c/a=1/r_L* and r_L,B=-c*/b*=1/r_R*.
The main text's literal individual substitution r_(L/R) -> 1/r_(L/R) needs checking:
left/right roles exchange. Its product still maps q -> 1/q, preserving the claimed
polarization swap and transition positions. This issue is separated from Eqs.(3)-(4).

## Eqs. (5)-(7), quantization and its boundary

Set q=r_L* r_R=ab/c^2. With j=n-1, rho_n=q^j/S_N and
S_N=(1-q^N)/(1-q). The first moment is 1+q d(log S_N)/dq.
At fixed |q|<1, P_N=1-[1+q/(1-q)-N q^N/(1-q^N)]/N ->1.
At fixed |q|>1 it tends to 0. The argument allows complex q; rho is not a
positive probability. Critical |q|=1 is excluded from quantized boundary phases.
At q=1, P_N=(N-1)/(2N); at q=-1 and N even the overlap vanishes and biorthogonal
normalization is undefined (an exceptional degeneracy). Thus no finite-size integer
P or defined polarization at every critical point is claimed.
For signed envelope decay lengths 1/xi_L+1/xi_R=0 is the robust critical equation;
xi_L+xi_R=0 assumes finite nonzero lengths. The Hermitian critical limit has both
lengths infinite and must be understood as a limit, not algebraic addition of infinity.

## SSH and Rice-Mele

For SSH q=(t1^2-gamma^2/4)/t2^2. Setting q=+/-1 gives Eq.(9), retaining only
real roots. Bloch E^2=(t1+gamma/2+t2 exp(-ik))(t1-gamma/2+t2 exp(ik)) has EPs
t1=+/-gamma/2 +/-t2, explaining the separate periodic and open thresholds.
Finite even chains have hybridization splitting, not exact zero eigenvalues at all
parameters. Chiral spectral pairing and exponential disappearance of this splitting
are the relevant thermodynamic statement.
The alternative PT chain has a=b=t1 and d=i gamma/2. The boundary energies are
E=d (odd A chain) and +/-d for the two even-chain edges; attachment at |t1|=|t2|
concerns the edge-bulk gap, not a claim that all PT bulk zero-energy EPs occur there.

For Rice-Mele t= t1+delta cos(kx), c=t1-delta cos(kx), d=-Delta sin(kx).
The equations (t1+delta u)^2-gamma^2/4=+/-(t1-delta u)^2 yield Eq.(11).
There are 2 roots from u=gamma^2/(16 t1 delta) when |u|<1, and 4 from
u=+/-sqrt((gamma^2/8-t1^2)/delta^2) when the radicand is strictly between 0 and 1.
On phase boundaries roots may coalesce; region counts describe interiors.
The d term cancels in attachment to E=d but enters the Bloch EP equation E^2=0.
At c=0 (kx=0 for t1=delta=1) the ratio is undefined; the finite matrix is decoupled
dimers plus one A site and the spectrum is obtained by continuity, not division by zero.

## Boundary sensitivity and domain walls

For odd physical length L=2N-1, couple the two A endpoints by Gamma t2 as in
the supplement's odd-chain intent. At t1=sqrt(13)/2, a b=1 and q=1. The first-order
shift is Gamma*(a^(N-1)+b^(N-1))/N. Consequently the |E|=epsilon threshold is
approximately epsilon*N/(a^(N-1)+b^(N-1)). Its limiting exponential rate per physical
site is log(a)/2=0.5973816..., with an O(log N) prefactor and finite-fit correction.
A second, exact calculation uses the cyclic tridiagonal determinant
D_L(E)-Gamma^2 D_(L-2)(E)-Gamma*(a^(N-1)+b^(N-1))=0,
where D_j=E D_(j-1)-D_(j-2), D_0=1, D_1=E. The positive small quadratic root
at |E|=1e-5 defines the finite threshold without an ill-conditioned eigenvalue search.
The paper's N in the crossover inset is treated as physical sites (odd L), unlike
the N A-unit-cell convention of its exact-state equations. Both rates will be shown.

For a trivial Hermitian SSH segment with M complete cells, intracell t3 and
intercell t4, its zero-energy inverse endpoint element is
(H_beta^-1)_(1,2M)=(-1)^(M+1)*t4^(M-1)/t3^M.
Schur elimination induces endpoint coupling of magnitude
tau_beta=t4*(t4/t3)^M, and zero diagonal self energies at E=0 by chiral symmetry.
This supplies a distinct analytic check of exponential tunneling. At small E and a
large beta gap the energy dependence is negligible; for a gapless beta segment it
cannot be replaced by a constant without checking the full matrix.
The supplement labels t3/t4=6,3.3,1 and 25 for both domains but omits absolute t4.
t4=0.5 is inferred from its Hermitian band edges [2.5,3.5] at ratio 6; this is an
explicit inference and cannot authenticate exact source arrays or parameter identity.

## Planned numerical criteria, before generation inspection

Use relative matrix residuals <=1e-11 for well-conditioned constructed eigenstates;
small-chain spectral agreement <=1e-9 in t2 units, and determinant checks in 60/90
decimal arithmetic for exponentially small couplings. Inspect critical points
separately; do not demand double-precision forward accuracy of a nonnormal matrix.
Reference plots are embedded rasters. Axis calibration and at least a one-pixel
coordinate uncertainty must be reported; a two-pixel spectral-envelope tolerance
tests the printed figure, not its unavailable author arrays. Quantitative curve
crowding and finite sampling limit what image agreement alone establishes.
Finite-size convergence at the actual N=46 is checked against N=23,92 and larger
where it distinguishes a thermodynamic assertion from a finite plotted result.
