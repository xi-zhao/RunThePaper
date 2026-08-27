# Paper Map

## Identity

- Paper ID: `2602.12212`
- Preprint identity: `arXiv:2602.12212v3`
- Title: *Quantum-Coherent Thermodynamics: Leaf Typicality via Minimum-Variance Foliation*
- Authors: Maurizio Fagotti
- Source: <https://arxiv.org/abs/2602.12212v3>
- Formal publication: unverified as of 2026-07-26; do not treat the arXiv DOI as a journal DOI
- Local PDF: `raw/2602.12212v3.pdf`
- Local source archive: `raw/2602.12212v3.tar`
- Extracted TeX/source figures: `paper-source/`

## Reproduction Goal

Independently reconstruct the minimum-variance decomposition, verify its
defining identities, and reproduce every active numerical result in the main
text and Supplemental Material. The primary scientific targets are:

1. the spin-1 leaf geometry and leaf-canonical curves;
2. finite-size leaf-typicality diagnostics for nonintegrable and integrable
   spin chains;
3. representative-state dynamics;
4. spectral-compression diagnostics.

All reader-facing plots must be generated from case-local structured data.
Source PDFs are references only and never count as reproduction data. The
paper supplies no author data or numerical code, so exact curve-level
comparison will use independently generated numerics plus explicitly labelled
digitized or visual reference features.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Introduction | Product/physics motivation | Generalizes thermodynamic ensembles away from the commuting leaf. |
| Coherent energy fluctuations | Core variational model | Defines minimum-variance decompositions and their QFI relation. |
| Leaf canonical ensemble | Thermodynamic construction | Gibbs weights are applied to the effective state Hamiltonian inside a fixed leaf. |
| Quantifying energy (in)coherence | Leaf-level observable | Uses the barycenter von Neumann entropy as an incoherence indicator. |
| Examples | Low-dimensional geometry | Spin-1/2 analytic chords and a spin-1 three-dimensional subspace. |
| Leaf typicality hypothesis | Main numerical claim | Defines the shell outlier diagnostic and tests it on spin chains up to \(L=12\). |
| End Matter: QFI and optimal variance | Structural identities | Establishes leaf-invariant SLD and QFI density statements. |
| End Matter: compression | Complexity claim | Relates the optimal ensemble to the smallest compatible energy window. |
| Supplemental: additional tests | Numerical breadth | All one- and nearest-neighbour two-site observables; integrable counterexample. |
| Supplemental: spectral compression | Numerical mechanism | Diagonal-entropy participation and entropy-density gain. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Eq. (2), `eq:family` | Convex-roof minimum of ensemble-averaged energy variance | verified by Yu construction and QFI identity |
| EQ002 | Eq. (3), `eq:Hrho` | Lyapunov equation defining \(H_\rho\) | verified; thermal `sech` and density-eigenvalue forms agree |
| EQ003 | Eq. (4), `eq:Yu` | Maps eigenvectors of \(H_\rho\) to optimal representatives and populations | verified by reconstruction, norm, population, and energy identities |
| EQ004 | Eq. (7), `eq:leaf-canonical` | Leaf-canonical ensemble at fixed barycenter | verified analytically for the spin-1 target |
| EQ005 | Eq. (8), `eq:leaf_typicality` | Local observable in an optimal representative | implemented and range/monotonicity checked |
| EQ006 | Eq. (9), `eq:H` | Spin-chain Hamiltonian used by all many-body targets | verified Hermitian; periodic boundary reconstructed from notation and source-curve agreement |
| EQ007 | End Matter, `eq:Lyapunov` | Symmetric logarithmic derivative | verified through equivalent QFI/minimum-variance identity |
| EQ008 | End Matter, `eq:EVFO` | QFI as expectation of an extensive commutator | verified spectrally against four times optimal average variance |
| EQ009 | Supplemental spectral-compression definitions | Diagonal entropy and entropy-density gain | implemented; participation and positive-gain checks pass |
| M001 | Main Fig. 2 caption/text | Shells contain \(O(\sqrt d)\) consecutive \(H_\rho\) levels; count \(N_\Delta\) outliers | reconstructed as centred `round(sqrt(d))`; disclosed |
| M002 | Main Fig. 2 caption/text | Choose dynamics representative by minimizing \(\delta_i\) and define a \(\delta\)-shell | minimizer and shell exact; confidence quantiles reconstructed and disclosed |
| M003 | Supplemental captions | Re-run the same diagnostic over the full local Pauli basis and swapped integrable dynamics | implemented for all 12 observables and paper sizes |

## Figure/Table Inventory

| Figure region | Atomic panels | Target mapping | Notes |
| --- | ---: | --- | --- |
| Main Fig. 1 | 2 | T001 | Two calculated viewing angles in `foliation3d3.pdf`. |
| Main Fig. 2 left | 6 | T002 | Two observables by three temperatures in `fig1.pdf`. |
| Main Fig. 2 right | 1 | T003 | Exact mixed/representative dynamics in `dyn.pdf`. |
| Supp. Fig. S1 | 12 | T004 | Full 12-observable grid, \(\beta=0.25\), `figtot0dot25.pdf`. |
| Supp. Fig. S2 | 12 | T005 | Full 12-observable grid, \(\beta=0.75\), `figtot0dot75.pdf`. |
| Supp. Fig. S3 | 12 | T006 | Full 12-observable grid, \(\beta=1.75\), `figtot1dot75.pdf`. |
| Supp. Fig. S4 | 12 | T007 | Full 12-observable integrable counterexample, `figtot0dot25int.pdf`. |
| Supp. Fig. S5 first row | 3 | T008A | Main-text Hamiltonian spectral compression, `fignum.pdf`. |
| Supp. Fig. S5 second row | 3 | T008B | Supplemental Hamiltonian spectral compression, `fignum1.pdf`. |
| Supp. Fig. S6 | 2 | T009 | Two Hamiltonian-family entropy-density-gain panels, `figcompression.pdf`. |

The denominator is therefore 65 theoretical numerical panels: 9 main-text and
56 supplemental. All are mapped to an existing independently generated target;
none is experimental, deferred, or silently grouped for scoring. The active
source contains no table, so there is no table item or placeholder exclusion.

## Assumptions

- The site sum in Eq. (9) is interpreted with periodic boundaries because the
  term \(\ell+1\) is used without an edge exception; this must be tested
  against source-figure symmetries and spectra.
- “All local observables” means the traceless Hermitian Pauli-string basis on
  one site and on two neighbouring sites, excluding the identity.
- Because the exact shell width/edge handling is omitted, it is a
  reconstruction variable, not silently assumed paper metadata.
- The A100 profile documented in `PRAgent-workflow/REMOTE_COMPUTE_RUNBOOK.md`
  (80 GB GPU, about 125 GiB host memory) is the preferred accelerator path.
  Its JupyterHub endpoint was unreachable during this run, so the exact
  \(L=12\) workload was completed with the same NumPy model locally.
