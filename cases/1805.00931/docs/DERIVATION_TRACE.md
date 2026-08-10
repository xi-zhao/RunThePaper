# Derivation Trace

## Scientific chain

### EQ001 → microscopic Floquet matrix

For a computational basis vector `|s>` with `s_j=±1`, periodicity gives

```text
E_I(s) = J sum_j s_j s_(j+1) + sum_j h_j s_j.
```

Therefore `exp(-i H_I)` is diagonal. Since the transverse terms commute across
sites,

```text
exp(-i H_K) = tensor_j [cos(b) I - i sin(b) sigma_x].
```

Multiplying the diagonal phase into the columns of the kick matrix yields the exact
finite-chain Floquet operator used by the code. No figure data enter this step.

### EQ002 + EQ003 → Figure 2 data

If `lambda_n=exp(-i phi_n)` are the Floquet eigenvalues,

```text
tr(U^t) = sum_n lambda_n^t,
K(t) = |sum_n lambda_n^t|^2.
```

The executed feature route uses one eigendecomposition per disorder realization to
produce every integer time. That route is exact at small `L` but cannot scale to the
paper's `L=15` ensemble. The code-ready paper route instead applies `U` matrix-free to
independent random-phase probes. If `X_z=z^dagger U^t z` and `X_w=w^dagger U^t w` use
independent probes, then

```text
E[X_z] = tr(U^t),
E[Re(X_z conjugate(X_w))] = |tr(U^t)|^2.
```

Thus the cross estimator is unbiased for the same SFF observable; unlike squaring one
noisy trace estimate, it adds no positive trace-estimation bias. Independent Gaussian
`h_j` are sampled with the paper's mean and standard deviation, and ensemble
means/standard errors are checkpointed before rendering.

### EQ004 → COE reference

For `0<t<N`, the paper prints

```text
K_COE(t) = 2t - t log(1 + 2t/N).
```

For plots extending beyond the reduced model's Heisenberg time, continuity uses the
standard complementary branch

```text
K_COE(t) = 2N - t log((2t+N)/(2t-N)),  t>N.
```

The paper-scale `N=2^15` curve and reduced `N=2^8` curve are both stored so their
different roles cannot be confused.

### EQ005 + EQ006 → matrix-free transfer action

The Gaussian characteristic function applied to two replicas gives

```text
O_sigma[a,b] = exp[-sigma^2 (M_z[a]-M_z[b])^2 / 2].
```

Under the paper's operator/state correspondence and row-major vectorization,

```text
(U tensor U*) O_sigma |A>  <=>  U (O_sigma elementwise A) U†.
```

Both left and right multiplications are implemented as diagonal Ising phases plus
`t` local two-state butterflies. A `4^t` dense matrix is never built. At `t=3`, the
action is compared element by element with an explicit Kronecker product.

### EQ007 → Figure 3 gap

The desired mode is the largest eigenvalue strictly inside the unit circle. Direct
Arnoldi would spend its Krylov space on the highly degenerate `±1` sectors. The code
therefore constructs those sectors from the same algebra proved in the supplement:

1. represent all `Pi^j` and `R Pi^j` as normalized basis-index permutations;
2. add the even-time singlet projector `Z` as a low-rank factor when independent;
3. at `t=6`, add the two phase-`pi` cross operators;
4. at `t=8`, add the printed spin-triplet projector `Z'`;
5. at `t=10`, add `Z''` and its two phase-`pi` cross operators. Because the arXiv
   source repeats and cancels one ket in displayed Eq. (175), reconstruct its unique
   state from the separately printed zero-momentum, odd-reflection, spin-singlet and
   Floquet-phase conditions rather than guessing a missing author value;
6. compute the small component Gram pseudoinverse and apply the orthogonal complement
   implicitly, without storing `4^t x O(t)` dense columns;
7. use projected Arnoldi for small verification systems and five-step,
   six-basis-slot explicitly restarted Arnoldi for the memory-bounded paper run;
8. compute `Delta=1-max|lambda(P T P)|`.

Complete diagonalization for `t<=5` checks both projected SciPy Arnoldi and the
restarted paper solver against the same subunit spectral radius. Protected ranks are
constructed and checked through `t=15`. At `sigma=0`, `T` is unitary and the code
returns zero gap.

### EQ008 → Table I without table copying

The Hilbert-Schmidt overlap between two qubit-site permutation operators is

```text
tr(P_g† P_h) = 2 ** number_of_cycles(g^{-1} h).
```

Thus a `2t x 2t` Gram matrix determines the rank of the entire dihedral operator span
without constructing `4^t` vectors. The supplement proves which additional sectors
are independent:

- `t=6`: one extra `+1` projector and two `-1` operators;
- `t=8`: the generic singlet plus one triplet projector;
- `t=10`: the generic singlet plus one further projector and two `-1` operators;
- even `t>=12`: one generic singlet projector;
- no extra sectors for the remaining tabulated times.

Adding these derived counts to the computed Gram rank produces all Table I entries
for `t=2..17`. The printed table is used only as an after-run falsification check.

## Scale boundary

The derivations and paper-scale code/config contracts are ready; the executed Figure
2/3 evidence is still reduced. That distinction is encoded in both configs, target
contracts, `figure_coverage.json`, and the authoritative state. No rescaling or fitted
physical parameter is used to make reduced data look closer to the source image.
