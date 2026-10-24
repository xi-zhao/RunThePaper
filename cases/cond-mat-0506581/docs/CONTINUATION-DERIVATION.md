# Continuation audit: conditions, gauge control and conclusion boundaries

This continues the same cond-mat/0506581v2 attempt. No other Agent or model was
used. Original source bytes, all earlier calculations and their declared criteria
are retained. The 3e-4 band/Pfaffian display criterion was chosen after the original
exploration, not preregistered. No criterion is relaxed in this continuation.

## Independent topological check

For each fixed q2, form the occupied-space link U(q1)^dagger U(q1+dq1).
Its polar unitary removes finite-step loss of orthogonality. The ordered product
around q1 in [0,2pi) is the Wilson holonomy. Follow its two eigenphases as q2
goes from 0 to pi, matching consecutive phases by shortest circular distance.
Count crossings of a fixed phase modulo 2pi. At the time-reversal endpoints the
pair is degenerate; away from an endpoint reference phase, its crossing parity is
the Kramers partner-switching invariant. This computation uses neither Pfaffian
values nor the existing spin-Chern routine.

Meshes (81,61) and (161,121) and three distinct reference phases give the same
parity: one at (v,R)=(0.1,0.05),(0,0.05),(0.1,0), and zero at (0.4,0.05), with
SO=0.06 and t=1. Endpoint splittings are at roundoff level. These are numerical
checks at the original conditions and their controls, not a proof for arbitrary
Hamiltonians. Chern values in the spin-conserving limit and a still-open bulk gap
along the original Rashba deformation provide a separate cross-check.

## A failed old gauge control, not a paper error

The old periodic-frame test interpolated from Href=sigma_z tensor s_x to H(k).
Checking that interpolation on a finite grid did not establish that it stayed
gapped. A continuous three-variable minimization at v=0.4, R=0.05 finds a middle
gap below 7e-12 at (q1,q2,t) approximately (2.046148,4.140029,0.788925).
The previous grid had reported a minimum of about 0.076. Thus its apparently
periodic boundary frame need not extend smoothly through the enclosed region.
Its odd winding in the ordinary insulator is a failure of that auxiliary gauge
construction. Do not use checks/periodic_gauge_audit.json as corroborating evidence
for either an invariant or an original-paper inconsistency. The radial-disk
calculation gives zero winding there and the independent Wilson calculation
agrees. The new minimization is a counterexample to the old gapped-path assertion;
failure to find a closing elsewhere would not be a global gap proof.

## Real-zero-line regulator remains a precisely bounded question

For a continuous single-valued real P on a closed contour, P+i delta lies in a
single open half-plane for every fixed nonzero real delta, so its ordinary winding
is zero. This elementary fact remains valid. The old radial-disk calculation
exhibits two real sign changes and zero constant-regulator winding. However, that
disk frame alone does not establish all torus sewing and gauge-patch assumptions
in the paper's real-gauge statement. The failed periodic-frame control cannot
close this gap. Accordingly the literal real-regulator check remains inconclusive
at the source's full intended gauge conditions, not a demonstrated refutation of
Eq.(5). A small nonzero staggered potential and the Wilson loop establish the odd
physical phase without relying on that regulator. The latter is an explicitly
separate limiting prescription, not a silent replacement of the original formula.

## Other local discrepancies and controls

Under the printed ket transformation u'_i=U_ij u_j, anti-linearity gives
M'=U* M U^dagger and Pf(M')=det(U)* Pf(M). A constant common ket phase pi/4 maps
P=1 to -i, not +i. The conjugation discrepancy reverses winding orientation but
not its parity. This is a local algebraic statement, not a failure of the QSH
phase. The energy-reflected source-figure comparison remains a labelled variant;
literal band signs and reflected residuals are both reported. Numerical matching
cannot identify the author's implementation. Ribbon width 30 and graphical
sampling were inferred from the source plot and are disclosed, not source-given
parameters. Original reference ordinates never enter the generation program.

For edge protection, use Theta=(I_channel tensor i s_y)K. For one Kramers pair a
Hermitian TR-even potential has zero backscattering matrix element by the
antiunitary antisymmetry identity. For two helical pairs, V=tau_y tensor s_x is
Hermitian and TR-even; its channel-1-up to channel-2-down matrix element has
magnitude one, while the within-pair element vanishes. This explicit control is
computed rather than merely assigning the value one.

The Slater overlap determinant identity is exact for noninteracting occupied
orbitals and is checked by explicit Fock-space coefficients. The source says
"We suspect" for weak interactions; no independent interacting theorem or new
interacting simulation is claimed or added as a completion requirement.
