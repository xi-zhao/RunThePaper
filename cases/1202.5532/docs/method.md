# Population refinement: fixed model and explicit uncertainty

The target remains arXiv:1202.5532v2, Figures 1(a) and 2(a), L=20,
J_perp=1, J_z=0.1, uniform fields in [-5,5], open boundaries, central cut,
and the previously declared uniformly sampled ten-particle product-state ensemble.
The source's magnetization sampling is unspecified. No source ordinate is used
to generate a trajectory, select a seed, or choose a control coefficient.

## Frozen continuation design

1. All 96 existing disorder/state pairs are retained. The full-population
   computation uses dt=0.05, bond<=64, discarded-weight cutoff=1e-11.
   Indices 0 and 1 already have exactly these parameters in observed experiment
   7f5a67a1-71b0-4d9c-aaf8-73f57179449d; only indices 2..95 are recomputed.
   Changing both dt and bond relative to the original calculation does not
   identify their individual contributions.
2. A further dt=0.025 calculation at the same bond/cutoff uses four certainty
   indices C={0,1,54,63}, plus a simple random sample of m=22 from the other
   K=92 indices. Indices 54 and 63 are included because of the PREVIOUS coarse
   truncation violations, not a favorable refined result. Indices 0 and 1 reuse
   the existing quarter-step receipt. The RNG seed and complete frame/sample
   were frozen before the new quarter-step outputs. No unfinished or adverse
   trajectory can be dropped from the prescribed estimator.
3. A planned same-subset bond check uses dt=0.025, bond<=128, cutoff=1e-13.
   Its configuration is not execution evidence. It must remain unexecuted or
   pending unless an actual receipt establishes completion.

Neither 96 long-chain trajectories nor 26 refinement controls constitute the
author's >10000 L=20 trajectories. Statistical efficiency is not that sample count.

## Independent finite-step oracle

For each of the 96 matching central ten-site chains, construct the full
fixed-particle-sector Strang unitary, using dense two-site gates and no MPS
truncation. A unitary Schur decomposition gives U=Q diag(exp(i theta)) Q^dagger;
at integer k=t/dt, propagate with Q diag(exp(i k theta)) Q^dagger. This avoids
accumulating 160000 matrix multiplications and retains the chosen finite-step
operator, not the exact Hamiltonian evolution. Independently diagonalize the
continuous Hamiltonian for the exact reference. Report unitarity, off-diagonal
Schur residual, state normalization and comparison against the existing MPS
implementation on L=4,6,8 at three time steps. The same Agent checks the work;
a different mathematical implementation is not a second research context.

The central interval starts at long-chain site 5. Long-chain even bonds are
therefore locally odd: the parity-inherited oracle has odd-half/even-full/
odd-half layers. The opposite local convention is retained as a diagnostic,
not silently substituted. Boundary-field partitioning on the isolated center
is an approximation to the long chain, so the oracle is a variance control,
never an assumed exact replacement for L=20.

Initial small-chain checks with cutoff=1e-15 failed the unchanged 1e-10
observable-agreement threshold (maximum difference about 1.43e-8 despite
infidelity below 7e-13). Tiny discarded probabilities can produce larger
amplitude/observable changes. Tightening only these algebra controls to
cutoff=1e-24 reduced the maximum disagreement to 1.15e-13. The threshold was
not relaxed. Failed attempts ae45dbb9-754c-44c0-a874-f41e7335f90f and
7bd07ac0-fad2-4e17-a4db-2a8b1961191b remain in the native history.

## Design-based partial-refinement estimator

Let X_i be the full-population L=20 half-step result, Y_i the exact central
L=10 result, and D_i the central oracle quarter-minus-half change. All these
are known for N=96 when the full-population run finishes. Let F_i be the
quarter-step (or separately bond-refined) L=20 result, observed for C and R.
Define a_i=X_i-Y_i+D_i and r_i=F_i-X_i-D_i. The coefficient of D is fixed at
one; it is not estimated from the new quarter-step results or the paper.

The estimate of the finite 96-sample mean of F-Y is

    z_hat = mean(a) + (sum_C r + K*mean_R r)/N.

It is design-unbiased, conditional on the saved 96 samples and all potential
refined outputs, because R is a uniform sample without replacement. The oracle
does not assume equality of the two chain lengths. A direct estimator with
D=0 is also retained, including its possibly larger uncertainty.

The unbiased conditional design-variance estimate is

    v_design = (K/N)^2 * (1-m/K) * sample_variance_R(r)/m.

To estimate the ordinary disorder variance of the fine-level control residual,
use the unbiased squared-sum estimate

    q_hat = sum_all a^2 + sum_C(2*a*r+r^2) + (K/m)*sum_R(2*a*r+r^2),
    s_z2_hat = [q_hat - N*(z_hat^2-v_design)]/(N-1).

The correction by v_design is essential: z_hat^2 alone overestimates the
squared finite-population mean. Under independent identically distributed
original disorder samples and the independent 12000-member exact-center
control ensemble C10, the estimated variance of z_hat + mean(C10) is

    s_z2_hat/N + v_design + sample_variance(C10)/12000.

Report the components separately. A negative variance estimate is flagged,
not made into evidence of zero uncertainty. Enumerating all subsamples of a
small artificial population checks these identities by a distinct finite
calculation. SEM is not a rigorous bound, and a normal confidence claim is
not warranted merely by these formulas, especially for rare resonances.

## Scientific stopping boundary

Sampling uncertainty, finite-step bias, accumulated truncation, and source
convention uncertainty are distinct. Compare half-to-quarter at fixed bond,
then bond growth at fixed quarter step, before interpreting a narrow error bar.
The source's per-step discarded-weight <1e-6 requirement is necessary but does
not bound accumulated observable error. Smaller-chain quadratic convergence
does not establish L=20 convergence. No object is marked complete on the basis
of configuration files, partial scratch output, or an execution success alone.
