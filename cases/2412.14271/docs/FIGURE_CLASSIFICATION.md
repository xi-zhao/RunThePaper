# Figure Classification

The machine-readable authority is `figure_coverage.json`. This projection keeps
the same atomic unit: one independently adjudicable numerical subpanel, or one
whole figure only when the unavailable source prevents panel enumeration.

| Paper item | Class | Coverage decision | Reason |
| --- | --- | --- | --- |
| Main Fig. 1(a) | `schematic_context` | excluded | Apparatus drawing; no computed observable. |
| Main Fig. 1(b) | `schematic_context` | excluded | Symmetry sketch; the numerical symmetry evidence is in Fig. 4. |
| Main Fig. 1(c) | `schematic_context` | excluded | Comparison sketch; no computed observable. |
| Main Fig. 2(a) | `theoretical_numerical` | covered, T001 | Formula-derived photon fixed point. |
| Main Fig. 2(b) | `theoretical_numerical` | covered, T001 | Formula-derived spin fixed point. |
| Main Fig. 2(c) | `theoretical_numerical` | covered, T001 | Independently generated cutoff-drift observable. |
| Main Fig. 2(d) | `theoretical_numerical` | covered, T001 | Independently generated spin observable. |
| Main Fig. 2(e) | `theoretical_numerical` | covered, T001 | Independently generated `M=60` Fock distribution. |
| Main Fig. 2(f) | `theoretical_numerical` | covered, T001 | Independently generated `M=80` Fock distribution. |
| Main Fig. 2(g) | `theoretical_numerical` | covered, T001 | Independently generated `M=100` Fock distribution. |
| Main Fig. 3(a) | `theoretical_numerical` | covered, T002 | Finite-system normal-phase distribution. |
| Main Fig. 3(b) | `theoretical_numerical` | covered, T002 | Finite-system side-lobe distribution. |
| Main Fig. 3(c) | `theoretical_numerical` | covered, T002 | Finite-system strong-coupling distribution. |
| Main Fig. 3(d) | `theoretical_numerical` | covered, T002 | Large-system normal-phase distribution. |
| Main Fig. 3(e) | `theoretical_numerical` | covered, T002 | Large-system side-lobe distribution. |
| Main Fig. 3(f) | `theoretical_numerical` | covered, T002 | Large-system strong-coupling distribution. |
| Main Fig. 3(g) | `theoretical_numerical` | covered, T002 | Cumulant branches compared with generated ED/QT means. |
| Main Fig. 4(a) | `theoretical_numerical` | covered, T003 | Wigner transform of generated density matrix. |
| Main Fig. 4(b) | `theoretical_numerical` | covered, T003 | Wigner transform testing coexistence and `Z4`. |
| Main Fig. 4(c) | `theoretical_numerical` | covered, T003 | Strong-coupling Wigner transform. |
| Main Fig. 4(d) | `theoretical_numerical` | covered, T003 | Large-system normal-phase Wigner transform. |
| Main Fig. 4(e) | `theoretical_numerical` | covered, T003 | Large-system coexistence Wigner transform. |
| Main Fig. 4(f) | `theoretical_numerical` | covered, T003 | Large-system strong-coupling Wigner transform. |
| Formal Fig. S1 / v1 Fig. 5(a) | `theoretical_numerical` | covered, T004 | One-loss normal-branch Bogoliubov scan. |
| Formal Fig. S1 / v1 Fig. 5(b) | `theoretical_numerical` | covered, T004 | One-loss superradiant-branch Bogoliubov scan. |
| Formal Fig. S2 / v1 Fig. 6(a) | `theoretical_numerical` | covered, T005 | Both-loss normal-branch Bogoliubov scan. |
| Formal Fig. S2 / v1 Fig. 6(b) | `theoretical_numerical` | covered, T005 | Larger superradiant-branch scan. |
| Formal Fig. S2 / v1 Fig. 6(c) | `theoretical_numerical` | covered, T005 | Smaller superradiant-branch scan and discrepancy test. |
| **Formal Fig. S3, panels unavailable** | `theoretical_numerical` | **uncovered, T006** | Formal supplement requires authorization; panel count, parameters, and observable are not frozen. |
| **Formal Fig. S4, panels unavailable** | `theoretical_numerical` | **uncovered, T006** | Formal supplement requires authorization; panel count, parameters, and observable are not frozen. |
| Formal Fig. S5 / v1 Fig. 7 | `theoretical_numerical` | covered, T007 | Generated convergence diagnostic; fidelity is reduced-scale. |
| v1 SM Fig. 8(a), formal number unverified | `theoretical_numerical` | covered, T008 | Formula-defined parity-resolved Liouvillian kernel. |
| v1 SM Fig. 8(b), formal number unverified | `theoretical_numerical` | covered, T008 | Generated odd-parity Fock distribution. |
| v1 SM Fig. 8(c), formal number unverified | `theoretical_numerical` | covered, T008 | Generated even-parity Fock distribution. |

## Coverage Boundary

- Eligible numerical items: **31**.
- Covered items: **29**.
- Explicitly uncovered items: **2** — formal Figs. S3 and S4.
- Excluded non-numerical items: **3** — main Fig. 1(a-c).
- Item coverage: **93.55%**.

Every confirmed numerical subpanel remains in scope. No source curve, raster
value, or author numerical array is used to generate a target. The two missing
formal figures are not hidden inside a range: they remain explicit zero-score
items until their source and evaluation contracts are available.
