# Numerical Methods

## NUM001 — minimum-variance ensemble

- Targets: T002–T009.
- Formula cards: EQ001–EQ003, EQ008.
- Input: eigensystem of the thermal Hamiltonian \(H_0\), target Hamiltonian \(H\),
  and inverse temperature \(\beta\).
- Stable construction:
  \[
  (H_\rho)_{mn}=
  \operatorname{sech}[\beta(e_m-e_n)/2]\,H_{mn}
  \]
  in the \(H_0\) eigenbasis.
- Solver: Hermitian dense `eigh`; NumPy locally, CuPy/cuSOLVER on A100.
- Outputs: \(E_{\rho,i},p_i,|\varphi_i\rangle\).
- Hard checks: density reconstruction, normalization, representative energy,
  and QFI/minimum-average-variance identity.
- Risk: extremely small \(p_i\) at low temperature magnifies pointwise
  floating-point error. Both all-state and population-active errors are saved.

## NUM002 — spin-chain Hamiltonian

- Targets: T002–T009.
- Formula card: EQ006.
- Paper couplings: exact values from captions.
- Boundary: periodic reconstruction, selected after the \(L=6\) sensitivity
  canary matched the source curves substantially better than open boundaries.
- Construction: sparse Pauli-string action in the computational basis, then a
  dense Hermitian matrix for exact diagonalization.
- Site observable: central site/pair; under periodic translation-invariant
  states this is equivalent to every translated site.
- Random seed: not applicable.

## NUM003 — typicality diagnostic

- Targets: T002, T004–T007.
- Formula card: EQ005.
- Shell: centred rolling mean over `round(sqrt(d))` consecutive levels with
  truncated edge windows.
- Grid: \(\Delta=0,0.0025,\ldots,0.17\).
- Observable basis: \(\sigma^{x,y,z}\) on one site and all nine
  \(\sigma^\alpha\otimes\sigma^\beta\) nearest-neighbour products.
- Output: one CSV row per `(group,L,beta,observable,family,Delta)`.
- Risk: the paper states only \(O(\sqrt d)\), so the exact integer and edge
  convention are reconstructed metadata and remain disclosed.

## NUM004 — spectral compression

- Targets: T008A, T008B, T009.
- Formula card: EQ009.
- Method: transform spectral and minimum-variance representatives into the
  \(H\) eigenbasis; compute columnwise Shannon entropy and participation
  number; then population-weight the entropies.
- Efficiency: reuse the same \(H,H_0,H_\rho\) eigensystems produced for the
  typicality target.
- Output: scatter-level CSV plus per-\(\beta\) weighted summaries in JSON.

## NUM005 — spin-1 geometry

- Target: T001.
- Formulas: EQ003–EQ004 plus the paper's Gell-Mann parameterization.
- Exact leaf vertices:
  \[
  (n_1,n_3,n_8)=(x,\pm\sqrt{1-x^2},1/\sqrt3),\quad
  (0,0,-2/\sqrt3).
  \]
- Leaf-canonical curves: Gibbs-weighted convex combinations of the three
  vertices with representative energies \(1.5\pm\sqrt{1-x^2}/2,-3\).
- Checks: common vertex, pure-state radius, convex-hull containment, entropy
  ordering.

## NUM006 — mixed and representative dynamics

- Target: T003.
- Formula cards: EQ002–EQ003, EQ006–EQ007.
- Exact mixed curve: diagonalize \(H\), transform the thermal density matrix
  into the \(H\) basis, and evaluate
  \(\sum_{ab}\rho_{ab}O_{ba}e^{-i(E_a-E_b)t}\).
- Representative: minimize the paper's
  \[
  \delta_i=\frac{|E_{\rho,i}-\mathrm{tr}(\rho H)|}
  {\sqrt{\mathrm{Var}_{\varphi_i}(H)+F_Q(\rho;H)/4}}.
  \]
- Confidence shell: use the paper's stated
  \(\delta_i-\delta_{\min}\le(\delta_{\max}-\delta_{\min})/L\).
  The paper does not state a numerical interval algorithm. The reproduction
  reports empirical 16/84 and 2.5/97.5 percentiles over the complete
  214-representative delta shell at \(L=12\).
- Efficiency: transform the mixed-state observable kernels once; evolve the
  sampled pure states as a single dense matrix and apply local Pauli strings
  by permutations.
- Hard checks: all ensemble invariants, direct-vs-spectral \(t=0\) mixed
  expectations, finite trajectories, and explicit shell/sample counts.

## Efficiency and reuse

- Baseline: transparent dense exact diagonalization; no approximation.
- Bottleneck: \(O(d^3)\) eigendecompositions and basis transforms.
- Reuse rule: process all \(\beta\) values inside one `(H0 family,L)` shard.
- Checkpoint rule: atomic CSV/JSON per group and size.
- The final dynamics figure uses the complete delta shell; the mixed line and
  selected-representative trajectory are also exact at the stated size.
- Case-specific code stays under this case; only a future domain-neutral
  minimum-variance primitive should be considered for harness promotion.
