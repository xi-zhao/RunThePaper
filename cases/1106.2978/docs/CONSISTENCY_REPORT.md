# Consistency Report

## Summary

| Level | Count | Meaning |
| --- | ---: | --- |
| exact_match | 5 | T001-T004 and T006 reproduce every printed executable feature and quantitative limit. |
| feature_match | 1 | T005 has the correct isotropic correlation sign, shape and `1/n` scaling; the largest finite chain remains 15.16% from the leading continuum kernel. |
| partial_match | 0 | No target is only locally covered. |
| blocked | 0 | No numerical target lacks an indispensable publication input or paper-scale implementation. |
| not_in_scope | 1 | Main Fig. 1 is a tensor-network schematic. |

## Per-target result

| Target | Paper item | Scientific result | Presentation result |
| --- | --- | --- | --- |
| T001 | Main Fig. 2(a) | dense-Liouvillian cross-check `< 7.22e-16`; cosine RMSE `0.00119` at `epsilon=1` | complete crop `94.0463`, high fidelity |
| T002 | Main Fig. 2(b) main | dense current error `< 3.34e-16`; isotropic slope `-2.00721`; `n=400` coefficient error `0.00378` | complete crop `88.4407`, accepted |
| T003 | Main Fig. 2(b) inset | slope error from `-arcosh(3/2)` `< 1.80e-13`; `R^2=0.99999855` | inset crop `89.7941`, accepted |
| T004 | easy-plane paragraph | maximum at `epsilon=1.629091855`; small/large-coupling coefficients approach `1/2` and `4/3` | numeric text claim, pixel N/A |
| T005 | isotropic correlation paragraph | finite exact correlation approaches the printed leading kernel; maximum relative error at `n=120` is `0.15156` | numeric text claim, pixel N/A |
| T006 | weak-coupling paragraph | current/profile relative errors `< 1.70e-7` | numeric text claim, pixel N/A |

## Reproduction defect found and repaired

- Direct cause: the first production configuration stopped the Fig. 2(b) current domain at `n=100`, while the complete paper axis extends to about `n=400`.
- Root cause: the initial inventory transcribed caption parameters but did not bind the full plotted axis domain into the machine contract.
- Code-fault assessment: the transfer algorithm was correct on `n<=100`; the defect was incomplete scientific configuration, not a wrong Hamiltonian or observable.
- Repair: update the scientific configuration and contract to `n=2..400`, rerun the isolated numerical channel, freeze new arrays and only then rerender.
- Prevention: full axes, inset axes and every series domain must be inventoried before production configuration freezes. RenderContract is forbidden from stretching or inventing missing scientific points.

## Paper review

No printed formula or quantitative claim currently has a stable contradiction after independent dense checks, asymptotic checks and full-domain repair. Therefore this case emits no paper-error candidate. A fresh-context protocol-v2 review remains required before lifecycle completion.
