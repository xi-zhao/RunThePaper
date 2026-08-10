# Derivation Trace

## T001: charge-resolved probability and entropy

1. The infinite half-filled chain gives the Toeplitz kernel
   \(C_{ij}=\sin[\pi(i-j)/2]/[\pi(i-j)]\), with diagonal limit `1/2`.
2. Diagonalizing `C` gives independent mode occupations \(f_l\). The reduced density matrix factorizes into two-level modes.
3. For each mode, multiply the charge polynomial by \((1-f_l)+f_l z\). A companion recurrence propagates the entropy weight \(-p\ln p\). This produces \(P(N_A)\) and \(\mathcal S(N_A)\) without Fourier discretization.
4. The charged moment scaling is Gaussian in flux. Fourier transformation gives the charge distribution. Differentiation at `n=1` gives the entropy contribution.
5. The `O((ln L)^0)` free-fermion corrections stated in the paper are included through
   \(\sigma^2=[\ln(2L)+\gamma_E+1]/\pi^2\) and the known entropy constant `0.495017908135137`. No fit parameter is used.

## T002: charge-resolved entanglement spectrum

1. Convert correlation eigenvalues to entanglement energies with
   \(\varepsilon_l=\ln[(1-f_l)/f_l]\).
2. Select the 24 modes nearest zero exactly as specified in the Fig. 3 caption. Freeze the remaining active modes in their most probable occupations.
3. Enumerate all \(2^{24}\) binary occupations. Sum log weights and charge shifts relative to the filled negative-energy state, then rank the weights in the all-sector set and separately for \(\Delta N_A=0,1,2,3,4,5\).
4. Transform each eigenvalue to the paper's horizontal coordinate
   \(x=2\sqrt{-\ln\lambda_{\max}\ln(\lambda_{\max}/\lambda)}\).
5. Independently evaluate Eq. (11) with 512-node Gauss-Legendre quadrature. For the all-sector curve the expression reduces to `I0(x)`, providing a direct identity check.

## Rejected first pass and unresolved paper-label discrepancy

The source Fig. 3 legend literally lists `0,1,2,3,5,6`. A first isolated run therefore evaluated those labels. It passed probability and entropy invariants but could not reproduce the last two curve positions: the `Delta N=5` branch starts near `x=9`, and `Delta N=6` lies outside the plotted range.

Equation (9) requires charge-sector onset to grow approximately linearly with `|Delta N_A|`. The source figure's purple and orange curves start near `x=7.2` and `x=9.0`, where the independently computed `Delta N=4` and `Delta N=5` branches start. This creates a stable discrepancy between the formula-derived curve identities `0,1,2,3,4,5` and the printed labels `0,1,2,3,5,6`.

The run following the literal printed labels is retained as `paper-exact-v1`. The numerical reproduction view `paper-exact-v2` follows the equations and labels the final two branches `4,5`, but protocol-v2 does **not** treat that choice as proof of a paper error. The discrepancy remains `inconclusive` until a fresh reviewer falsifies alternative interpretations and validates the required cross-check record.

## Paper-scale execution trace

The original accepted path enumerated all `2^24` occupations in one vectorized
array. The code-ready rerun path in `paper_scale.py` preserves the same exact
top-1000 numerical object while partitioning the integer occupation space. Each
shard keeps only its exact top candidates for `all,0,...,5`; the aggregate of
per-shard top-k sets is mathematically the global top-k set. Correlation modes,
the Fig. 2 recurrence, numerical shards, and analytic shards are config-hash
checkpointed and resumable.

## Code Pointers

- EQ001, EQ002, EQ004: `src/symmetry_entanglement/model.py`
- T001/T002 orchestration and checks: `src/symmetry_entanglement/reproduction.py`
- Accepted isolated attestation: `outputs/runs/1711.09418-paper-exact-v2/run_attestation.json`
