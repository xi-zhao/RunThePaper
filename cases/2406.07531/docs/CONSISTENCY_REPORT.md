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

- Si gap-convergence curves;
- 2D BN DOS;
- MgO and SrTiO3 spectral heat maps;
- Na spectral heat map and bandwidth;
- Na local-minus-full DOS;
- Na self-energy values through the sixth neighbour.

## Observations requiring future falsification

- Many production choices are absent from the main article.
- APS Supplement Tables S6/S7 are unavailable through the legitimate routes
  tested.
- The MgO value 8.22 eV is slightly above the quoted experimental range
  7.98-8.19 eV, but this small difference alone is not evidence of an error.
- The claim that Na corrections remain nonzero through the sixth neighbour
  cannot be independently quantified without a paper-scale self-energy.

Current classification: inconclusive; paper_error_candidates=0.
