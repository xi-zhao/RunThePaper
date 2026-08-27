# Paper Map

## Identity

- Paper ID: `2512.08279`
- Title: *Programmable Open Quantum Systems*
- Authors: Mingrui Jing, Mengbo Guo, Lin Zhu, Hongshun Yao, Xin Wang
- Formal publication: *Physical Review Letters* **137**, 040403 (2026)
- DOI: `10.1103/yqlr-2dhr`
- Preprint: `arXiv:2512.08279v1`
- Formal PDF: `raw/published.pdf`
- Preprint PDF: `raw/paper.pdf`
- TeX and Supplemental Material: `paper-source/arxiv.tex`
- Paper-linked author repository:
  `https://github.com/QuAIR/ProgrammableLindbladian`, inspected at commit
  `3e2e4c3be7a738b13442c546ff186c2870dfe465`

The formal article is the authority for bibliographic metadata and the final
main-text claims. The arXiv bundle contains the complete Supplemental Material
and source figure assets. Reference [60] of the formal article explicitly
points to the author repository, so its scripts are valid parameter provenance,
but they are not used as generated evidence.

## Reproduction Goal

This case reproduces every numerical paper figure:

1. Main Fig. 2: the two-qubit SWAP–dephasing overlap, both from an
   independently assembled Liouvillian and from a finite quasisampling
   estimator.
2. Main Fig. 3: the one-port Choi-program-state programming overhead
   \(2^{\gamma_\epsilon}\) for amplitude damping and amplitude damping plus a
   \(Z\) Hamiltonian, using an independently implemented Choi contraction and
   diamond-norm SDP.

The processor diagrams and circuit schematics are mapped for completeness but
are not numerical reproduction targets. The task is not to copy source panels
or merely rerun MATLAB/CVX code. Author code is used only to identify the
published numerical parameter set and to cross-check conventions.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Main text: programmability definition | Defines a fixed processor fed by analytic time-dependent program states | Establishes CPTP and HPTP lanes |
| Main text: programmable classes | Pauli and covariant Lindbladians | Theorem-level context; no numerical panel |
| Main text: beyond deterministic channels | No-go result and explicit quasisampling protocols | Leads to Fig. 2 |
| Main text: programming cost | Defines \(\gamma_\epsilon\) and the Choi-state choice | Leads to Fig. 3 |
| End Matter A | Necessary condition for CPTP programmability | Independent proof context |
| End Matter B | Finite-time-grid SDP for programming cost | Numerical specification for Fig. 3 |
| Supplemental I | Liouville and Choi conventions | Numerical foundation for both targets |
| Supplemental II–III | Programmable classes and explicit HPTP protocols | Includes the SWAP–dephasing derivation |
| Supplemental IV | Programming-cost properties and Choi program states | Supplies the exact SDP and analytic assumptions |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Supplemental Eq. for \(\mathbf L\), `arxiv.tex:291-305` | Vectorized GKSL generator | mapped |
| EQC002 | Supplemental Choi reshuffling, `arxiv.tex:309-316` | Convert \(e^{t\mathbf L}\) into \(J(\mathcal A_t)\) | mapped |
| EQC003 | Main/Supplemental SWAP–dephasing factorization, `arxiv.tex:163-170,782-806` | Closed semigroup used by Fig. 2 | mapped |
| EQC004 | Supplemental overlap lemma, `arxiv.tex:877-974` | Exact Fig. 2 observable | mapped |
| EQC005 | Supplemental coherent processor, `arxiv.tex:678-719,750-757` | Fixed HPTP map for the SWAP sector | mapped |
| EQC006 | Supplemental physical-implementability cost, `arxiv.tex:318-335` | Signed CPTP decomposition and sampling overhead | mapped |
| EQC007 | Main Eq. (2) / Supplemental definition, `arxiv.tex:1091-1105` | Defines \(\gamma_\epsilon\) | mapped |
| EQC008 | End Matter Eq. (B1) / `arxiv.tex:1146-1156` | Exact programming-cost SDP | mapped |
| EQC009 | Choi link/contraction convention, `arxiv.tex:262-269,1149-1153` | Retrieves a channel from \(J^\mathcal P\) and \(\pi_t\) | mapped |
| EQC010 | Watrous/QETLAB diamond-norm SDP plus formal End Matter B | Converts the \(\epsilon\)-error condition into LMIs | mapped |
| EQC011 | Paper-linked author scripts `error_threshold_ad*.m` | Fig. 3 Lindbladians and finite grids | mapped |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| FIG001 | Fixed processor and time-dependent program state | schematic_context | Main Fig. 1 |
| FIG002 | Exact and quasisampled SWAP–dephasing overlap | numeric_reproduction | Main Fig. 2; target T001 |
| FIG003 | Programming overhead versus error threshold | numeric_reproduction | Main Fig. 3; target T002 |
| FIGS001 | Two-outcome SWAP–dephasing HPTP protocol | schematic_context | Supplemental protocol figure |
| FIGS002 | Circuit implementation of amplitude damping | schematic_context | Supplemental Quantikz figure |
| FIGS003 | Six-operation amplitude-damping HPTP protocol | schematic_context | Supplemental protocol figure |

There are no paper tables.

## Numerical Parameter Provenance

| Target | Parameter | Value | Authority |
| --- | --- | --- | --- |
| T001 | \(\lambda\) | 0.5 | Main Fig. 2 caption |
| T001 | time interval / points | \([0,10]\), 101 points | Caption plus paper-linked `Quasi-Sampling.ipynb` |
| T001 | outer cycles / inner HPTP samples | 1000 / 200 | Paper-linked `Quasi-Sampling.ipynb` |
| T002 | damping rate \(G\) | 0.1 | Paper-linked `error_threshold_ad*.m` |
| T002 | Hamiltonians | \(H=0\) and \(H=Z\) | Paper-linked `error_threshold_ad*.m` |
| T002 | time discretization | 1000 sampled points from 0 to 9.99 with \(T=10\) | Author loop uses the first 1000 entries of `0:T/1000:T` |
| T002 | error grid | 41 points, \(0:0.005:0.2\) | Paper-linked scripts and source-figure filename |
| T002 | program copy count | \(n=1\) | Paper-linked scripts |

The End Matter describes the mathematically closed grid
\(\tau_k=kT/N,\;k=0,\ldots,N\). The released Fig. 3 script has an off-by-one
implementation and excludes \(t=10\). The paper-facing reproduction follows
the released 1000-point grid to match the plotted result and separately checks
that adding the endpoint does not materially change the curve.

## Assumptions and Conventions

- \(J(\mathcal E)=\sum_{ij}|i\rangle\langle j|\otimes
  \mathcal E(|i\rangle\langle j|)\) is the unnormalized Choi operator, so a
  trace-preserving \(d\)-dimensional channel has \(\operatorname{Tr}J=d\).
- The program state is \(\pi_t=J(\mathcal A_t)/d\).
- Liouville vectorization follows the paper convention
  \(\lvert A\rangle\rangle=\sum_{ij}A_{ij}|i\rangle|j\rangle\).
- The logarithm in \(\gamma_\epsilon\) is base 2, while Fig. 3 plots the
  overhead \(2^{\gamma_\epsilon}\), not \(\gamma_\epsilon\) itself.
- The random seed is absent from the paper and author notebook. The
  reproduction fixes and records a seed so that quasisampling evidence is
  deterministic; the seed is a reproducibility control, not a physical
  parameter.
