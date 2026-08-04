# Derivation Trace

## EQ001 — J1-J2-J3 Hamiltonian

Source: Eq. (1). With pair energies counted once, `H=ΣNN s_i s_j + R ΣNNN s_i s_j + R' Σ3NN s_i s_j` in units of `|JNN|`. Flipping `s_i` changes the energy by `ΔE=-2 s_i h_i`, where `h_i` is the weighted 12-neighbor field. Implemented in `src/ising_j1j2j3.py::{energy_per_spin,flip_delta_energy}` and the Torch runner. Status: verified.

## EQ002 — ordered-state energies

Source: Eqs. (2a)-(2d). Bond counting for the four periodic patterns gives
`u_c=-2+2R+2R'`, `u_SAF=-2R+2R'`, `u_44=-2R'`, and `u_42=-1`.
The exact phase label is the `argmin` of these affine functions; pairwise equalities are the Fig. 2 boundaries. Implemented in `ground_state_energies` and checked against explicit lattices. Status: verified.

## EQ003 — Fourier interaction

Source: Eqs. (3)-(4). Fourier transforming the three bond classes produces the printed `J(q)` and the source's Lifshitz stability discussion. This lane is source-traced but unused by current numerical code. Status: source-only.

## EQ004 — thermodynamic integration

Source: Eqs. (5)-(6). Integrating `U` over inverse temperature recovers `F/(kBT)`, and a first-order jump obeys `ΔS=ΔU/(kBT)`. The missing integration grid and hysteresis branches prevent exact numeric reconstruction. Status: source-only.

## EQ005 — cumulants and scaling

Source: Eqs. (7)-(14). `U_L=1-<m^4>/(3<m^2>^2)` and pseudocritical shifts scale as `L^{-1/ν}`. Hyperscaling gives `ν=2/(d+α/ν)`; inserting `d=2` and `α/ν=0.92` gives `ν≈0.685`, consistent with the quoted 0.68. Full fits remain source-only because Fig. 15's `R` is ambiguous and histories are unavailable.

## EQ006 — large-R' decoupling

Axial distance-two bonds partition the square lattice into four independent sublattices. Hence the normalized discontinuities vanish as `R'→∞`, matching the text after Fig. 15. Status: verified as a structural limit.

Formula gate record: `outputs/checks/formula_verification.json`.
