# Paper Map

## Identity

- Paper ID: 10.1103-PhysRevB.91.085420
- Title: Interband coherence induced correction to adiabatic pumping in periodically driven systems
- Authors: Hailong Wang, Longwen Zhou, Jiangbin Gong (NUS)
- Source: Phys. Rev. B **91**, 085420 (2015); DOI 10.1103/PhysRevB.91.085420
- Local PDF: `raw/paper.pdf` (image-only, no text layer; Foxit print)
- Local source: `raw/page_images/p01.png … p09.png` (150 dpi renders, read visually)

## Reproduction Goal

Reproduce the central claim: for a **general (multi-band) initial state** in a
periodically driven closed system undergoing an adiabatic pumping cycle
(β: 0 → 2π), the one-cycle displacement of the wave-packet center is

```
Δ⟨x⟩ = Σ_n ∫dk ∫dβ B_n(β,k) ρ_{n,k}(0)          (weighted Berry-curvature integral)
       − 2 Σ_{m≠n} ∫dk Re[ C*_{n,k}(0) C_{m,k}(0) (dE_{n,k}/dk) W_{nm,k}(0) ]   (IBC correction)
```

Both terms are **independent of the adiabatic duration T**. The second (interband
coherence, IBC) term survives the adiabatic limit and is missed by a naive
application of the quantum adiabatic theorem. Validate on the continuously driven
Harper model (CDHM), Eq. (14), with α = 1/3, τ = 2.

In scope (numerical targets): Fig. 1, Fig. 2, Fig. 3, Fig. 4.
Out of scope: none beyond these four figures — the paper has no other figures/tables.

## Model — Continuously Driven Harper Model (CDHM), Eq. (14)

```
H = Σ_l (J/2)(a†_l a_{l+1} + H.c.) + K cos(2πt/τ) Σ_l cos(2π α l + β) a†_l a_l
```

- α = M/N = 1/3 (M=1, N=3) -> superlattice period N=3 -> 3 Floquet bands
- τ = 2 (driving period); β the adiabatic parameter, β(s)=2πs, period 2π
- Bloch reduction: lattice index l = 3n + j, j in {0,1,2}; onsite potential depends
  only on sublattice j (since cos(2π*3n/3 + ...)=cos(...)). Per-k Hamiltonian is 3x3.
- Superlattice constant a = 3 (atomic spacing 1) -> k in [-π/3, π/3] (Fig. 1 x-axis
  k/π in [-1/3, 1/3]).
- Adiabatic protocol: β piecewise constant, changing **once per driving period**
  (β_j = 2π j/T at the j-th period). Hence one full cycle = product of T
  one-period Floquet operators U(k, β_j) -- this makes the "actual" dynamics cheap.

## Reproduction Goal per figure

| Fig | Quantity | Params |
| --- | --- | --- |
| 1(a) | Floquet eigenphases ω_{n,k}(β)/π, 3 bands, surface over (k, β) | J=K=3 |
| 1(b) | Initial band populations ρ_{n,k}(0)=|C_{n,k}(0)|², initial state at site l=0 | J=K=3 |
| 2 | Population change Δρ_{n,k}(k) after one cycle, bottom band: (a) actual, (b) theory Eq. (8) | J=K=3, T=1024 |
| 3 | ⟨x⟩(t) over one cycle, 6 durations; theory Eq. (13) (filled dot), Berry-only (triangle) | J=K=4, T=1024..6144 |
| 4 | Δ⟨x⟩ vs J(=K) topological-transition probe; actual (open), theory (filled), Berry-only | J=K in [5.0,5.3], T=2560 |

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| I. Introduction | context | Floquet topology, Thouless pumping, closed driven systems |
| II. Population correction in adiabatic following | derivation | Eqs. (1)-(8): Floquet states, first-order adiabatic perturbation, Δρ_{n,k} |
| III. Wave-packet dynamics during a cycle | derivation | Eqs. (9)-(13): Δ⟨x⟩ decomposition, Berry curvature B_n, IBC term |
| IV. Theory vs model calculations | numerics | Eq. (14) CDHM; Figs. 1-4 |
| V. Summary | - | - |
| Appendix 1 | derivation | Eqs. (A1)-(A11): first-order adiabatic perturbation theory |
| Appendix 2 | derivation | Eqs. (A12)-(A26): Δ⟨x⟩ from position operator in Floquet-Bloch basis |

## Equation/Method Inventory

| ID | Source | Role | Status |
| --- | --- | --- | --- |
| Eq.(1) | II | Floquet operator U(β) eigen-equation, eigenphases ω_{n,k}(β) | transcribed |
| Eq.(2) | II | accumulated dynamical phase Ω_{n,k}(s_j) | transcribed |
| Eq.(3) | II | state expansion in instantaneous Floquet eigenstates | transcribed |
| Eq.(4)/(A4) | II | transition amplitude dC_{n,k}/ds | transcribed |
| Eq.(5)/(A10) | II | first-order amplitude C_{n,k}(1) | transcribed |
| Eq.(6)/(A11) | II | W_{nm,k}(s) kernel | transcribed |
| Eq.(8) | II | population change Δρ_{n,k} (Fig. 2 target) | transcribed |
| Eq.(9)/(A26) | III | Δ⟨x⟩ raw decomposition | transcribed |
| Eq.(11) | III | Berry curvature B_n(β,k) | transcribed |
| Eq.(12) | III | average quasienergy E_{n,k}=int_0^1 ω_{n,k}[β(s)]ds | transcribed |
| Eq.(13) | III | final Δ⟨x⟩ = Berry integral - IBC correction (Fig. 3/4 target) | transcribed |
| Eq.(14) | IV | CDHM Hamiltonian | transcribed |

## Figure/Table Inventory

| Item | Caption summary | Class | Notes |
| --- | --- | --- | --- |
| Fig. 1(a) | Floquet eigenphases of CDHM vs k, β | numeric | J=K=3 |
| Fig. 1(b) | ρ_{n,k}(0) on 3 bands, initial state at l=0 | numeric | J=K=3 |
| Fig. 2(a) | actual Δρ_{n,k} vs k after one cycle | numeric | J=K=3, T=1024 |
| Fig. 2(b) | theoretical Δρ_{n,k} (Eq. 8) | numeric | J=K=3 |
| Fig. 3 | ⟨x⟩(t) over one cycle, 6 T; theory + Berry-only | numeric | J=K=4 |
| Fig. 4 | Δ⟨x⟩ vs J topological probe | numeric | J=K in [5,5.3], T=2560 |

## Assumptions

- Atomic spacing set to 1, so superlattice constant a = N = 3; k in [-π/3, π/3].
- Symmetry assumption for Eq. (10)/(13): k-reflection symmetry ρ_{n,-k}=ρ_{n,k},
  ω_{n,-k}=ω_{n,k} holds for the site-0 initial state and the left-right-symmetric
  undriven CDHM, so the ballistic (4th) term of Eq. (9) integrates to zero.
- Displacement Δ⟨x⟩ measured in units of the superlattice constant a (matches
  Fig. 3 y-axis reaching ~3-4 and Fig. 4 reaching ~15-20).
- Sign/phase convention of the Bloch hopping fixed by matching Fig. 1(a) band
  structure and the reported Chern numbers (4,-8,4) at J=K<5.14.
