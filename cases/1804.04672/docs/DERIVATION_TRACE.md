# Derivation Trace

This case is formula-heavy. Every numerical target must map back to a source
equation or an explicit reconstruction step before code is written.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer once implementation exists.

`T001` now has case-local code, generated paper-parameter data, and a rendered
red branch selected by the analytic chiral edge trace. Boundary-localization
weights and non-Bloch bulk-continuum distance are retained as diagnostics, not
as the red-branch definition.

## EQC001: Main Bloch Hamiltonian

Source: TeX label `model`.

The paper defines:

```text
H(k) =
  (v_x sin k_x + i gamma_x) sigma_x
  + (v_y sin k_y + i gamma_y) sigma_y
  + (m - t_x cos k_x - t_y cos k_y + i gamma_z) sigma_z
```

For the main numerical figures, the paper then uses:

```text
v_x = v_y = 1
t_x = t_y = 1
gamma_x = gamma_y = gamma
gamma_z = 0
```

For the first target:

```text
gamma = 0.2
m = 1.717
```

This equation defines the two-band non-Hermitian Chern model. The Hermitian
part is the Qi-Wu-Zhang Chern-insulator model; the non-Hermitian part appears
as imaginary Zeeman fields.

## EQC002: Cylinder Finite-Strip Hamiltonian

Source: cylinder paragraph and Fig. `cylinder` caption.

The first target uses periodic boundary condition in `x` and open boundary in
`y`. Therefore `k_x` remains a good quantum number, while the `y` direction is
a finite chain of length `L_y`.

Starting from EQC001, collect all `k_x` terms into an on-site block:

```text
M(k_x) =
  (v_x sin k_x + i gamma_x) sigma_x
  + i gamma_y sigma_y
  + (m - t_x cos k_x + i gamma_z) sigma_z
```

The `y` direction comes from:

```text
v_y sin k_y sigma_y - t_y cos k_y sigma_z
```

Using:

```text
sin k_y = (e^{i k_y} - e^{-i k_y}) / (2i)
cos k_y = (e^{i k_y} + e^{-i k_y}) / 2
```

the hopping block in the positive `y` direction is:

```text
T_y = -t_y/2 sigma_z - i v_y/2 sigma_y
```

and the reverse hopping is:

```text
T_y^dagger = -t_y/2 sigma_z + i v_y/2 sigma_y
```

Thus the finite strip Hamiltonian is:

```text
H_y(k_x) =
  sum_y c_y^dagger M(k_x) c_y
  + sum_y c_y^dagger T_y c_{y+1}
  + sum_y c_{y+1}^dagger T_y^dagger c_y
```

For `L_y=40`, this is an `80 x 80` matrix for each `k_x` value.

The first runner must generate all eigenvalues for `180` sampled `k_x` values
and store at least:

```text
target_id
kx
band_index
energy_real
energy_imag
edge_label
edge_weight_left
edge_weight_right
```

Implementation:

```text
src/nonhermitian_chern.py:cylinder_hamiltonian
src/nonhermitian_chern.py:generate_cylinder_spectrum_rows
scripts/run_first_target.py
```

## T001 Edge-State Classification Requirement

The paper panel colors chiral edge states red. The source EPS can be used as a
reference, but the generated runner must not copy red points from the source
panel.

The implementation must define an edge-state rule before rendering. Boundary
weight alone is not enough:

```text
edge_weight = probability weight on a fixed number of top/bottom y layers
edge_label = edge_weight > threshold
```

The runner records this as `edge_localization_candidate`, not directly as the
paper's red chiral branch. This is deliberate: in a non-Hermitian open-boundary
spectrum, right-eigenvector boundary weight can also reflect skin-effect
localization.

For the rendered red branch, use the analytic cylinder edge traces:

```text
E_+(k_x) = sin(k_x) + i gamma
E_-(k_x) = -sin(k_x) - i gamma
```

At each sampled `k_x`, the runner finds the nearest finite-strip eigenvalue to
each trace and marks it red only when the residual is below `0.005` and the
state remains on the `Im(E)=+-gamma` plateau. This gives `102` red points,
matching the red point count extracted from the source `energy.eps`. The
non-Bloch cylinder bulk continuum remains important: it explains why
skin-localized bulk states should not be colored red merely because their
right eigenvectors have large boundary weight.

## EQC003: Non-Bloch Chern Number

Source: TeX label `chern`.

The paper defines a non-Bloch Chern number using right and left eigenvectors in
the generalized Brillouin zone:

```text
C = (1 / 2 pi i) integral epsilon^{ij}
    <partial_i u_L(tilde k) | partial_j u_R(tilde k)>
```

For `T001`, this is interpretive context. The runner does not need to compute
the Chern number to generate the cylinder spectrum, but the report must avoid
claiming full non-Bloch topology reproduction from the spectrum alone.

## EQC005: Fig. 1 Open-Boundary Phase Boundaries

Source: TeX labels `mpm` and `quadratic`, plus the supplemental numerical
boundary table `diskdata`.

The ordinary Bloch Hamiltonian predicts gap-closing boundaries:

```text
m_\pm = t_x + t_y ± sqrt(gamma_x^2 + gamma_y^2)
```

For the symmetric Fig. 1 parameters:

```text
t_x = t_y = v_x = v_y = 1
gamma_x = gamma_y = gamma
gamma_z = 0
```

this becomes:

```text
m_\pm = 2 ± sqrt(2) gamma
```

These are the gray dotted lines in Fig. 1. They are not the open-boundary
topological transition curve.

The non-Bloch low-energy theory shifts the wavevector into the complex plane.
For the same symmetric parameters, the effective mass is:

```text
tilde m = m - 2 - gamma^2
```

The non-Bloch Chern number changes when `tilde m=0`, so the theory boundary is:

```text
m_c = 2 + gamma^2
```

This is the blue dashed curve in Fig. 1. The red curve in the paper is the
numerical open-boundary transition boundary obtained from finite-size spectra
and gap-square extrapolation. The current `T003` runner keeps these as three
separate physical series:

```text
bloch_boundary_lower / bloch_boundary_upper
non_bloch_theory_boundary
source_numerical_boundary
```

The red series currently uses the supplemental numerical boundary table as a
reference, so it is not yet a fresh independent square finite-size
extrapolation. This is why `T003` is scored as partial evidence rather than
complete reproduction.

## EQC006: Fig. 2 Square Spectrum And Wave-Packet Evolution

Source: Fig. `square` caption and the real-space Hamiltonian in the
supplement.

Fig. 2 uses the same open-boundary square Hamiltonian as the Fig. 1 numerical
phase diagram. The two parameter points are the markers shown on Fig. 1:

```text
Fig. 2(a): gamma = 0.15, m = 2.2121
Fig. 2(b): gamma = 0.15, m = 1.7879
L = 30
```

The left panel in each row is the low-energy part of the square spectrum. The
right three panels use the caption wavepacket:

```text
psi(t=0) = N exp[-(x-15)^2/40 - (y-1)^2/10] (1,1)^T
```

and evolve it by:

```text
i partial_t |psi(t)> = H |psi(t)>
psi(t) = exp(-i H t) psi(0)
```

The displayed intensity is:

```text
I(x,y,t) = sum_{orbital=A,B} |psi_{x,y,orbital}(t)|^2
```

renormalized so that the total intensity of each displayed time slice is
`1`. This is important because the Hamiltonian is non-Hermitian and the norm
is not conserved.

The physical distinction between the two rows is:

```text
Fig. 2(a): no chiral edge mode; the wavepacket fades into the bulk.
Fig. 2(b): in-gap chiral edge modes; the wavepacket shows edge motion.
```

The current `T004` runner generates the low-energy spectra and the normalized
intensity maps independently. It does not yet digitize the source intensity
maps into a pixel-level gate.

## EQC004: Cylinder Non-Bloch Bulk Continuum

Source: supplemental section V, labels `bulkeigen2`, `boundarycond`,
`equalmod`, and `bulkbetay`.

For the cylinder, `kx` remains a good quantum number. Along the open `y`
direction the bulk ansatz is:

```text
(psi_n,A, psi_n,B) = beta^n (phi_A, phi_B)
```

Substituting this ansatz gives the quadratic equation:

```text
[(m - t_x cos kx - gamma_y) - t_y beta^-1]
[(m - t_x cos kx + gamma_y) - t_y beta]
= E^2 - (t_x sin kx + i gamma_x)^2
```

For an energy belonging to the continuum bulk spectrum, the two beta roots
must obey the equal-modulus condition:

```text
|beta_1(E)| = |beta_2(E)|
```

Using Vieta's formula, the common radius is:

```text
r(kx) = sqrt(abs((m - t_x cos kx + gamma_y)
                 / (m - t_x cos kx - gamma_y)))
```

Therefore the non-Bloch cylinder bulk continuum at fixed `kx` is obtained by
sampling:

```text
beta = r(kx) exp(i ky_tilde)
```

and inserting it into the original Bloch Hamiltonian. This continuum is the
right comparison object for `T001`: a state can have large boundary weight
because of the non-Hermitian skin effect and still belong to the bulk
continuum. A conservative red-branch classifier must therefore use separation
from this non-Bloch bulk continuum. For Fig. 3(b), the accepted first-pass red
subset is the plateau branch satisfying `| |Im(E)| - gamma_x | <= 0.01` and
distance at least `0.005` from the sampled non-Bloch continuum. Boundary weight
is kept as a diagnostic, not a hard gate, because the skin effect biases right
eigenvectors toward a boundary.

Implementation:

```text
src/nonhermitian_chern.py:non_bloch_cylinder_radius
src/nonhermitian_chern.py:non_bloch_cylinder_hamiltonian
src/nonhermitian_chern.py:non_bloch_cylinder_bulk_eigenvalues
scripts/analyze_edge_branch_candidates.py
```

## EQC007: Finite-Size Gap-Square Extrapolation

Source: supplemental section I and Supplemental Fig. S2 (`fitting`).

The phase-boundary scan asks whether the open-boundary spectrum is gapped in
the thermodynamic limit. For a finite disk of radius `L`, the numerical
diagnostic is the smallest spectral distance to zero:

```text
|Delta(L)|^2 = min_E |E|^2
```

The supplement states that this quantity is plotted against `1/L^2`, and that
the linear-fit intercept gives the thermodynamic-limit gap square:

```text
|Delta(L)|^2 = a/L^2 + b
b = |Delta(L -> infinity)|^2
```

The physical interpretation is:

```text
b > 0  : open-boundary bulk spectrum remains gapped.
b ~= 0 : gap closes in the thermodynamic limit, marking the phase boundary.
```

Supplemental Fig. S2 uses `gamma_x=gamma_y=0.2` and shows three examples:

```text
m = 2.2000 : nonzero intercept
m = 2.0800 : nonzero intercept
m = 2.0400 : near-zero intercept
```

The last value is the non-Bloch prediction `m_c=2+gamma^2=2.04` for
`gamma=0.2`, so S2 is the method-level bridge between the Fig. 1 red numerical
boundary and the formula-level blue theory curve.

Implementation:

```text
src/nonhermitian_chern.py:disk_hamiltonian_sparse
src/nonhermitian_chern.py:generate_disk_gap_scaling_rows
src/nonhermitian_chern.py:fit_gap_scaling_by_mass
scripts/run_gap_scaling.py
```

## Current Formula Gate Position

The current cards are still `source_only` or `reconstructed`, but all open
numeric cards now have code references and generated checks. This is enough
for independent feature-level data generation. It is not enough to claim full
paper-level reproduction because several source comparisons remain
source-visual only rather than digitized or pixel-gated.
