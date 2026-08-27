# Figure Classification

Only numerical figures/tables become executable reproduction targets.

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Fig. 1 (types of exchange statistics) | `schematic_context` | no | Conceptual illustration, no data |
| **Fig. 2 left** (level degeneracy `{d_n}`) | `numeric_reproduction` | **yes** | Integer degeneracies from `z_R(x)`; target T1 |
| **Fig. 2 right** (`<n>_beta` vs `beta*eps`) | `numeric_reproduction` | **yes** | Closed-form occupation curves; target T1 |
| Table 1 (R-matrices, `z_R(x)`) | `numeric_reproduction` | yes (input) | Feeds T1; validated by ED (T2) |
| Fig. 3 (2D 7×7 solvable lattice) | `schematic_context` | no | Lattice/interaction diagram |
| Fig. 4 (paraparticle braiding) | `schematic_context` | no | Exchange illustration |
| SI tensor-network / CR figures | `schematic_context` | no | Graphical proofs |
| 1D solvable spin model (Eq. Hamil1Dspin) | `numeric_reproduction` | yes (validation) | Not a printed figure; ED validates emergent free paraparticles — target T2 |

Allowed classes:

- `numeric_reproduction`
- `schematic_context`
- `experimental_context`
- `literature_or_external_context`
- `algorithm_trace`
- `not_in_scope`

## Flagged text/figure inconsistency (unknown-unknown)

The **main-text prose** (arXiv source line 603) states that Fig. 2's right panel
plots Ex.3 and Ex.4 "with `m=5`". The **published Fig. 2 legend** instead reads
`Ex.2 (m=2)`, `Ex.3 (m=2)`, `Ex.4 (m=3)`, and the left panel's degeneracy ladders
(Ex.3 showing `d_1=2`, Ex.4 showing `d_1=3` and `d_2=1`) are consistent only with
`m=2`/`m=3`, **not** `m=5`. We reproduce the **figure** (the reader-facing
artifact), so the paper-exact parameters are `m3=2`, `m4=3`. The `m=5` prose is an
internal inconsistency, most likely a caption/figure that was regenerated at
smaller `m` after the sentence was written. This is recorded as an open question
on the `single_mode_partition_z_R` equation card.
