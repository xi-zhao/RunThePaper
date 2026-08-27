# Consistency Report

## Passed

- B_DM preserves the impurity mean-field 1-RDM.
- The embedding basis remains orthonormal.
- Equation (2) removes and restores the Hartree-Fock contribution exactly.
- Equation (4) has the correct GW limiting case.
- Lehmann and Dyson Green functions agree.
- The noninteracting self-energy vanishes.
- The retarded diagonal self-energy is causal.
- The spectral-weight and particle-number checks pass.
- The local-only counterfactual zeros only interatomic blocks.
- The finite real/momentum transform round-trips.

## Not yet tested against the paper

- all 10 Si gap-convergence/reference series in Fig. 2(a);
- all 6 displayed 2D BN DOS/reference series in Fig. 2(b);
- both numerical layers in each MgO and SrTiO3 band-structure panel;
- the 3 theoretical Na layers in Fig. 4(a);
- the Na local-minus-full DOS heat map;
- all 4 real/imaginary Na self-energy series in Fig. 4(c);
- Supplement Tables S6 and S7.

That is 30 known eligible items and 0 currently covered items. The formal
supplement may contain additional numerical items; its remainder is a source
scope blocker, not silently treated as empty.

## Observations requiring future falsification

- Many production choices are absent from the accessible main article.
- APS Supplement Tables S6/S7 and the rest of the formal supplement are
  unavailable through the legitimate routes tested.
- The MgO value 8.22 eV is slightly above the quoted experimental range
  7.98-8.19 eV, but this small difference alone is not evidence of an error.
- The claim that Na corrections remain nonzero through the sixth neighbour
  cannot be independently quantified without a paper-scale self-energy.

Current classification: inconclusive; paper_error_candidates=0. Root cause is
`unresolved/open`: without the formal supplement, the audit cannot confirm a
publication omission. A production-code fault remains `not_excluded` because
only the small-system method-validation path has executed.
