# Formula Verification

All 18 equation cards are open for numerical use: each has a pinpointed paper
source, a derivation, an executable code reference and at least one independent
symbolic, limiting or numerical check.

| Cards | Result |
| --- | --- |
| EQ001-EQ002, EQ012 | continuum basis and spectra pass direct diagonalization |
| EQ003 | Fukui-grid Chern numbers are opposite unit integers |
| EQ004 | lattice Hermiticity, analytic gap and flat-band limit pass |
| EQ005 | explicit two/four-terminal currents reproduce Fig. 2 labels |
| EQ006-EQ007 | explicit first-star matrix plus dimensional SI estimates reproduce the stated scales, with omitted material constants disclosed |
| EQ008 | independently derived shell coefficients feed the closed flow and give 14.864 K self-consistently |
| EQ009 | full-BZ, bulk-gap-selected and baseline-subtracted spectral flow resolves both boundaries at all subcritical Rashba ratios across three widths and nested grids |
| EQ010 | the TR scattering constraint and random scalar-disorder ensemble have no elastic backscatter |
| EQ011 | operator construction gives dimension 4; independent `u,T` fits give exponents -2 and -5 |
| EQ013 | explicit 8x8 first-star projection matches `sigma_z tau_z s_z` to `8.9e-16` |
| EQ014 | conventional-current full-BZ Kubo is a verified proxy, not the missing cited conserved-current definition |
| EQ015 | one-loop matrix shell integration derives 1/4 and 1/2 without circular constants |
| EQ016 | an independent interband Lindhard integral converges to `Pi(q) ~ -q/4` and yields the screened `q^-1` law |
| EQ017 | exhaustive mass search verifies the edge Zeeman gap and a generic intervalley proxy; continuous optimization falsifies the minimal translation-preserving Rashba/Zeeman/staggered path, leaving the paper's unspecified bulk terms unresolved |
| EQ018 | finite-cylinder spectral flow permutes one level and pumps one `hbar` |

Open questions in cards are provenance boundaries, not failed algebra: the
finite ribbon width/grid, finite lattice Rashba normalization, exact conserved
spin-current definition, the parallel-field connecting terms, graphene lattice
constant and Fermi velocity are not all printed in the target publication.  A
formula gate being open means its declared mathematical object is verified; it
does not upgrade a declared proxy to a paper-exact observable.
The authoritative machine result is `outputs/checks/formula_verification.json`.
