# Target Ledger

| Target | Paper item | Formula path | Executed numerical scope | Scientific status | Pixel status | Remaining cause |
| --- | --- | --- | --- | --- | --- | --- |
| T001 | Fig. 5 cross section | BEM001–BEM004, BEM006 | `N=1600`, 153 `kR` points, Eq. (22) observable | passed | 69.0193, needs repair | source-sign review + render |
| T002 | Fig. 6 near field | BEM001–BEM003, BEM005–BEM006 | `N=1600`, shared null vector, `401 x 401` on `[-3R,3R]^2` | passed | 97.3720, high fidelity | source-sign review |
| T003 | Fig. 7 far field | BEM001–BEM006 | same frozen null vector, 1440 angles | passed | 53.6671, rejected | source-sign review + render |

All targets use
`outputs/data/paper_scale_bem/data/bem_paper_scale.npz`, produced by attested
run `paper-scale-figure-geometry-bem-v2`. The paper's rounding/discretization
equivalence class is satisfied; element-wise identity to an unpublished private
mesh is neither required by the paper nor claimed here.
