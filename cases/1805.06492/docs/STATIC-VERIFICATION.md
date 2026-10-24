# Separate analytic checking of the fixed main-text claims

These are same-agent mathematical checks, not an independent reviewer or a proof kernel.
The derivation is in `checks/derivation.md`; this file uses alternative block determinants,
finite geometric sums, exact rational counterexamples and Schur complements to challenge it.
Numerical execution and its absent PRAgent receipts are recorded separately.

## A. Exact A boundary state: support within the stated short-range models

In A/B order, the A-only vector belongs to ker(S). The rectangular (N-1)-by-N S
has rows (b,c) on neighboring A columns; its null vector is the sequence (-b/c)^j.
Then H(v,0)=(d v,0). Applying the same rank argument to T-dagger proves the left
state with (-a*/c*)^j and eigenvalue d*. This proves Eqs.(3)-(4) for the original
models, including arbitrary complex hopping constants and momentum-independent d
in the open direction. It does not assert the result for arbitrary same-sublattice
dispersion or at a singular parameter without taking the limiting normalized state.

## B. B-termination sentence: a literal discrepancy, with an exact control

Use the original left-to-right site coordinates B0,A1,B1,A2,B2, with a=5/2,
b=-1/2,c=1, d arbitrary. The A1 equation at E=-d is B0+(5/2)B1=0.
The source sentence's substitution r_R -> 1/r_R gives (B0,B1,B2)=(1,2,4).
Its A1 residual is 1+(5/2)*2=6 and its A2 residual is 2+(5/2)*4=12, exactly,
so no scalar normalization repairs this state. The correct sequence is (1,-2/5,4/25),
which satisfies both equations exactly. This is a source-parameter example t1=1,
gamma=3,t2=1; it is not a new Hamiltonian or changed boundary convention.
The left state must use the other reciprocal, so the correct substitution is
r_R,B=1/r_L* and r_L,B=1/r_R*. The B biorthogonal product is still 1/q.
For the Hermitian control a=b=6/5, both prescriptions coincide and satisfy the rows.
Thus the literal individual-eigenvector sentence needs a left/right interchange;
the claimed swap of P=0 and P=1 regions, and unchanged transition positions, survives.
No statement about later paper revisions or author intent is made.

## C. Polarization and bulk attachment: conditional support

For any fixed q off the unit circle, the normalized geometric sum gives
<n>/N=1/[N(1-q)]-q^N/(1-q^N). For |q|<1 this tends to 0; for |q|>1 it tends to 1.
Consequently P tends to 1 or 0 respectively, independent of the phase of q.
This argument is separate from inspecting left/right wavefunctions individually.
The same product appears in the rectangular block spectrum: E^2-d^2=ab+c^2+
2c sqrt(ab)cos(theta). For the real original SSH/Rice-Mele parameters, the condition
that E=d joins the continuous open bulk spectrum is |ab/c^2|=1. For generic complex
f and g, the corresponding transfer-root magnitudes must be interpreted with their
complex phase and open-boundary dispersion, rather than imposing real momenta on a
periodic Bloch spectrum. The paper's short-range open models obey this construction.
At q=1 the finite state is extended and P_N=(N-1)/(2N), rather than a boundary integer.
At q=-1 and even N the overlap sum is zero. These critical cases must not be inserted
in a biorthogonal normalization formula with a zero denominator. Eq.(6) is shorthand
for the vanishing sum of signed inverse decay lengths away from infinite lengths.

## D. SSH criticality, even-chain edge count, and the PT variant

For the original SSH, q=(t1^2-gamma^2/4)/t2^2. The open-boundary criterion factors
into t1^2=gamma^2/4 +/- t2^2, exactly Eq.(9), for real solutions only.
Independently, the periodic 2-by-2 determinant vanishes when either off-diagonal
factor is zero, requiring k=0 or pi and t1=+/-gamma/2 +/-t2. These are inequivalent
sets at gamma=3,t2=1. Chiral symmetry enforces +/- energy pairs but finite even chains
hybridize the two edges; the asymptotic zero modes cannot be asserted exactly at N=46.
The semi-infinite left and right endpoint null vectors are both normalizable in the
reciprocal open representation precisely when |sqrt(ab)/c|<1; otherwise they are not.
This proves the two-edge versus zero-edge prediction for an even chain in the limit.
For the PT variant a=b=t1,d=i gamma/2, the same argument gives r_L=r_R=-t1/t2,
boundary energy +d at an A termination and -d at B, with attachment at |t1|=|t2|.
The bulk E=0 exceptional points are a different question from edge-bulk attachment.

## E. Rice-Mele connection and phase count: support

Eliminating q from q=+1 yields 4 t1 delta cos(kx)-gamma^2/4=0.
Eliminating q from q=-1 yields 2[t1^2+delta^2 cos^2(kx)]-gamma^2/4=0.
These are respectively the linear and quadratic solutions of Eq.(11), checked
without presuming its displayed expression. An interior root cos(kx) in (-1,1)
gives two momenta. Hence regions contain 0,2,4 or 6 roots; boundary coincidences
are not additional roots. At t1=delta=Delta=1,gamma=3 all six source roots exist.
The exactly solvable edge has E=-sin(kx); its crossings between separated bulk bands
follow the polarization and the attachment points. The d term cancels in E^2-d^2,
but remains in the independent periodic EP equation. An even chain has both endpoint
branches where P=1 in the thermodynamic limit. No Chern-number quantization theorem
for arbitrary non-Hermitian systems is inferred from these model checks.

## F. Boundary sensitivity: support for the exponential law, with a length convention

At the outer SSH transition ab=1 the open odd-chain characteristic polynomial is
the uniform-chain continuant D_L(E)=U_L(E/2), independently of its skin eigenvectors.
Adding the endpoint link gives exactly D_L-Gamma^2 D_(L-2)-Gamma(a^(N-1)+b^(N-1)).
For epsilon=|E|=1e-5, L=2N-1, D_L(epsilon)=+/-N epsilon+O(epsilon^3 N^3), giving
Gamma_c=epsilon N/(a^(N-1)+a^(-(N-1))) to leading order. Thus
log Gamma_c=log(epsilon N)-(N-1)log(a)+o(1), with a=(3+sqrt(13))/2.
The asymptotic rate is log(a) per A cell or log(a)/2 per physical site; the ln(N)
term changes a finite-range fit. The supplement's odd physical lengths 41..71 give
a slope near 0.58, while the limiting rate is 0.5973816. Its threshold is operational,
not a demonstration that every finite Gamma_c is an exact spectral singularity.
The supplement's printed negative multiplicative beta is not used; a negative
prefactor would not define a positive crossover amplitude. Only main-text alpha
and exponential scaling are required here, with the exact threshold independently solved.

## G. Domain-wall mechanism: support with limits on source-figure identity

The Hermitian beta chain's determinant at E=0 is (-1)^M t3^(2M). Its inverse
endpoint element follows from the unique path cofactor and equals
(-1)^(M+1) t4^(M-1)/t3^M. Schur elimination therefore gives a real effective
endpoint hopping of magnitude t4(t4/t3)^M. This exponential is not guessed from
an eigenvector plot. Direct inversion of the beta block checks the same transfer
factor, and full ring spectra test the direction of the crossover at source ratios.
When the gap is large and |E| is much smaller than it, replacing the self energy
by its E=0 value is controlled by resolvent analyticity. When t3=t4 the beta gap
closes as its length increases; a constant self energy is then insufficient, and the
full ring is used. The main mechanism is supported, while exact Fig.S6 array identity
is not established because t4 and the chain-length notation are not fully explicit.
The chosen t4=0.5 is visibly consistent with the original beta-band edges, and is
an inference. The original alpha domain and its boundary hoppings are retained.

## H. Numerical conditioning diagnosis is not an assertion about the authors

The same finite physical matrix under a permutation can produce different forward
eigenvalue errors in double precision near a Jordan degeneracy. Its characteristic
polynomial and exact eigenvalues do not change. The central open spectra are generated
in a reciprocal representation or with the exact rectangular-block expression.
For the domain-wall ring, conserving every neighbor-pair product and both directed
loop products preserves its cyclic characteristic polynomial under diagonal gauges.
High-precision evaluation of that original polynomial can check a gauge's numerical
roots. This evidence diagnoses our computation and demonstrates a possible mechanism
for raster discrepancies; it does not establish which eigensolver or grid the authors used.

## Scope audit

The abstract's exact modes, biorthogonal localization, SSH/Rice-Mele phase diagrams,
and the conclusion's boundary/domain-wall crossover all have explicit targets.
Figure 1 and Figure 2(a,b) are the three numerical leaves. Main-text formula groups
and the PT/termination remarks are separately assessed. Supplementary Haldane spectra
are outside the requested main-text scope; its general normalization argument was read.
The fixed source archive contains no author arrays or executable numerical solution;
it contains original embedded raster figures and the supplementary PDF. This limits
pointwise source matching but not the independent Hamiltonian calculation.
