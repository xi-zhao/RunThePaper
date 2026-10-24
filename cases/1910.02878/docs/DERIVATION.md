# Two boundaries, finite flux, and a genuinely coupled matrix response

This continues fixed 1910.02878v4. All original figure parameters and previous
criteria remain unchanged. New models below are labelled diagnostic examples
for a universal proof, not substituted author plots or new completion targets.

## 1. The full-spectrum one-sided inclusion is itself too strong

The source's Eq. (5), supplement SIV, claims that the limit of ALL finite-open
eigenvalues belongs to the spectrum of the fixed left-boundary half-line.
Consider the local two-band symbol

    h(z) = [[0, u + z^-1], [2u + 2z, 3]],  u=0 or 1/5.

Here the finite matrix has upper block [[0,0],[2,0]], lower block
[[0,1],[0,0]], and the displayed onsite block. It is a bounded, constant
spin-similarity of a Hermitian staggered SSH chain; the similarity condition
number is sqrt(2), independent of N. It is therefore genuinely non-Hermitian,
but is NOT a non-Hermitian skin-effect counterexample.

At u=0, finite chains decompose into the left dangling state at 0, the right
dangling state at 3, and N-1 dimers [[0,1],[2,3]]. Thus

    det(xI-H_N) = x*(x-3)*[x*(x-3)-2]^(N-1).

The left half-line contains the dangling state 0 and infinitely many dimers,
so its spectrum is {0,(3-sqrt(17))/2,(3+sqrt(17))/2}: it does NOT contain 3.
Yet 3 is an exact eigenvalue of every finite chain. The right half-line has
the missing dangling state. Transposing a finite matrix does not repair this:
its right and left eigenvectors for this isolated state both occupy the SAME
right end, a possibility omitted from the source's list of cases in SIV.

An independent bounded inverse test is possible without a spurious second
boundary. Let S be the unilateral isometry (S*S=I, SS*=I-P0). At energy 3,

    H_L-3 = [[-3I,S],[2S*,0]],
    (H_L-3)^-1 = [[-P0/3,S/2],[S*,3I/2]].

Multiplication gives the identity on the half-line. The generator verifies
it on arbitrary compact-support complex inputs with enough zero padding;
the checker also verifies exact finite characteristic polynomials. Using an
ordinary finite truncation as a half-line oracle would add the very right
edge state in question and would be an invalid check.

This is not restricted to a disconnected dimer limit. For u=1/5, after the
constant spin similarity the off-diagonal block is sqrt(2)*(uI+S).
Its squared singular operator is the scalar Jacobi operator
2*[(1+u^2)I+u(S+S*)]. The left spectrum has edge 0 and the two bulk intervals
given by (E)(E-3)=2*|u+exp(ik)|^2. Its distance from 3 is exactly

    [sqrt(9+8*(1-u)^2)-3]/2 = 0.37882942280559... .

For finite Q_N=uI+S_N, the trial y_j=(-u)^(N-j) has only a first-row
residual u*(-u)^(N-1). Hence s_min(Q_N)<=u^N, and the exact block eigenvalue
relation E(E-3)=2*s_j(Q_N)^2 gives a finite eigenvalue converging to 3 with
distance at most (2/3)*u^(2N). The one-sided inclusion still fails. Tiny
finite differences below double precision are certified by this inequality,
not inferred from an eigensolver returning exactly 3.

For a full-spectrum finite-section result both terminations must be accounted
for, or isolated end modes must explicitly be excluded from a bulk statement.
No claim is made here to prove the most general replacement theorem.
The independent general operator-theory comparison is the two-half-space
distinction in Koekenbier and Schulz-Baldes, Section 3.1, DOI 10.4171/JST/524;
we do not import that work's numerical examples or treat its generic hypotheses
as part of this fixed source. Its role is a general mathematical reference.

## 2. A class-A phase-transition argument not using either false step

Let h(k) be an m-band finite-range periodic symbol with det(h(k)-E)!=0.
Make an N-cell ring with boundary phase phi. A unitary twisted Fourier basis
gives the EXACT finite determinant identity

    det(H_ring(phi)-E) = product_j det[h((phi+2*pi*j)/N)-E].

As phi traverses one cycle, the N adjacent momentum intervals cover one
Brillouin zone. Its determinant winding is consequently exactly W(E), not
N*W(E). The finite open chain has no phi dependence, so if it avoids E its
flux winding is zero. Scaling all wrapping terms continuously from one to
zero must therefore encounter a determinant zero somewhere in (cut,phi)
whenever W(E)!=0. If E is already an open eigenvalue, the endpoint is already
gapless. This proves a finite-boundary class-A point-gap closing without
assuming a common imaginary-gauge intersection or one-sided spectral inclusion.

This is a topology-of-the-flux-family statement. By itself it does not prove
where in the cut parameter a crossing occurs, how much of the open spectrum
moves, an extensive localized eigenvector basis, or every symmetry-protected
version of the paper's physical theorem. Those are not silently inferred.

## 3. Matrix boundary correction and an exact spectral-exclusion certificate

For ANY finite-range block chain with an exponentially localized right
half-line eigenmode v, truncate v to N cells. The residual r=(H_N-E)v_N is
supported at the remote boundary. For a fixed initial segment h of v with
||h||>0, the boundary-to-boundary matrix

    Delta_N = -r*h*/||h||^2

annihilates that residual exactly and is exponentially small. A left-mode
version follows by taking adjoints. Without a bound on distance to the
unperturbed eigenvalues, this alone is NOT a quantitative spectral-motion
claim, and without an index/mode-existence argument it is not universal skin
physics. The conditional construction itself is general, not scalar only.

We test it on the irreducible noncommuting two-band matrices

    A=diag(2,6/5), B=diag(1/2,4/5), C=[[0,1/10],[1/25,0]], E=i/5.

A has distinct eigenvectors and C mixes them, so these matrices have no
common invariant spin subspace. The polynomial det[A*z^2+(C-E)z+B] has four
roots inside the unit circle, giving winding +2 under our stated upper-block
Fourier convention. (Right/left sign conventions in other Toeplitz orderings
are reversed; the nonzero index is what is used here.)

For each root z_j use u_j=[-z_j/10,2z_j^2-E*z_j+1/2]^T. The three
smallest-modulus roots and the 2x2-minor null vector of [u_1,u_2,u_3] give
v_0=0 and v_n=sum c_j*u_j*z_j^n. No source curve or author realization enters.
Adding A*v_(N+1)*v_1*/||v_1||^2 in the (last,first) cell block makes E an
EXACT finite eigenvalue. The generator checks the recurrence at 100 digits.

To avoid trusting nonnormal double-precision eigenvalue distances, the checker
constructs a separate rational certificate. Substituting z=i*x at E=i/5
gives the real rational quartic

    (12/5)x^4-(16/25)x^3-(539/250)x^2+(13/50)x+2/5.

Exact real-root isolation encloses its four simple roots to width <1e-65.
For |E-i/5|<=1e-5, Rouche bounds put one root in each radius-1e-4 disk
about the rational imaginary centers. On each circle the change in the
polynomial is bounded by

    (16/5)*delta*M^3+(2*delta/5+delta^2)*M^2+(13/10)*delta*M.

All comparisons use rational arithmetic. The boundary secular determinant is
the determinant of [U;U diag(z_j^(N+1))]. Its six terms have coefficients
det(U_I)*det(U_Ic). The pair-minor identity

    det(u_j,u_k)=(1/10)*(z_j-z_k)*(2*z_j*z_k-1/2)

supplies uniform rational coefficient bounds. The term with the two largest
root moduli strictly dominates the other five for every N>=15. Thus the
ENTIRE disk |E-i/5|<=1e-5 contains no unperturbed eigenvalue for every N>=15.
This is a finite-spectrum exclusion, not a singular-value proxy or sampled
circle check. The boundary correction therefore produces actual eigenvalue
motion of at least 1e-5 in this genuinely coupled example.

An additional rational bound uses ||A||=2, the pair-minor upper bounds,
and |(v_1)_first|=(1/200)*product_{j<k<=3}|z_j-z_k| to bound the
boundary-link norm by K*rho^(N+1), rho<1. It turns the exponential sensitivity
into an inspectable inequality rather than reliance on tiny floating outputs.
The certificate is ordinary exact-arithmetic mathematics with explicitly
checked inequalities, not proof-assistant or formal-kernel certification.

## What remains

The full-spectrum single-termination Eq. (5) is refuted under its literal
unrestricted block-chain reading. A class-A flux closing is proved, and a
genuinely coupled matrix example has certified exponential boundary spectral
sensitivity. The source's universal physical TII.proof_scope remains separate:
these results do not promote a boundary-pseudomode construction into every
symmetry class's finite bulk eigenstate theorem, or convert a failed auxiliary
proof step into a counterexample to the physical claim. Prior results and
original targets remain intact.
