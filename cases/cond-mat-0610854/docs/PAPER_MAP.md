# Paper Map

## Scientific model

Eq. (1) defines half-filled spinless fermions on a periodic chain with nearest-neighbor interaction `V=2`, nearest and next-nearest hopping `t=t'=1`, and Gaussian onsite disorder with sample RMS fixed to `W`.

## Complete numerical inventory

| Item | Kind | Target | Required content |
| --- | --- | --- | --- |
| Main Fig. 1 | numerical plot | T001 | Poisson analytic curve, GOE samples, model distributions at `L=16`, `W=3,7,11` |
| Main Fig. 2 top | numerical plot | T002 | disorder-averaged mean adjacent-gap ratio for `L=8,10,12,14,16` over full `W` range |
| Main Fig. 2 bottom | numerical subplot | T003 | crossing-region enlargement with the same five size curves and uncertainties |
| crossing drift | quantitative text claim | T004 | adjacent-size crossing estimates drift in both `W_c(L)` and `r_c(L)` |

There are no tables or supplemental figures. Every figure in the paper is numerical; nothing is excluded as a schematic.

## Printed quantitative anchors

- Poisson: `P_P(r)=2/(1+r)^2`, mean `2 ln 2 - 1 ≈ 0.386`.
- GOE: mean `0.5295 ± 0.0006`; footnote states 1000 random matrices of size 3432.
- Model: half filling, periodic boundary, `V=2`, `t=t'=1`, lengths through `L=16`.
- Disorder samples are Gaussian and rescaled to exact sample mean-square `W^2`.
- Sample counts: `L=8`: 10000; `L=14,16`: about 50–100 away from crossing and 1000 in the critical region. Counts for `L=10,12` and the exact `W` grid are not printed.
