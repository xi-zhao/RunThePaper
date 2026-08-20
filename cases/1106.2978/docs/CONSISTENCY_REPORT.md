# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 19 | All targets except T005 and T014 reproduce the printed executable statement. |
| feature_match | 0 | No remaining target is accepted only by a broad feature match. |
| partial_match | 2 | T005 and T014 are numerically reproducible objects whose printed formulas conflict with exact checks. |
| blocked | 0 | No numerical target lacks an indispensable publication input or paper-scale implementation. |
| not_in_scope | 1 | Main Fig. 1 is a tensor-network schematic. |

## Per-target result

| Target | Paper item | Scientific result | Presentation result |
| --- | --- | --- | --- |
| T001 | Main Fig. 2(a) | dense-Liouvillian cross-check `< 7.22e-16`; cosine RMSE `0.00119` at `epsilon=1` | complete crop `94.0463`, high fidelity |
| T002 | Main Fig. 2(b) main | dense current error `< 3.34e-16`; isotropic slope `-2.00721`; `n=400` coefficient error `0.00378` | complete crop `88.4407`, accepted |
| T003 | Main Fig. 2(b) inset | slope error from `-arcosh(3/2)` `< 1.80e-13`; `R^2=0.99999855` | inset crop `89.7941`, accepted |
| T004 | easy-plane paragraph | maximum at `epsilon=1.629091855`; small/large-coupling coefficients approach `1/2` and `4/3` | numeric text claim, pixel N/A |
| T005 | isotropic correlation paragraph | finite exact correlations are mirror-equal to `7.12e-14`, while the printed scaled mirror gap remains at least `0.00856579` | formula gate blocked; fresh review pending |
| T006 | weak-coupling paragraph | current/profile relative errors `< 1.70e-7` | numeric text claim, pixel N/A |
| T007-T013 | theorem/corollaries/method | explicit MPO, dense Liouvillian, structural and complexity checks pass | numeric text claims, pixel N/A |
| T014 | root-of-unity paragraph | complete Eq. (7) evaluation leaves the named `r=m` component nonzero; the opposite hopping vanishes at `r=m-1`, producing the `m`-state space used by the paper's own `m=3` example | formula gate blocked; repaired diagnostic pending fresh review |
| T015-T019 | reduced matrix and asymptotics | all matrix, amplitude, `alpha` and continuum checks pass | numeric text claims, pixel N/A |
| T020 | easy-plane spectral convergence | maximum spectral-ratio/current-fit relative error `1.04e-4`; thermodynamic magnetization vanishes and the bulk profile converges | numeric text claim, pixel N/A |
| T021 | infinite transfer rank | analytic hopping witnesses and shifted-minor diagonals agree to `1.41e-16` relative error; rank lower bound 12 is certified for every probe | numeric text claim, pixel N/A |

## Reproduction defect found and repaired

- Direct cause: the first production configuration stopped the Fig. 2(b) current domain at `n=100`, while the complete paper axis extends to about `n=400`.
- Root cause: the initial inventory transcribed caption parameters but did not bind the full plotted axis domain into the machine contract.
- Code-fault assessment: the transfer algorithm was correct on `n<=100`; the defect was incomplete scientific configuration, not a wrong Hamiltonian or observable.
- Repair: update the scientific configuration and contract to `n=2..400`, rerun the isolated numerical channel, freeze new arrays and only then rerender.
- Prevention: full axes, inset axes and every series domain must be inventoried before production configuration freezes. RenderContract is forbidden from stretching or inventing missing scientific points.

## Paper review

The previous independent review was based on the old six-target scope and is
now stale. A new protocol-v2 review must inventory the repaired 25-item,
21-target package before either discrepancy can be promoted to
`paper_error_candidate`.
