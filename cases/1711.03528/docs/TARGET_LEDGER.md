# Target Ledger

| Target | Paper figure | Goal | Local status | Acceptance |
| --- | --- | --- | --- | --- |
| T001 | Fig. 1 | Build the constrained Hilbert-space graph for `L=6` | reproduced | exact node count and Hamiltonian edges generated |
| T002 | Fig. 2 | Show slow `Z2` entanglement growth and local oscillations | physically_consistent | finite-size ED gives `Z2` period `2.375`, close to paper `~2.35` |
| T003 | Fig. 3 | Show high-overlap scar tower and FSA structure | physically_consistent | scar tower and FSA ground-state profile appear; near-zero FSA is partial |
| T004 | Fig. 4 | Show non-Poisson / WD-trending level statistics and Gaussian density | partial | density feature appears; spacing statistics need symmetry-resolved L=32 rerun |

## Planned Large-Scale Target

The paper-scale reproduction would rerun:

- PBC `L=32`;
- zero-momentum, inversion-even sector;
- unfolded level spacings excluding low spectrum and central zero-mode region;
- iTEBD dynamics with bond dimension around 400.

This is classified as `planned_large_scale`, not complete locally.
