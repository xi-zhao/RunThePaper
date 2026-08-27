# Numerical Methods

## Numerical object

The independent model propagates two bosons under random-matrix Hamiltonians and forms the collision-free conditional probability vector

```text
p_cond(r,s;t) = p_raw(r,s;t) / sum_{a<b} p_raw(a,b;t),  1 <= r < s <= M.
```

The denominator is evaluated separately for every realization and time before ensemble averaging. For the main setting `M=8`, `N=2`, the vector has `D=C(8,2)=28` entries.

## Frozen paper parameters

| Parameter | Value | Source |
| --- | --- | --- |
| Modes / photons | `M=8`, `N=2` | paper experiment |
| Input pair | `(3,4)` one-based / `(2,3)` zero-based | main OTOC text |
| Integrable / chaotic | `Lambda=0.01` / `Lambda=1000` | paper random-matrix section |
| Paper times | `1`, `1.79`, `29.29`, `100`, `1000` | appendix unitary construction |
| Fig. 3, Fig. 4, Fig. S5 ensembles | `2000` | corresponding captions |
| Fig. S4 modes | `4,6,8,10,12,14,16,18,20,22` | vector text of Fig. S4 |

## Paper-scale grids and checks

- Fig. 3 (`T002`): `2000` realizations; coarse `41`-point and refined `81`-point grids on `0.8…2.8`; logarithmic late-time extension through `1000`.
- Fig. 4 (`T003`): `2000` realizations; mixed linear/logarithmic grid from `0.05` through `1000`.
- Fig. S4 (`T005`): every printed even mode through `M=22`; `2000` chaotic realizations per mode.
- Fig. S5 (`T006`): `2000` realizations; mixed grid from `0.02` through `1000`; all `28` configurations, including the initial pair.
- Fig. S6 (`T007`): short-time power-law fit plus the paper's non-initial FFT scope.

The exact outputs and assertions are stored as paired files under:

```text
outputs/data/scientific_closure/T00X.json
outputs/checks/scientific_closure/T00X.json
```

The flat CSV files under `outputs/data/` and their PNG renderings are an older reduced-scale exploratory renderer path; they are not evidence for the paper-exact ensemble-count claims. They have been regenerated after the normalization repair so their Fig. S5 data now contain all `28` configurations, but fresh review must use the paired `scientific_closure` JSON and v2 isolated attestation for paper-scale adjudication.

## Central v2 results

- Fig. 3 extrema: entropy maximum and PT minimum at `t=1.79`, SFF minimum at `t=1.825`, PR maximum at `t=1.775`.
- Fig. 3 convergence: maximum refinement shift `0.025`; maximum late-domain shift `0`.
- Fig. 3 late-time separation: PT plateau/dip ratio `1.863`; SFF plateau/dip ratio `14.577`.
- At `t=1.79`: chaotic PR `12.5765`, integrable PR `1.05238`; chaotic entropy `2.79295`, integrable entropy `0.15909`.
- Fig. S4: PT endpoint reduction `0.91550`; entropy-gap drop `1.67762` percentage points; `M=22` uses all `2000` chaotic realizations.
- Fig. S5: `28/28` configurations for each ensemble, three overlap sectors `{0,1,2}`, and probability sum one at every stored time.
- Fig. S6 slopes: overlap-one `1.99959`, overlap-zero `3.99978`; pairwise chaotic FFT-PR win fraction `1.0`.

The author-repair scaling benchmark separately times counts `16`, `64`, and `256` and projects paper-scale cost without promoting scientific coverage. The actual paper-scale isolated run, not the projection, is the primary evidence.
