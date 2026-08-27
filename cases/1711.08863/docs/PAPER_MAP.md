# Paper Map

## Identity

- Paper ID: `1711.08863`
- Title: *Decoherence-Free Interaction between Giant Atoms in Waveguide QED*
- Authors: Anton Frisk Kockum, Göran Johansson, Franco Nori
- Publication: Physical Review Letters 120, 140404 (2018)
- DOI: `10.1103/PhysRevLett.120.140404`
- Local PDF: `raw/paper.pdf`
- Local source: `paper-source/extracted/`

## Reproduction Goal

Follow the two-atom and general multi-connection master-equation derivation,
regenerate every curve in Main Fig. 2, and independently test the three central
analytic claim families that are not carried by a numerical display. Connection
layouts and proposed circuit drawings remain context rather than raster targets;
their surrounding chain and all-to-all theorems are counted separately.

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| Introduction | Physical motivation | Interaction-versus-decoherence trade-off and giant-atom platform. |
| Two atoms in a waveguide | Core model | Main Eq. (1), Table I, and Main Fig. 2. |
| General multi-point master equation | Generalization | Pairwise sine/cosine coefficient sums used as an independent generator. |
| 1D protected chain | Design consequence | Schematic construction and phase-counting argument. |
| All-to-all connectivity | Design consequence | Schematic construction and constraint counting. |
| Supplement | Full derivation | SLH composition, arbitrary rates/phases, and topology proofs. |

The complete source audit is also recorded in
`PAPER_REVIEW_PROTOCOL_V2.md`. It distinguishes the verified Fig. 2 numerical
claim from a likely local operator-label typo in Supplement Eq. (S21) and from
two nonnumeric editorial cross-reference errors.

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQ001 | Main Eq. (1) | Meaning of plotted master-equation coefficients | verified |
| EQ002 | Main Eq. (2) definitions + supplement | General point-pair coefficient sums | verified |
| EQ003 | Main Table I | Closed curves for `ab`, `aabb`, `abab`, `abba` | verified |
| EQ004 | Text after Fig. 2 + supplement | Decoherence-free braided interaction | verified |
| EQ005 | Supplement Eqs. (S135)-(S137) | General zero-decay factorization | verified |
| EQ006 | Supplement Eqs. (S122)-(S128) | Protected-chain all-N rank witness | verified |
| EQ007 | Supplement Eqs. (S129)-(S134) | All-to-all all-N rank witness and N=3 constructions | verified |

## Figure/Table Inventory

| Item | Caption summary | Initial class | Notes |
| --- | --- | --- | --- |
| Main Fig. 1(a-e) | Five two-atom topologies | schematic_context | Five excluded panels. |
| Main Table I | Analytic coefficients | formula_source | Excluded from the denominator because it is the formula source and cross-check for T001. |
| Main Fig. 2 | Couplings and decays versus phase | numeric_reproduction | T001; all 13 visible curves on one shared axis. |
| Main Fig. 3(a-c) | Protected nearest-neighbor chain | schematic_context | Three excluded panels; the independent tunability theorem is T003. |
| Main Fig. 4(a-c) | Protected all-to-all setup | schematic_context | Three excluded panels; the independent constraint theorem is T004. |
| Supplement Fig. S1(a-c) | SLH composition rules | schematic_context | Three excluded panels. |
| Supplement Figs. S2-S6(a-b) | Setup and SLH-flow diagrams | schematic_context | Ten excluded panels. |
| Supplement Figs. S7-S8 | Chain and all-to-all notation | schematic_context | Two excluded figures; their analytic claims map to T003/T004. |

The resulting display inventory contains **28 atomic items**: one eligible
numerical figure and 27 excluded formula/schematic items. No display panel is
silently deleted from the full-paper inventory.

## Independent Analytic Claim Inventory

| Claim family | Paper location | Coverage |
| --- | --- | --- |
| Arbitrary multi-point master equation and topology rule | Main Eq. (2); supplement general multi-point section | **reproduced, T002** |
| Protected 1D chain has N constraints and N-1 independently tunable couplings | Main text after Fig. 3; supplement chain section | **reproduced, T003** |
| Protected all-to-all layout has N-1 controls, with explicit N=3 constructions | Main text after Fig. 4; supplement all-to-all section | **reproduced, T004** |

These claims have no numerical display that can carry an independent verdict.
They therefore enter the scientific denominator instead of being hidden behind
the schematic classification of Figs. 3 and 4.

## Coverage Summary

- Eligible reproduction items: **4**.
- Reproduced items: **4**.
- Explicitly unresolved items: **0**.
- Coverage: **100.00%**.
- Fidelity and reproduction degree: **87.66/100**.

## Closed Former Gaps

T002 now has an all-size phasor factorization plus unequal-rate direct-sum
checks. T003 and T004 now have exact all-N rank witnesses, constructive
solutions, representative numerical checks, and one isolated attested run.
Fresh review remains a lifecycle step, not an uncovered scientific item.

## Assumptions

- The figure uses the paper's equal bare coupling `gamma` at every point and
  equal phase `phi` between adjacent connection points.
- Rates and couplings are normalized by `gamma`, so the runner sets `gamma=1`.
- The phase interval and endpoint ticks are exactly `0 <= phi <= pi`.
