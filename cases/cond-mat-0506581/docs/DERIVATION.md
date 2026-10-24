# Fixed-v2 model and checks

This is a same-agent derivation. It is not a formal proof-kernel certificate or an independent-context review. The only paper version is the supplied cond-mat/0506581v2 PDF/source archive. Parameters are t=a=1, intrinsic SO=0.06, Rashba=0.05, staggered v=0.1 (QSH) or 0.4 (ordinary insulator). v=0 is used only for the original inversion-symmetric zero-loop claim.

## Hamiltonian correspondence

Use the ordered basis (A up,A down,B up,B down), a1=(1/2,sqrt(3)/2), a2=(-1/2,sqrt(3)/2), d=(0,1/sqrt(3)), and qj=k.aj. Then x=(q1-q2)/2, y=(q1+q2)/2. Pauli matrices have the usual sy[0,1]=-i convention. In particular Gamma12=-sigma_y, Gamma15=sigma_z spin_z, Gamma23=-sigma_x spin_x, Gamma24=-sigma_x spin_y.

For the AB block, the three bonds have R=0,-a1,-a2. For delta=R+d from A to B, Eq.(1) gives t I + i lambda_R (-delta_y sx+delta_x sy)/|delta|, multiplied by exp(i k.R). For AA next neighbors R=a1-a2,a1,a2, the coefficients are -i,+i,-i times lambda_SO sz; BB has opposite signs. The first-then-second path cross product gives these signs (for R=a1, j=A(a1) to B(0) to A(0) gives positive nu). Fourier transforming yields every coefficient of Table I. A distinct checker enumerates geometric nearest/next-nearest bonds and common intermediate sites.

For a zigzag strip use A_j at j a1 and B_j at (j-1)a1+d, j=0,...,N-1, periodic along a1-a2. This is the degree-two zigzag termination. A hopping (a,b,n1,n2) connects row j to j+n1+n2+b-a with phase exp(-i k n2). The caption does not specify N. Original vector level counts and spacing identify N=30 (60 atomic sites); this inference is kept separate from source-specified couplings. Edge-localization and width checks test N=20,30,40. No author-specific code is used.

## Bulk gap and phase boundary

At K, q1=2pi/3,q2=-2pi/3, put D=3sqrt(3) lambda_SO. The four eigenvalues are -D-v, -D+v, D-sqrt(v^2+9 lambda_R^2), D+sqrt(v^2+9 lambda_R^2). For nonnegative v and in the weak-SO regime the middle levels cross when v=D-9 lambda_R^2/(4D). Its endpoints are v=3sqrt(3)lambda_SO and |lambda_R|=2sqrt(3)lambda_SO. The plotted symmetric lobe follows from v and lambda_R sign symmetries. At lambda_R=0 the low-energy gap is 2|D-v|. These Dirac-point formulas are checked against full-zone band minima in the figure's regime; they are not asserted as a global formula for arbitrary large SO or arbitrary couplings.

Spin-conserving blocks have opposite Haldane Chern integers. The lattice Berry-flux sum is an alternative to Pfaffian counting. A nonzero bulk gap along the interpolation from lambda_R=0 to 0.05 preserves its Z2 parity. This establishes the phase identification without using the source plot as input.

## Twisted supercell

For L1=N1(a1+a2), L2=N2(a1-a2), label primitive cells by p=m1+m2 and q=m1-m2 with equal parity, 0<=p<2N1, 0<=q<2N2. There are 2N1N2 primitive cells, 4N1N2 sites and 8N1N2 spin orbitals. Every bond crossing the p or q boundary receives exp(i w1 alpha1+i w2 alpha2). This seam gauge realizes the paper's large-unit-cell convention. It is not a uniform vector-potential gauge with an untransformed time-reversal operator. At N1=N2=2, half filling occupies 16 of 32 orbitals.

A distinct check compares its spectrum with the union of eight primitive-cell spectra satisfying q1+q2=(alpha1+2pi m1)/N1, q1-q2=(alpha2+2pi m2)/N2, m1=0,...,N1-1, m2=0,...,2N2-1. This directly tests seam phases and cell counting. Checking gauge-invariant spectra alone would not establish the Pfaffian convention; direct original-curve comparison and the TRIM check constrain that convention.

## Pfaffian and topology

For an orthonormal occupied frame U (columns), J=I_sites tensor i sy and M=U^dagger J U^*. J^T=-J implies M^T=-M. For two occupied bands P=M12; for a supercell use skew elimination. Independently, det M=P^2 and |P| is the square root of the product of one singular value from each repeated pair. At TR-invariant twists the occupied subspace is invariant under Theta, so M is unitary and |P|=1. An occupied subspace orthogonal to its TR image has M=0.

For a ket change |u'_i>=sum_j V_ij |u_j>, anti-linearity gives M'=V^* M V^dagger and P'=det(V)^* P. The v2 text instead prints det(V) P and exp(+2i theta) P. Its own bra-ket definition gives exp(-2i theta) P. A two-state example with P=1 and theta=pi/4 gives -i, while the printed transformation gives +i. This is an algebraic conjugation/sign discrepancy. It changes winding orientation, not zeros, |P|, or winding modulo two.

Around each isolated zero a local smooth frame is built by polar-aligning occupied states to the frame at the loop center. The alignment is valid when its smallest overlap singular value stays nonzero. Sum arg(P_next/P_current) on a closed loop to get the winding; TR partners have opposite winding. At v=0 inversion allows real P in appropriate patches, and isolated zeros become a line. Continuous small-v deformation with a gapped spectrum checks the same mod-2 class. A naive principal-square-root phase or raw eigensolver phases are not a valid implementation of Eq.(5). Global real-gauge patching and the precise i-delta prescription require care and must not be claimed checked merely from |P| plots.

## Edge protection and spin accumulation

For an antiunitary Theta with Theta^2=-1 and a Hermitian TR-even V, antisymmetry of <a|Theta b> gives <Theta u|V|u>=0. Thus a single time-reversed pair has no single-particle elastic backscattering matrix element. With two pairs, a TR-even inter-pair coupling is allowed; parity rather than the count itself is protected. This argument assumes TR symmetry, a bulk gap and the stated weak/elastic single-particle regime; it is not a proof about all disorder or all interacting edges.

One flux quantum shifts momenta by 2pi/L. A single edge particle-hole excitation changes the edge spin by <Sz>_L-<Sz>_R. Faraday's relation yields Eq.(3), with conductance normalized here to e/(2pi) and hbar=1. Sz conservation gives a difference of magnitude one; Rashba mixing allows smaller, Fermi-energy-dependent values. These values are checked from localized ribbon eigenstates and their velocity, not assigned spin labels.

## Many-body statement and limitations

Exterior-product multilinearity gives <Phi|Theta Phi>=det(U^dagger J U^*)=Pf(M)^2 for a noninteracting Slater determinant. An explicit small Fock-space calculation is a distinct check of the determinant identity. Equation (7) is proposed as a many-body generalization; the text says 'We suspect' its persistence under weak interactions. A square root requires branch/gauge choices, and the Slater identity alone does not prove an interacting invariant or stability theorem. The original conjecture is audited at its stated level; no new interacting lattice calculation is manufactured as a source result. The abstract's proposal and conclusion's stronger stability wording must be distinguished.

## Quantitative comparison and error criteria

Numerical arrays are independently generated before rendering. Reference paths are extracted only by comparison code from the fixed PDF's vector lines. For F2c, use the path-frame endpoints for alpha2/pi and |P|. For F1, calibrate k=0 from its original tick, k=pi from the symmetric midpoint, E=0 from its axis, E=1 from the top frame labeled 1. Retain original coordinates and extraction code. PDF coordinates are approximately 0.001 pt resolution, so transformed ordinate error is several times 1e-5; sampling/linear interpolation contributes separately. A 3e-4 envelope for vector-vertex energy/Pfaffian comparisons includes coordinate/calibration sensitivity; this is a post-exploration criterion, not preregistration. Full-range residuals and calibration perturbations are reported, rather than declaring agreement from linewidth. Linear algebra identity tolerance is 1e-10 in t units for small matrices; converged numerical zeros are checked below 1e-10. Finite grids establish observed minima and convergence, not a rigorous continuum error bound.

Exploration revealed a possible E -> -E relation between Table I and Figure 1. Both literal and reversed spectra are retained. The checker tests geometric Eq.(1), Table I, intrinsic-SO reversal, Rashba reversal, zero-Rashba control and width to discriminate an implementation/edge/parameter error from a source-sign convention. Agreement after an allowed explanatory transformation is not literal source-figure agreement, and cannot identify the author's implementation.

## Resolved clipping and cusp diagnostics

The original strip has uniformly spaced interior k samples at Delta k=2pi/120. At the E=+/-1 frame, additional vector vertices are clipping intersections of straight plotted segments, not additional eigenvalue evaluations. Comparing those vertices to a dense exact spectrum gives residuals up to 0.0048 t after energy reflection. The specific prediction of the clipping explanation is that linear interpolation of an independently generated 121-point spectrum at those coordinates restores the same approximately 2e-4 t agreement as the interior. Both comparisons are retained in checks/refined_comparison.json. This separates source graphical interpolation from a physical energy error; it does not erase the literal E-sign discrepancy.

For F2c the magnitude has a cusp at its zero. Interpolating a uniform 1001-point mesh across the cusp raises the apparent minimum to about 7e-4. The independently solved zero was added as an exact grid node, without consulting the source ordinate. The resulting full-source-vertex residual is about 1.3e-4. Its remaining source-plot discrepancy is reported as measured; it is not asserted to be solely floating-point or PDF rounding error.

## Literal constant-regulator problem in Eq.(5)

For a continuous real, single-valued P on a closed contour and a real nonzero constant delta, P+i delta lies entirely in one open half-plane. Its winding is exactly zero. Consequently, ordinary winding of log(P+i delta) cannot equal half the number of real sign changes when there are two sign changes. This conclusion is independent of floating-point precision and of the detailed Hamiltonian.

The fixed-v2 model provides such a numerical case at v=0. Use the half BZ 0<=q1<=pi, 0<=q2<=2pi and a smooth occupied frame constructed by radial projector transport from its center. Rotate the frame by a constant allowed U(2) phase so that P is real. Consecutive frame-overlap singular values remain bounded away from zero; the whole closed contour is defined by one continuous disk construction. The computed contour has two sign changes and no TRIM zero. Its constant-i-delta winding is zero for either regulator sign, while the stated half-sign-change count is one. Grid and transport refinements plus the lambda_R=0 control are retained in checks/line_index_audit.json.

For small nonzero v, the original point-zero definition gives an odd winding, and the bulk gap stays open as v tends to zero. Thus the QSH class and the line-zero topology remain supported. What fails literally is the constant regulator as a sufficient prescription for the real-zero-line case. An additional gauge-patch/transition rule or a physical TR-preserving small-v limiting prescription can resolve the index; those are extra specifications and are not silently substituted for the printed formula. This is a version-specific formula ambiguity/inconsistency, not an attribution to an unknown author program or a refutation of the QSH effect.
