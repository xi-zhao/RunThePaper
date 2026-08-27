# Paper Map

## Identity

- Paper ID: `quant-ph-9709029`
- Title: *Entanglement of Formation of an Arbitrary State of Two Qubits*
- Author: William K. Wootters
- Publication: PRL 80, 2245 (1998), DOI 10.1103/PhysRevLett.80.2245
- Local PDF/source: `raw/paper.pdf`, `paper-source/9709029.tex`

## Reproduction Goal

Re-derive and independently test every quantitative formula and construction in the Letter. The paper has no figures or tables. The unresolved additivity question is explicitly not claimed as solved.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Definitions and spin flip | Model | Pure and mixed-state entanglement definitions |
| Main formula | Central result | E(rho)=E(C(rho)) and concurrence spectrum |
| Constructive proof | Method | HJW decompositions, tilde orthogonality, lower bound |
| Zero-concurrence case | Boundary | Explicit separable decomposition condition |
| Discussion | Open problem | Additivity remains unresolved |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Eqs. (1)-(3) | convex-roof definition | verified |
| EQ002 | Eqs. (4)-(5) | spin flip | verified |
| EQ003 | Eqs. (6)-(8) | pure concurrence and entropy | verified |
| EQ004 | Eqs. (9)-(10) | mixed concurrence formula | verified |
| EQ005 | Eqs. (11)-(18) | HJW and lower bound | verified |
| EQ006 | Eqs. (23)-(24) | zero-concurrence construction | verified |
| EQ007 | Pure-state operational discussion | asymptotic entanglement rate | finite typical-subspace consequence verified numerically |
| EQ008 | Historical rank-two paragraph | earlier scope of the closed formula | verified independently; attribution source unavailable |
| EQ009 | Eqs. (19)-(22) | equal-entanglement optimal components | verified independently; Uhlmann attribution unavailable |
| EQ010 | Parenthetical after Eq. (19) | `m<=16` convexity bound | verified independently; attribution source unavailable |
| EQ011 | Closing pure-state interpretation | minimum transmitted-qubit rate | independently derived and verified by matching finite-block achievability and converse |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Figures/tables | None in paper | non-numeric | no pixel target |
| Random tests reported by Smolin | private communication | external result | independently replaced by a frozen 128-state campaign |

The authored scope also includes the pure-state communication-rate statement,
now closed by an independent rank-limited fidelity theorem and executable
finite-block boundary check. The prior rank-two scope, equal-entanglement
construction, and finite-dimensional ensemble bound remain separately traced.
External historical attributions remain explicit evidence limits rather than
being silently treated as locally proved.

## Assumptions

- Basis order is `00,01,10,11`; logarithms use base two.
- Random campaigns are reviewer-declared falsification grids, not undisclosed paper parameters.
