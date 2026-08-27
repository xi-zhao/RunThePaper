# Paper Map: arXiv:1711.03528

## Paper

- Title: Quantum many-body scars
- PaperID: arXiv:1711.03528
- Authors: C. J. Turner, A. A. Michailidis, D. A. Abanin, M. Serbyn, Z. Papic
- Main object: constrained Rydberg / Fibonacci chain described by the PXP Hamiltonian

## What The Paper Claims

The paper shows that a non-integrable constrained quantum chain can contain a small tower of atypical many-body eigenstates. These states have unusually large overlap with the period-2 density-wave state `Z2`, and they explain the long-lived oscillations seen after a quench from that state.

## Numerical Figures In Scope

| Paper figure | Type | In scope | Reproduced target |
| --- | --- | --- | --- |
| Fig. 1 | Hamiltonian graph / model structure | yes, as method validation | L=6 constrained Hilbert-space graph |
| Fig. 2 in source file `ent_dynamics.pdf` | iTEBD dynamics | yes | L=16 exact time evolution plus a code-ready `L=101`, bond-400 finite-window MPS comparator |
| Fig. 3 | Exact diagonalization + FSA + participation ratio | yes | `L=28`, `k=0, I=+1` scar tower plus local FSA outputs; `L=32` config is code-ready |
| Fig. 4 | Level statistics and density of states | yes | `L=28` same-sector unfolding and density of states; `L=32` config is code-ready |

## Out Of Scope

- Experimental Rydberg-atom data from the referenced Bernien et al. experiment.
- Pixel-level recreation of layout, line style, or figure typography.
- Full paper-scale L=32 symmetry-resolved ED in the `k=0, I=+` sector.
- Execution of the bond-400 MPS convergence grid and author-identical iTEBD details absent from the paper.
