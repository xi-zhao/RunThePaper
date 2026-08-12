# Derivation Trace

## EQC001–EQC003: N00N state through the MZI

The input is

`|psi> = sqrt(b)|20> + exp(2 i phi)sqrt(1-b)|02>`.

The single-photon operation is the printed `U(theta)=H'R(theta)H'`.  Replacing each input creation operator by its linear combination under `U` and collecting normalized bosonic occupations yields the 3×3 symmetric-square representation in the ordered basis `|20>,|11>,|02>`.  This construction preserves unitarity.  At `theta=pi/2`, `phi=0` gives probabilities `[1/2,0,1/2]`; `phi=pi/2` gives `[0,1,0]`.

Code: `quantum.py::{mzi_unitary,two_photon_lift,noon_state,output_probabilities}`.

## EQC004: partial indistinguishability

Supplement Eq. (2) replaces the pure superposition by a density matrix whose off-diagonal coherence is multiplied by `p`.  Its eigenvalues are nonnegative for `0<=p<=1`, its trace is one, and propagation uses `rho_out=Gamma_2(U) rho Gamma_2(U)^dagger`.

Code: `quantum.py::noon_density`.

## EQC005–EQC006: classical transfer and HOM visibility

Classical output powers are `|U_jk|^2`.  For a splitter of reflectivity `R`, distinguishable and indistinguishable coincidence probabilities give

`V=1-(2R-1)^2/(R^2+(1-R)^2)`.

For signal/idler-dependent reflectivities, both coincidence expressions are weighted over the pair spectrum before taking the ratio.  `V(1/2)=1` and `V(0)=V(1)=0`.

## EQC007–EQC008: HOM width and brightness

The delay curve is `C(tau)=C_inf[1-V exp(-4 ln2 tau^2/w^2)]`.  The program reports multiple transform conventions instead of selecting one silently.  Two independent photon losses give

`B = C_det * 10^(2 L_dB/10) / P_mW`,

which evaluates to `2.309e8 pairs/s/mW` for the printed rounded inputs.

## EQC009: declared mode/loss reconstruction

The scalar transverse Helmholtz operator is discretized on a 2-D finite-difference grid.  Its largest guided eigenvalue gives `beta^2` and `n_eff=beta/k0`; intensity is area-normalized.  Electrode loss is estimated from modal overlap with a lateral gold region.  This produces the scientific modal localization and monotonic loss-vs-gap feature, while remaining explicitly distinct from the unpublished vector FEM.

## Gate Result

All nine equation cards are open: eight verified formula chains and one source-traced declared reconstruction.  Machine result: `outputs/checks/formula_verification.json`.
