# Final precision and size comparison: conditions and interpretation

The source is still arXiv:1202.5532v2. The random-field XXZ model, Jperp=1,
Jz=0.1, eta=5, open boundaries, central cut, natural-log entropy and original
time window are unchanged. Independent generation never reads source ordinates.
The declared convention is uniformly sampled half-filled product states for
each WHOLE chain length. The source does not specify magnetization sampling;
the independently checked free-variance identity favors this convention among
the two tested alternatives, without authenticating author sampling.
The old fair-independent-occupation wording in checks/derivation.md is historical;
the actual fixed-filling generators and ensemble-derivation.md govern this test.

## Exact population and refinement bookkeeping

All 96 original L20 disorder/state pairs are retained. The half-step result
uses dt=0.05, bond64, cutoff1e-11: 93 new rows, one completed repaired seed8,
and two previously completed identical controls. The quarter-step result uses
dt=0.025 with the same bond/cutoff on the frozen 26-member set. The higher-bond
result uses dt=0.025, bond128, cutoff1e-13 on exactly that same set.
The certainty indices and uniform-without-replacement random design are in
method.md; estimators.py implements and independently enumerates the unbiased
finite-population identities. No sample is removed, reweighted after seeing
its value, or inferred from a cancelled/unfinished scratch file.

The dense central-L10 finite-step Schur oracle supplies a fixed coefficient-one
control for the quarter-minus-half correction. Its different boundary is not
assumed equal to L20; the residual correction is design-unbiased. Report the
coefficient-zero comparison too. Statistical SEM, subsampling design uncertainty,
observed timestep/bond changes and reference width have separate meanings.
Negative variance estimates are flagged, never interpreted as zero uncertainty.

## Direct comparison of whole-chain ensembles

A central ten-site interval of a uniformly half-filled twenty-site chain has
hypergeometric particle number, not exactly five particles. It is a legitimate
variance control but cannot by itself represent the source's whole L10 curve.
For the actual size comparison, compute 12000 new independent fixed-N5 L10
interacting/free pairs at the SAME ten times. Separately regenerate the free
counterpart of each original 12000-member mixed-filling center control.

The old interacting controls were concatenated in 100-row completion order.
One independently recomputed complete ten-time ED anchor per original block
identifies that permutation. Require all 120 matches to be unique and below
1e-10; the observed maximum is zero. This recovers the pairing rather than
guessing that an unlabelled row has the same index as a newly generated row.

If Y is the central interacting result and f denotes a free result, the target is

  E[S20-f20] - E[S10_fixed-f10_fixed]
  = E[S20-f20-Y+f_center]
    + E[Y-f_center] - E[S10_fixed-f10_fixed].

Use the frozen nested estimator for the first term and the two independent
12000-member exact ensembles for the other terms. Add their variance estimates.
The same identity applies to pure-state particle-number variance. The variance
is taken within each quantum state before averaging over disorder.

## Criteria and what the evidence establishes

The original checker required the L20 paired entropy SEM below 0.02 nats,
and source comparisons within three combined error scales. Those criteria
remain unchanged. Original plot widths are not known calibrated SEMs and
correlated time points do not supply an independent multiple-test p-value.
For the direct size test, retain the same three-SEM comparison and show its
actual finite resolution. Reconstructing identical author arrays is not required.

Assess solver adequacy from all 96 half-step rows and all 26 paired refinements,
their independently validated kernel/oracle checks, actual per-step discarded
weights and the observed changes relative to the finite statistical resolution.
This adequacy assessment is made after seeing the refinement evidence; it is
not a preregistered rigorous bound or proof of asymptotic dt convergence.
The earlier 0.02-nat and three-scale criteria are not widened. A sum of discarded
weights is a diagnostic, not an entropy error bound. The checked QR-SVD fallback
reconstructs the original failed finite matrix without jitter or altered weights.

The supported statement is finite-time statistical compatibility of the source
curves and the small size effect at the resolved precision. It is not exact
equality of chain lengths or a proof of infinite-time localization/entropy growth.
L20 is evaluated at the ten originally frozen times, with nine nonzero comparisons
against the reference interpolated in log time; no values between these observed
times are asserted. Its figure uses markers without connecting generated segments.
The separate L10 check retains all 47 original reference times for each interaction.
Other original checks, including the previously retained saturation-interaction
discrepancy, retain their own evidence and qualifications.
