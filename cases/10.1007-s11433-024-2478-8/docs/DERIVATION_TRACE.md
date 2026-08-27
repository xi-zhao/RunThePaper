# Derivation Trace — Buffer-atom-mediated ORMD CZ gate (Sun 2024)

Paper: Y. Sun, *Buffer-atom-mediated quantum logic gates with off-resonant
modulated driving*, Sci. China-Phys. Mech. Astron. **67**, 120311 (2024).
DOI 10.1007/s11433-024-2478-8.

## Physical picture

Three atoms sit in a line: control qubit — buffer — target qubit. The buffer is
always prepared in `|1>`. Qubit register state `|0>` is dark (decoupled from the
drive); `|1>` is coupled to a Rydberg state. Because the two qubit atoms are far
apart, only the two adjacent pairs (control–buffer, buffer–target) interact via
the Rydberg dipole–dipole (Förster) interaction. The buffer therefore *mediates*
an effective two-qubit interaction between control and target that do not
directly interact — extending the two-qubit gate beyond nearest neighbour.

The gate is an **off-resonant modulated driving (ORMD)** CZ: smooth
Fourier-series waveforms `Ω(t), Δ(t)` (§Waveform) drive the system so that every
register input returns to its initial state (no Rydberg leakage) while
accumulating a state-dependent phase, and the four phases realise a CZ up to
single-qubit Z rotations.

## Waveform definition (card `fourier_waveform`)

Main text p.4. Each Rabi/detuning waveform is a real cosine series

```
f(t) = 2π · ( a0 + 2 Σ_{n=1..N} a_n cos(2π n t / τ) ) / (2N + 1)   [rad/µs],  τ = 0.25 µs
```

fixed by a coefficient list `[a0, a1, …, aN]`. Self-consistency check: the hybrid
`Ω₂` list `[112.83, −46.32, −11.51, 2.35, 0.193, −1.14]` gives `Ω₂(0) ≈ 0`
(smooth turn-on) and `Ω₂(τ/2) ≈ 2π·16.4 MHz`, so `Ω₁ = 0.686·Ω₂` peaks at
`2π·11.2 MHz` — matching the plotted curves of Fig. 3(a). See
`src/waveforms.py`.

## Register-sector decomposition

With the buffer fixed in `|1>` and `|0>` dark, each two-qubit input maps to an
independent three-body sector whose dynamics is a closed sub-problem:

| register input | three-body state | active atoms | Hamiltonian | states |
|---|---|---|---|---|
| `|00>` | `|010>` | buffer only | `H_b` (a1), card `h_sector00` | 2 |
| `|01>`,`|10>` | `|011>`,`|110>` | buffer + 1 qubit | `H_s` (a3), card `h_sector01` | 5 |
| `|11>` | `|111>` | all three | `H_d` (a4), card `h_sector11` | 9 |

Rotating-frame convention (appendix): `H = (Ω/2)(|g><e| + h.c.) + Δ|e><e|`,
`ħ = 1`. Buffer couples `|1>↔|r>` with `(Ω₁, Δ₁)`; each qubit couples `|1>↔|r'>`
with `(Ω₂, Δ₂)`. The dipole–dipole interaction is a Förster resonance: an
adjacent pair in `|r r'>` couples with strength `B` to a pair state `|q q'>` at
extra energy `δ_q` (set to 0 throughout).

### Sector `|00>` — eq. (a1)

Only the buffer is bright: `{|1_b>, |r_b>}`, a driven two-level system.
Limiting check: constant `Ω`, `Δ=0` gives the textbook Rabi law
`P_e = sin²(Ωt/2)` (test `test_rabi_analytic_limit`).

### Sector `|01>`/`|10>` — eq. (a3)

Buffer + one qubit, basis `{|1_b1_u>, |r_b1_u>, |1_br'_u>, |r_br'_u>, |q_bq'_u>}`.
Reproduces (a3) verbatim, including the Förster coupling `|r_br'_u>↔|q_bq'_u>`.

### Sector `|11>` — eq. (a4), reconstructed in the product basis

The paper writes `H_d` in a Morris–Shore-reduced form (symmetric combinations of
the two identically-driven qubit atoms). Rather than transcribe that error-prone
reduced form, we build the **full 9-state product Hamiltonian** from the local
driving rules + Förster couplings, applying the physical truncation that
triply-excited states are blockaded:

```
|111>, |r'11>, |1r1>, |11r'>, |r'r1>, |1rr'>, |r'1r'>, |q'q1>, |1qq'>
```

with Förster couplings `|r'r1>↔|q'q1>` and `|1rr'>↔|1qq'>`.

**Equivalence proof (card `h_sector11`, symbolic_identity check).** Forming the
symmetric qubit combinations `|B1>=(|r'11>+|11r'>)/√2`,
`|B2>=(|r'r1>+|1rr'>)/√2`, `|Bq>=(|q'q1>+|1qq'>)/√2`, the product basis
reproduces the published couplings exactly: `|111>↔|B1>` at `(√2/2)Ω₂`,
`|1r1>↔|B2>` at `(√2/2)Ω₂`, `|B1>↔|B2>` at `Ω₁/2`, `|B2>↔|Bq>` at `B`, and the
diagonal `2Δ₂` on `|r'1r'>`. The antisymmetric combinations decouple from `|111>`
and stay dark for all time — verified numerically to `< 1e-10` population, which
both validates the reconstruction and confirms the Morris–Shore reduction.

## CZ metric (card `cz_gate_metric`)

The CZ conditional (entangling) phase is `Φ = φ_11 + φ_00 − 2φ_01`, which must be
`π`. The average gate error is `1 − F` with the Pedersen average-fidelity formula
`F = (|tr(U_t†U)|² + tr(U†U)) / (d(d+1))`, `d=4`, realised gate `U = diag(a_k)`,
ideal `U_t = e^{iθ}(Z_c⊗Z_t)CZ` optimised over the single-qubit Z phases (the
paper's "typical way", refs [48,49] = Pedersen 2007). See `src/gate.py`.

## Result

Independent integration of the reconstructed Hamiltonians with the paper's own
waveform coefficients yields, at `t=τ`:

| protocol | Φ/π | gate error | max leakage |
|---|---|---|---|
| Fig. 3 hybrid | −1.00000 | 6.5×10⁻⁶ | 1.2×10⁻⁵ |
| Fig. 3 amplitude-only | −0.99985 | 5.6×10⁻⁵ | 1.0×10⁻⁴ |

Both satisfy the paper's claim "gate errors less than 10⁻⁴" and realise the CZ
conditional phase π — a self-validating reproduction, since wrong Hamiltonians
would not reproduce the paper's quantitative claim from its own coefficients.
