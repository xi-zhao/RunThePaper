# Figure Classification

The reproduction scope is numerical figures only. Schematic, experimental, or
external-context figures are not executable targets.

## Classification Rules Used

- `numeric_reproduction`: generated from a model equation, simulation,
  diagonalization, numerical invariant, parameter scan, or plotted computed
  data. These become targets.
- `schematic_context`: visual explanation of a model, geometry, mechanism, or
  setup. These are excluded.
- `experimental_context`: measured data, devices, photos, or lab outputs. These
  are excluded.
- `literature_or_external_context`: copied external data or comparison plots not
  generated from the paper's own method. These are excluded unless explicitly
  requested.

## arXiv 1803.01876

W1 atomic split: Fig. 2 has 4 panel items; Fig. 3 has 6 series items (including
the dashed analytic unit circle); Fig. 4 has 1 item; Fig. 5 has 3 items;
Supplemental Fig. 6 has 6 items; Supplemental Fig. 7 has 2 items. Together
these are 22 eligible numeric display items. Fig. 1 is the sole excluded
schematic.

| Figure | Source label | Class | Reproduce? | Reason |
| --- | --- | --- | --- | --- |
| Fig. 1 | `sketch` | `schematic_context` | No | Lattice/model sketch only. It defines unit-cell convention but has no numerical data. |
| Fig. 2(a-c) | `spectsmall` | `numeric_reproduction` | Yes | Open-chain eigenvalue spectra from finite Hamiltonian diagonalization. |
| Fig. 2(d) | `spectsmall` | `numeric_reproduction` | Yes | Boundary-perturbed open-chain spectrum from the same finite Hamiltonian. |
| Fig. 3(a) | `absbeta` | `numeric_reproduction` | Yes | `|beta_j|` curves computed from the beta-root equation. |
| Fig. 3(b) | `absbeta` | `numeric_reproduction` | Yes | Generalized Brillouin zone `C_beta` computed from model parameters. |
| Fig. 3(c) | `absbeta` | `numeric_reproduction` | Yes | Zero-mode and bulk eigenstate profiles computed from the open-chain model. |
| Fig. 4 | `invariant` | `numeric_reproduction` | Yes | Non-Bloch winding number computed on `C_beta`. |
| Fig. 5(a) | `t3` | `numeric_reproduction` | Yes | Nonzero-`t3` invariant and `L=100` open-chain spectrum from 35-digit independent numerics. High precision prevents the double-precision non-normal spectral drift; source paths are reference-only. |
| Fig. 5(b) | `t3` | `numeric_reproduction` | Yes | Nonzero-`t3` generalized Brillouin zone from numerical construction. |
| Supplemental Fig. 1 | `supplemental-1` | `numeric_reproduction` | Yes | Complex-plane spectra and open-chain eigenenergies. |
| Supplemental Fig. 2 | `supplemental-2` | `numeric_reproduction` | Yes | Spectrum and invariant in the `|t2| < |gamma|/2` regime. |

## No-display quantitative claims

| Claim | Classification | W1 decision | Target |
| --- | --- | --- | --- |
| Zero-mode endpoint migration across three `t1` intervals | analytic main claim | uncovered; implementation not ready | T006 |
| Multiband winding additivity `W=sum_l W^(l)` | analytic method claim | uncovered; implementation not ready | T007 |
| Correction of Ref. 49 zero-mode interval | cross-paper correction claim | uncovered; cited source context missing | T008 |

These claims remain in the whole-paper denominator. The first two were missed
by the former figure-centered scope; the third is a falsifiable paper-review
claim and cannot be replaced by reading or digitizing source pixels.
