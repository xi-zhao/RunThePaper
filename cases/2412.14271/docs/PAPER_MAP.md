# Paper Map

## Identity

- Paper ID: `2412.14271`
- Published title: *Dissipative Phase Transition in the Two-Photon Dicke Model*
- Authors: Aanal Jayesh Shah, Peter Kirton, Simone Felicetti, Hadiseh Alaeian
- Formal publication: *Physical Review Letters* **135**, 173602 (2025)
- DOI: `10.1103/mz92-6l9g`
- Preprint: <https://arxiv.org/abs/2412.14271> (v1, 18 December 2024)
- Formal PDF: `raw/published.pdf` (SHA-256 `b296f832115c50803ad63121282708d75590a0a807ad2498486d02895dba823a`)
- Preprint PDF: `raw/paper.pdf` (SHA-256 `d5fff6d685bdcae16c762b0ea32bcc9998aa8b41c69a8324250517f3500afc4a`)
- TeX source: `paper-source/main.tex`; no author numerical program is present or used.
- Formal supplemental URL: <http://link.aps.org/supplemental/10.1103/mz92-6l9g>
  (authorization required when last checked on 2026-08-22; not frozen).
- Author-data repository: Zenodo DOI `10.5281/zenodo.17156911`; only its
  metadata and printed-parameter comparison may be consulted. Author numerical
  arrays are forbidden as runner inputs and cannot substitute for reproduction
  evidence.

## Reproduction Goal

Independently derive the Lindblad, mean-field/cumulant, exact-diagonalization,
quantum-trajectory, Wigner, and Liouvillian observables and regenerate every
available numerical panel. Fig. 1 is contextual schematic and is not redrawn.
Paper figures may be inspected only after independent data generation for
comparison/rendering; their pixels never enter the numerical calculation.

## Version Precedence

The formal PRL is authoritative. Relative to arXiv v1, published Fig. 2 uses
`N=5`, `omega_a=2 omega_c`, and `omega_c=1`, while v1 used `N=4` and
`omega_a=omega_c=1`. Published-main parameters override the v1 source. The APS
formal supplement currently requires authorization, and the available accepted
manuscript ends before the supplement. The v1 supplement is therefore used
only for items that the formal main text does not contradict. It is not used to
invent later formal-only content. Formal Figs. S3 and S4 remain two separate,
uncovered items until their source can be frozen and enumerated panel by panel.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main model | Hamiltonian, scaling, Lindblad jumps | Defines the finite and thermodynamic models. |
| Dissipative transition | Instability with one-photon loss; stabilization with two-photon loss | Main Figs. 2-3. |
| Wigner function | Phase-space evidence for coexistence and weak `Z4` symmetry | Main Fig. 4. |
| Supplemental EOM/stability | Mean-field and second-order cumulant equations plus Jacobians | v1 Figs. 5-6; formal S1-S2 inferred from the main references. |
| Supplemental convergence | Loss-rate and trajectory convergence | Formal S3-S5; S3-S4 source unavailable. |
| Supplemental symmetry | Rank-two Liouvillian kernel for pure two-photon loss | v1 Fig. 8; formal numbering unverified. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| DPT001 | Published Eqs. (1)-(2) | Collective-spin Hamiltonian and thermodynamic scaling | verified |
| DPT002 | Published Eqs. (3)-(5) | Lindblad generator and one/two-photon jumps | verified |
| DPT003 | v1 SM Eqs. (7)-(22) | One-photon mean-field fixed points and critical coupling | reconstructed against published parameters |
| DPT004 | v1 SM Eqs. (24)-(26) | One-photon Bogoliubov stability matrix | verified |
| DPT005 | v1 SM Eqs. (35)-(50) | Second-order cumulant equations with both losses | source verified; publication-version differences possible |
| DPT006 | v1 SM Eqs. (51)-(53) | Both-loss Bogoliubov stability | source verified; publication-version differences possible |
| DPT007 | v1 SM Eq. (54) | Quantum-trajectory ensemble and photonic partial trace | verified |
| DPT008 | standard displaced-parity identity | Wigner transform of independently generated photonic density matrix | independently verified |
| DPT009 | v1 SM pure-two-photon section | Parity-resolved Liouvillian kernel | verified |

## Figure/Table Inventory

The atomic inventory contains **34 visible or source-confirmed items**:
**31 eligible numerical items**, **29 covered**, **2 uncovered**, and
**3 excluded schematics**. Thus item coverage is **29/31 = 93.55%**. A target
may implement several items, but each subpanel is counted independently.

| Atomic item | Scientific object | Class | Decision |
| --- | --- | --- | --- |
| Main Fig. 1(a) | Cavity-emitter and loss-channel schematic | `schematic_context` | excluded |
| Main Fig. 1(b) | `Z4` symmetry sketch | `schematic_context` | excluded |
| Main Fig. 1(c) | `Z2` comparison sketch | `schematic_context` | excluded |
| Main Fig. 2(a) | Mean-field photon branch versus coupling | `theoretical_numerical` | covered by T001 |
| Main Fig. 2(b) | Mean-field spin branch versus coupling | `theoretical_numerical` | covered by T001 |
| Main Fig. 2(c) | Quantum photon occupation and cutoff drift | `theoretical_numerical` | covered by T001 |
| Main Fig. 2(d) | Quantum spin observable | `theoretical_numerical` | covered by T001 |
| Main Fig. 2(e) | Fock distribution at `M=60` | `theoretical_numerical` | covered by T001 |
| Main Fig. 2(f) | Fock distribution at `M=80` | `theoretical_numerical` | covered by T001 |
| Main Fig. 2(g) | Fock distribution at `M=100` | `theoretical_numerical` | covered by T001 |
| Main Fig. 3(a) | `N=5` normal-phase Fock distribution | `theoretical_numerical` | covered by T002 |
| Main Fig. 3(b) | `N=5` side-lobe distribution | `theoretical_numerical` | covered by T002 |
| Main Fig. 3(c) | `N=5` strong-coupling distribution | `theoretical_numerical` | covered by T002 |
| Main Fig. 3(d) | `N=15` normal-phase trajectory distribution | `theoretical_numerical` | covered by T002 |
| Main Fig. 3(e) | `N=15` side-lobe trajectory distribution | `theoretical_numerical` | covered by T002 |
| Main Fig. 3(f) | `N=15` strong-coupling distribution | `theoretical_numerical` | covered by T002 |
| Main Fig. 3(g) | Cumulant branches and ED/QT means | `theoretical_numerical` | covered by T002 |
| Main Fig. 4(a) | Finite-system normal-phase Wigner function | `theoretical_numerical` | covered by T003 |
| Main Fig. 4(b) | Finite-system coexistence Wigner function | `theoretical_numerical` | covered by T003 |
| Main Fig. 4(c) | Finite-system strong-coupling Wigner function | `theoretical_numerical` | covered by T003 |
| Main Fig. 4(d) | Large-system normal-phase Wigner function | `theoretical_numerical` | covered by T003 |
| Main Fig. 4(e) | Large-system coexistence Wigner function | `theoretical_numerical` | covered by T003 |
| Main Fig. 4(f) | Large-system strong-coupling Wigner function | `theoretical_numerical` | covered by T003 |
| Formal Fig. S1 / v1 Fig. 5(a) | One-loss normal-branch Bogoliubov spectrum | `theoretical_numerical` | covered by T004 |
| Formal Fig. S1 / v1 Fig. 5(b) | One-loss superradiant-branch spectrum | `theoretical_numerical` | covered by T004 |
| Formal Fig. S2 / v1 Fig. 6(a) | Both-loss normal-branch spectrum | `theoretical_numerical` | covered by T005 |
| Formal Fig. S2 / v1 Fig. 6(b) | Larger superradiant-branch spectrum | `theoretical_numerical` | covered by T005 |
| Formal Fig. S2 / v1 Fig. 6(c) | Smaller superradiant-branch spectrum | `theoretical_numerical` | covered by T005 |
| **Formal Fig. S3 (panel inventory unavailable)** | Loss-rate convergence observable confirmed by formal main text | `theoretical_numerical` | **uncovered: missing formal source input** |
| **Formal Fig. S4 (panel inventory unavailable)** | Loss-rate convergence observable confirmed by formal main text | `theoretical_numerical` | **uncovered: missing formal source input** |
| Formal Fig. S5 / v1 Fig. 7 | Quantum-trajectory convergence | `theoretical_numerical` | covered by T007 |
| v1 SM Fig. 8(a), formal numbering unverified | Parity-resolved Liouvillian eigenvalues | `theoretical_numerical` | covered by T008 |
| v1 SM Fig. 8(b), formal numbering unverified | Odd-parity Fock distribution | `theoretical_numerical` | covered by T008 |
| v1 SM Fig. 8(c), formal numbering unverified | Even-parity Fock distribution | `theoretical_numerical` | covered by T008 |

There is no separately counted text-only quantitative claim: every confirmed
quantitative claim is already carried by one or more numerical panels above.

## Uncovered Items

| Item | Direct current gap | Why it remains uncovered | Required closing action |
| --- | --- | --- | --- |
| Formal Fig. S3 | Formal supplement is not frozen; panel count, parameters, and plotted observable are unavailable. | Any implementation would guess the evaluation contract, so neither code nor an artifact can honestly be declared paper-exact. | Acquire and hash the formal supplement, enumerate every subpanel, derive its formulas/parameters, then decide whether a run is required. |
| Formal Fig. S4 | Formal supplement is not frozen; panel count, parameters, and plotted observable are unavailable. | The arXiv v1 supplement predates this formal-only item and cannot prove its content. | Acquire and hash the formal supplement, enumerate every subpanel, derive its formulas/parameters, then decide whether a run is required. |

Neither missing item is silently merged into a range, replaced with author
arrays, or treated as covered by a proxy figure. Both contribute zero to the
paper-level reproduction degree until independently covered.

## Other Fidelity Gaps

- Published main Figs. 3-4 require `N=15`, photon cutoffs up to 240, and many
  trajectories; paper-scale stochastic runs are a time tradeoff after a local
  feature run.
- The paper reports Gaussian-fit means but not the fitting windows/weights.
