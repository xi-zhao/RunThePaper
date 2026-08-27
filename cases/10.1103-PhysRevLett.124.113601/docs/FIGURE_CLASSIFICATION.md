# Figure Classification

Figures are classified before coding so apparatus art and source panels cannot
be mistaken for independent numerical evidence.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. 1 | `schematic_context` | no | Optical apparatus illustration, not a numerical output |
| Fig. 2 main | `numeric_reproduction` | yes, T001 | Full GAA/AA eigensystems and critical thresholds |
| Fig. 2 inset | `numeric_reproduction` | yes, T001 | IPR and the mobility-edge index |
| Fig. 3(a) | `numeric_reproduction` | yes, T002 | AA susceptibility and critical pump vs disorder |
| Fig. 3(b,c) | `numeric_reproduction` | yes, T002 | Momentum distributions at `chi/J=0,1` |
| Fig. 3(d,e) | `numeric_reproduction` | yes, T002 | State-resolved susceptibility channels |
| Fig. 4(a) | `numeric_reproduction` | yes, T003 | Mean-field cavity photon number; published-only panel |
| Fig. 4(b) | `numeric_reproduction` | yes, T003 | Threshold landscape vs `gamma_c` and disorder |
| Fig. S1(a-e) | `numeric_reproduction` | partial/paper subset, T004 | Density features are closed; exact pump samples are not printed |

## Active Numerical Scope

- `T001`: Fig. 2, AA/GAA state-resolved instability and GAA mobility edge.
- `T002`: Fig. 3, AA transition mechanism and momentum-space channels.
- `T003`: Fig. 4, nonlinear photon number and threshold landscape.
- `T004`: Fig. S1, self-consistent density profiles with disclosed reconstructed
  below/above-threshold pump values.
- `D001`: unpublished finite-size and weak-trap sanity checks; diagnostic only.

The arXiv source figures under `internal-paper-reference/` are
reference artifacts only. Fig. 4(a) and Fig. S1 must be cropped from the
published PDFs for comparison because they are absent from the arXiv source
bundle.
