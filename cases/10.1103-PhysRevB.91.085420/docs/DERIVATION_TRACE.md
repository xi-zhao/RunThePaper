# Derivation Trace — PRB 91, 085420 (2015)

Human-readable trace of the derivation. The machine-checked cards are in
`EQUATION_CARDS.json`; the rendered equation-level view is `DERIVATION.md`
(auto-generated — do not hand-edit).

## 0. Physical question

For a periodically driven **closed** system taken adiabatically around a pumping
cycle (β: 0 → 2π over duration Tτ), what is the displacement Δ⟨x⟩ of the
wave-packet center when the initial state is a *general* superposition across
Floquet bands (not a single Floquet band)?

## 1. Floquet setup (Eqs. 1–3)

- One-period evolution operator U(β); Floquet eigenstates |ψ_{n,k}(β)⟩ with
  eigenphases ω_{n,k}(β): U(β)|ψ_{n,k}⟩ = e^{-iω_{n,k}}|ψ_{n,k}⟩ (Eq. 1).
- Parallel-transport gauge ⟨ψ|dψ/dβ⟩ = 0 ⇒ ψ(2π) = e^{-iγ}ψ(0), γ = Berry phase.
- Accumulated dynamical phase Ω_{n,k}(s_j) = Σ_{j'≤j} ω_{n,k}[β(s_{j'})] (Eq. 2).
- State expansion |Ψ(s)⟩ = √(a/2π)∫dk Σ_n C_{n,k}(s) e^{-iΩ_{n,k}(s)}|ψ_{n,k}[β(s)]⟩
  (Eq. 3); ρ_{n,k}(0) = |C_{n,k}(0)|² initial band populations.

## 2. First-order adiabatic perturbation theory (Eqs. 4–8, App. 1)

- Projecting |Ψ(s+ds)⟩ = U|Ψ(s)⟩ gives the transition equation dC_n/ds
  (Eq. 4 / A4).
- Integrating **by parts** (App. A5–A10, keeping O(1/T)):
  C_{n,k}(1) = C_{n,k}(0) + (1/T) Σ_{m≠n} C_{m,k}(0)[W_{nm,k}(s)]₀¹ (Eq. 5),
  with the kernel W_{nm,k}(s) of Eq. 6 / A11.
- Population change Δρ_{n,k} = |C_{n,k}(1)|² − ρ_{n,k}(0)
  = (2/T) Re[Σ_{m≠n} C*_n(0) C_m(0)(W_{nm,k}|₀¹)] (Eq. 8).
- **Key scaling**: for a single-band initial state the cross term C*_n C_m = 0 so
  Δρ ~ 1/T²; for a general (multi-band) initial state the interband-coherence
  (IBC) cross term is nonzero so Δρ ~ 1/T. This 1/T vs 1/T² split is what makes
  the correction survive.

Numerical realisation of W(0): using U|ψ_m⟩ = λ_m|ψ_m⟩ and ⟨ψ_n|U = λ_n⟨ψ_n|
(U unitary ⇒ normal ⇒ orthonormal eigenvectors),
⟨ψ_n|∂_βψ_m⟩ = ⟨ψ_n|∂_βU|ψ_m⟩/(λ_m − λ_n) (n ≠ m). This avoids any β-gauge
fixing; the physical combination C*_n C_m W_{nm} is gauge-invariant.

## 3. Wave-packet displacement (Eqs. 9–13, App. 2)

- The position operator in the Floquet-Bloch basis (App. A12–A19) gives ⟨x⟩ as an
  intraband-Berry-connection + amplitude-derivative integral; the interband
  ("third") term A19/A20 is rapidly oscillating and drops.
- Subtracting initial from final (A22 vs A25):
  Δ⟨x⟩ = Σ_n ∫dk [dγ_{n,k}/dk + dΩ_{n,k}(1)/dk] |C_{n,k}(1)|² (Eq. 9 / A26).
- Four terms arise. dγ/dk·Δρ → 0 (γ is T-independent, Δρ~1/T). The
  dΩ(1)/dk·ρ(0) term is odd in k under k-reflection symmetry ⇒ integrates to 0.
  The surviving pieces are the **weighted Berry-curvature integral**
  Σ_n ∫dk (dγ/dk) ρ_{n,k}(0) = Σ_n ∫∫ B_n(β,k) ρ_{n,k}(0) dβ dk (Eq. 11), plus
  the **IBC correction** from dΩ(1)/dk·Δρ. Because Ω(1)=T·E (Eq. 12) is ∝T while
  Δρ~1/T, their product is T-independent and non-vanishing.
- Final result (Eq. 13):
  Δ⟨x⟩ = Σ_n ∫dk ∫dβ B_n(β,k) ρ_{n,k}(0)
         − 2 Σ_{m≠n} ∫dk Re[C*_n(0) C_m(0)(dE_{n,k}/dk) W_{nm,k}(0)].
  Both terms are independent of T. Only W(0) survives the k-integration (the
  W(1)-part self-averages/oscillates away), which is why Eq. 13 needs only static
  β=0 quantities.

## 4. Unit / prefactor bookkeeping

⟨x⟩ is computed exactly from the dynamics in **atomic-spacing units** (x = 3n+j).
For a filled single band the Berry term must reduce to the Thouless result
Δx = a·C_n with a = N = 3 (one Wannier center per pumped charge per cell). This
fixes the overall a/(2π) prefactor carried by **both** terms of Eq. 13, and it is
independently confirmed by the exact dynamics (theory total 3.08 vs dynamics 3.10
at J=K=4). The (k,β)-torus orientation sign is a gauge choice; the physical
displacement comes out with the paper's positive sign once aligned to the
dynamics.

## 5. What the model calculation shows (Sec. IV, Figs. 1–4)

- Fig. 1: Floquet spectrum and initial populations for J=K=3.
- Fig. 2: Eq. 8 reproduces the actual one-cycle Δρ (feature level).
- Fig. 3: Δ⟨x⟩ is T-independent; the Berry-only term (4.32) is far from the true
  displacement (3.10); the IBC correction (−1.24) closes the gap.
- Fig. 4: scanning J=K across the Floquet-Chern transition (~5.14), the corrected
  theory tracks the actual displacement and both jump at the transition, while the
  Berry-only term does not follow the actual result — a topological-transition
  probe from a trivial site-0 initial state.
