# Derivation Trace

## Geometry (EQ001)

The monolayer reciprocal vectors are rotated by 60 degrees. Substituting the local displacement `d0=theta z×r` gives `G_j·d0=b_j·r`. We choose two 120-degree primitive moire vectors `B1=b1` and `B2=b3`; the complete first shell is `±B1`, `±B2`, `±(B1+B2)`. Their dual vectors satisfy `B_i·A_j=2πδ_ij`, and both have length `a_M=a0/theta`.

The two rotated +K valleys fold to adjacent MBZ corners. In this gauge,

```text
kappa_plus  = (B1-B2)/3
kappa_minus = (2B1+B2)/3.
```

Their separation has magnitude `4π/(3a_M)`, the small-angle displacement of the monolayer K points.

## Local potential and tunneling (EQ002-EQ003)

Main Eq. (2) yields three positive Fourier coefficients `V exp(i l psi)` at `B1`, `B2`, and `-(B1+B2)` plus their conjugates. Main Eq. (3) yields coefficients `w` at `q=0`, `-(B1+B2)`, and `-B2` in the bottom-to-top block. Using `H_{G,G'}=V_{G-G'}` fixes every plane-wave matrix element without reading a plotted curve.

At the zero-displacement site, the formula gives `Delta_b=Delta_t=6V cos(psi)` and `Delta_T=3w=-25.5 meV`. The implementation test checks this high-symmetry value.

## Two-band continuum (EQ004)

For Bloch momentum `k`, each layer basis state is `exp[i(k+G)·r]`. Its kinetic energy is

```text
- (hbar^2/(2m*)) |k+G-kappa_l|^2,
```

with `hbar^2/(2m_e)=38.0998212 meV nm^2` and `m*=0.62m_e`. Fourier links from EQ002-EQ003 assemble a Hermitian `2N_G × 2N_G` matrix. Complete hexagonal reciprocal shells remove directional truncation bias. Main panels use cutoff 4 (61 plane waves per layer) and are checked against cutoff 5.

## Pseudospin and winding (EQ005)

The code evaluates the printed vector `(Re Delta_T†, Im Delta_T†, (Delta_b-Delta_t)/2)` directly. For the invariant, normalize it to `n=Delta/|Delta|`, take periodic central differences in primitive-cell coordinates `(u,v)`, and sum `n·(∂_u n×∂_v n)/(4π)`. The coordinate Jacobian cancels between derivatives and cell integration. A 151×151 grid gives `N_w=-0.9969`, converging to the printed `-1`.

## Bands, DOS and topology (EQ006)

Hermitian diagonalization returns bands in descending energy because the paper numbers hole bands from the valence maximum. The DOS uses the top four bands, both time-reversed valleys, a uniform MBZ mesh and a declared 0.12 meV Gaussian broadening. Hole filling is the number of states above the running energy, so it spans 0-8 holes per MUC.

The kinetic term is the only k-dependent matrix element, so `∂H/∂k_x,y` is diagonal. Inserting those derivatives in the Kubo sum produces Berry curvature in nm². Integrating it on a full reciprocal primitive cell yields `C1=-0.9778`, `C2=+0.9760` at 1.2 degrees. The deviations from integers are finite-grid/truncation error and have the correct paper signs.

Global adjacent-band gaps use exactly the caption definition `min(E_i)-max(E_j)`. The angle sweep recovers the second/third-band closing near 1.74 degrees and the first/second overlap near 3.1 degrees. The layer-bias transition is located by minimizing the direct corner gap; the separate tight-binding estimate is the zero-bias corner splitting stated in the paper.

## Kane-Mele reduction (EQ007)

The two layer-localized orbitals form a honeycomb lattice. The three nearest-neighbor vectors generate the off-diagonal `t0` structure factor; six triangular-lattice next-nearest neighbors generate layer diagonal terms with the printed phases `exp(i s kappa_l·a_M)`. `t0=0.29 meV` and `t1=0.06 meV` are unchanged. One constant shift aligns the arbitrary energy zero with the continuum plot and is stored in T002.

## Remote conduction bands (EQ008)

Each layer carries conduction/valence orbitals. The diagonal gap is `Delta_g=1.1 eV`; the off-diagonal massive-Dirac term is `hbar v_F(k_x∓ik_y)` with the printed layer rotation. Conduction and valence potentials use their distinct `(V,psi)` values. Three 2×2 tunneling harmonics implement all `w_c,w_v,w_cv,w_vc` phases from the supplement. Selecting eigenvalues below/above half the gap cleanly separates the valence and conduction target panels.

The derived expansion parameter `2(hbar v_F |kappa|/Delta_g)^2=0.00732` and monolayer curvature `-0.1146 nm²` agree with the supplement's scale estimates.

## Remote spin bands (EQ009)

The same plane-wave construction is repeated in layer×spin space. The down-spin sector is shifted by `Delta_SOC=220.5 meV`; each spin has its own potential and spin-conserving tunneling, while `w_up,down=-i5.6 meV` and `w_up,down=-w_down,up*` determine the off-diagonal tunneling matrices. The computed upper bands stay close to the two-band result, which is the robustness claim of the supplementary panels.

## Deferred DFT derivation

The supplement specifies fully relativistic LDA/PZ Quantum Espresso, 50/408 Ry cutoffs, 16×16×1 k points, 20 Å vacuum, fixed in-plane coordinates, z relaxation below 0.005 eV/Å and Wannier90 projection onto Te p/Mo d orbitals. This is enough to plan the workflow, but the exact pseudopotential files/version and a substantial first-principles run are still required. The figure is therefore not synthesized from the fitted continuum model.
