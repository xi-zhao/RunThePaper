# Consistency Report

## Consistent Features

| Feature | Paper expectation | Local result | Status |
| --- | --- | --- | --- |
| Open-chain zero modes | Zero modes appear inside the non-Bloch topological interval. | Verified for `|t1| < sqrt(t2^2 + (gamma/2)^2)`. | consistent |
| Chiral spectral pairing | Energies pair as `E` and `-E`. | Structure-aware eigensolver gives zero pairing residual within tolerance. | consistent |
| Generalized Brillouin zone | Bulk states live on `C_beta`, not the unit circle. | `C_beta` radius and equal-modulus beta roots match the derivation. | consistent |
| Skin effect | Right eigenstates localize at one boundary. | Zero mode and selected bulk profiles are left-localized. | consistent |
| Winding plateau | `W=1` in the topological region and `W=0` outside. | Plateau checks pass away from transition tolerance. | consistent |
| Nonzero `t3` transition | Transition near `t1 = +/-1.56`. | Reproduced from the quartic beta-root condition. | consistent |

## Partial Or Not Exact

| Item | Reason |
| --- | --- |
| Pixel-level figure matching | Not used as acceptance; the original plotted data is not available as raw numerical data. |
| Digitized curve comparison | Not implemented yet. Rendered EPS images are used as visual references only. |

## Source Figure Errata

| Figure | Source artifact | Physical truth | Evidence |
| --- | --- | --- | --- |
| Fig. 2(d) low-energy region | The source EPS connects `|E|` samples by per-`t1` sorted rank, so the genuine `|E|` crossings near `t1` in `[1.0, 1.2]` are drawn as avoided crossings. | Eigenvalue-continuation branches cross: the boundary-perturbed mode dips to `min|E| = 0.003` at `t1 = 1.025` (analytically nonzero, since `det` of the chiral block has no zero in `[0.9, 1.3]`), crosses other branch moduli in `[1.0, 1.2]`, and crosses zero exactly at `t1 = 0.8 + gamma/2 = 22/15` where the perturbed first bond decouples. | `outputs/checks/fig2_boundary_perturbation.json` (`physics_probes`, `source_figure_artifact`), sorted-rank reproduction figure `outputs/figures/fig2_boundary_perturbation_sorted_artifact_zoom.png`. |

The published rendering of Fig. 2(d) follows the physical branch identity (`connect_within_branch_id_in_t1_order`), not the source figure's sorted-line convention. The sorted-line look is kept only as a reproducible artifact evidence figure.

## What The Case Proves

The case proves that the formula-to-numerics chain can be followed across the paper: Hamiltonian construction, non-Bloch beta equation, generalized Brillouin zone, winding number, and boundary spectra all produce the paper's physical features.
