# Model and independent checks

Source: fixed arXiv 1202.5532v2, Eqs. (1)-(2), text pp. 1-4. No newer version is used.

For spin one-half, S^z=n-1/2. On an open nearest-neighbor chain,
H=sum_i [ (c_i^dagger c_{i+1}+h.c.)/2 + Jz (n_i-1/2)(n_{i+1}-1/2) ]
 + sum_i h_i(n_i-1/2), with h_i uniform in [-5,5], J_perp=1.
The transverse term has matrix element 1/2, not 1. A bit state of fixed N
remains in its N sector. This is an exact reduction, not an approximation.
The center cut gives coefficient matrices for each left-half charge q;
their squared singular values are the eigenvalues of rho_A. The generator
returns -sum p ln p (nats). Number variance is <N_A^2>-<N_A>^2 for each
pure-state realization, averaged afterwards; variance of the disorder mixture
would be a different quantity. Entropy is likewise averaged after evaluation.

The source specifies a center bond and uses TEBD; an open chain is inferred,
not explicitly named in the source. Boundary sensitivity is checked separately.
Random product state is interpreted as independent fair up/down choices; the
source does not specify a fixed magnetization ensemble. Saturation uses Neel.
No arbitrary normalization is fitted to the source plots. Natural logarithm
is our convention; source writes log without an explicit base.

Independent free-fermion formulation at Jz=0: propagate the initially occupied
orbitals with the L by L one-particle Hamiltonian. If f are the eigenvalues of
the restricted correlation matrix, S=-sum[f ln f+(1-f)ln(1-f)] and
Var(N_A)=sum f(1-f). This tests the interacting sector solver at its free limit.
An additional tensor-product Pauli construction and direct matrix exponential
test interacting small chains without using the sector Hamiltonian construction.
Norm, total charge, energy, density-matrix positivity and S_A=S_B are controls.
Late-time eigenvalue errors accumulate as t*delta(E); compare two LAPACK
drivers and explicitly measure the sensitivity up to the final time.

For a finite chain S <= (L/2)ln2. Linear late-time S versus L is evidence
for a volume law at the tested sizes, not a proof at infinite L. Comparing
S at finite late times is not taking entropy of the time-averaged density matrix.
The limiting operations Jz->0 and t->infinity can fail to commute: interaction
phases Jz*t remain order one no matter how small a nonzero Jz is if one waits.
This explains a possible singular perturbation, not a theorem of asymptotic
logarithmic growth for the microscopic XXZ chain.

Reference [22] states a consistent mechanism, not a solved XXZ derivation:
all longitudinal Ising terms commute with every local S^z, so particle density
is fixed. For one cross-cut pair H=J S_A^z S_B^z initially |+x,+x>, the reduced
eigenvalues are (1 +/- |cos(Jt/2)|)/2. At Jt=pi this gives ln2 entanglement with
unchanged local density and zero longitudinal particle current. Couplings of
size exp(-r/xi) can dephase at t~exp(r/xi), giving a logarithmic distance scale;
an extensive entropy density and sufficiently generic couplings are needed to
turn that scale into a growth law. We do not add a new long-range model as an
acceptance requirement or claim this proves the microscopic chain's long-time phase.

Local unitaries inside A or B preserve the Schmidt eigenvalues exactly; the
cross-cut term is necessary for growth. A local measurement's statistics are
determined by rho_A, but a single arbitrary local observable need not detect
its entropy. The paper does not establish eventual absence of particle or
energy transport and explicitly allows subdiffusion or an unobservably late crossover.

Sinai discussion is contextual: a short-range random force gives potential
barrier fluctuations of order sqrt(R); activated escape ln(t)~sqrt(R) yields
R~ln(t)^2. No mapping of the quantum XXZ dynamics to that stochastic model is
derived in this paper. The broad-rate-model discussion is likewise a possible
analogy, not a numerical target of this reproduction.

Pre-comparison criteria: small-chain formulation checks absolute errors below
1e-9 at t<=1e3; inspect phase-error growth separately at t up to 1e10. Disorder
uncertainty uses realization-level SEM, paired differences when the same fields
and states are used, and no selection of favorable realizations. Source vectors
will be calibrated to axis ticks; their coordinate precision is distinct from
unknown source sampling error. Report residuals in physical units and in our
SEM units, without equating a 2-SEM overlap with full reproduction.
