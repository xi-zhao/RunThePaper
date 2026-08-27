# Formula Verification

All twelve cards in `EQUATION_CARDS.json` are source-traceable. EQ001-EQ009
retain their existing reconstructed/verified state; EQ010-EQ012 are explicitly
`source_only` and therefore do not count as reproduced scientific evidence.

| Formula | Role | Gate | Independent check |
| --- | --- | --- | --- |
| EQ001 | root-of-unity strings/kernels | open | even rapidity kernels and exact regular zeros |
| EQ002 | infinite-T fillings | open | `0<theta<1`, susceptibility check |
| EQ003 | densities/velocities | open | positive densities and odd velocities |
| EQ004 | Euler wall | open | oddness, plateaus, boundedness |
| EQ005 | dressed scattering | open | resolvent identity and symmetry |
| EQ006 | spin Onsager coefficient | open | positivity and grid convergence |
| EQ007 | projected diffusive wall | open | zero-diffusion limit, oddness, plateaus |
| EQ008 | mixed-state purification TEBD | open | exact local density matrix, two-site unitarity, norm and total-spin conservation, checkpoint equivalence |
| EQ009 | full spectral diffusion operator | open | kernel spectrum, magnetic-response normalization, real/odd/bounded PDE smoke profile |
| EQ010 | hard-rod limiting reduction | source-only | paper statement traced; independent reduction missing |
| EQ011 | free-model zero diffusion | source-only | paper statement traced; independent invariant missing |
| EQ012 | entropy-production positivity | source-only | main/supplement derivation traced; independent proof/check missing |

Machine-readable result: `outputs/checks/formula_verification.json`.

The open scientific discrepancy is explicit: the ell=7 integral converges to
`0.73077` while the paper prints `0.744` (1.78%). No physical coefficient is
fitted to remove it.

Under the fresh-review v2 vocabulary this remains `inconclusive`: one
independently converged lane is enough to preserve and investigate a mismatch,
but not enough to accuse the paper. A `paper_error_candidate` would additionally
need paper-exact cross-checks from a second independent method and fresh-context
adjudication.
