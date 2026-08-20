# Derivation Trace

Use this file for formula-heavy papers. Every implemented equation should map
back to a source equation or an explicit derivation step.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until its formula dependencies are traceable and
the formula gate is not closed.

## Equation Cards

### EQ001--EQ003: spin chain to block entropy

1. Start from the printed XY Hamiltonian and apply the paper's Jordan-Wigner
   Majoranas. The thermodynamic-limit ground state is Gaussian.
2. Transcribe the printed Fourier coefficient `g_l` without reading any
   plotted point. Its phase ratio has unit modulus, and midpoint Fourier
   quadrature avoids sampling the isolated gap-closing momenta.
3. Assemble the `2L x 2L` block Toeplitz covariance with block
   `B[j,k] = Pi_(k-j)`. The identity `Pi_l^T = -Pi_-l` makes it exactly
   antisymmetric up to roundoff.
4. Diagonalize the Hermitian matrix `i B_L`. Its positive eigenvalues are the
   `nu_m` in the paper's canonical antisymmetric form.
5. Each mode contributes the binary entropy of `(1+nu_m)/2`; summing the L
   contributions gives `S_L`.

The critical-Ising prose shortcut for `g_l` is not used as an input. Directly
evaluating Eq. (8) at `a=gamma=1` gives
`g_l = -2/[pi(2l+1)]` in the paper's block index. This identity is an
independent quadrature check and also records the apparent indexing or missing-
pi ambiguity in the prose.

### EQ004: scaling checks

The CFT coefficient is `(c+cbar)/6`. With equal left/right charges it gives
`1/6` for Ising (`c=cbar=1/2`) and `1/3` for XX/XXX (`c=cbar=1`). These are
regression checks over generated entropies, not replacements for the numerical
curves. Away from the Ising critical point, the saturation scale follows
`(1/6) log2 |1-a|^-1`; finite-L points near `a=1` are not required to equal the
infinite-half-chain asymptote.

### EQ005: the XXX convention fork

The printed `H_XXZ` has an overall minus sign. At `Delta=1, lambda=0` this is a
ferromagnet with a degenerate maximum-spin ground multiplet; one ground state is
fully polarized and has zero entropy. The caption simultaneously describes a
free-boson critical curve, which is the antiferromagnetic XXX behavior.

The runner therefore computes two explicitly labeled objects:

- the literal printed ferromagnetic convention, including the zero-entropy
  polarized state and the fixed-`S_z=0` symmetric Dicke representative;
- the antiferromagnetic convention selected by the caption's critical physics,
  obtained independently by sparse exact diagonalization in `S_z=0`.

For the literal sign and `Delta>=1`, the two-spin bond eigenvalues are
`-Delta`, `Delta-2`, and `Delta+2`.  Hence every bond is bounded below by
`-Delta`, and a polarized periodic product state saturates all bonds.  At
`Delta=1` the `Delta-2` branch is also degenerate, producing the full symmetric
spin multiplet (including the Dicke representative); for `Delta>1` the common
ground space reduces to the two polarized product states.  This is an exact
ground-space certificate, not a finite-sector numerical guess.

No figure value is used to choose between them. Agreement of the second object
with the stated logarithmic coefficient is evidence about author intent; the
Hamiltonian/caption mismatch remains a formal review discrepancy until a
fresh-context reviewer attempts to falsify it.

### EQ006: majorization

For every Gaussian normal mode, form probabilities `(1+nu_m)/2` and
`(1-nu_m)/2`. Their tensor product gives all `2^L` density eigenvalues. Sort
both spectra, pad the `L` spectrum with zeros to dimension `2^(L+2)`, and test
all partial sums. The reported margin is
`min_k(sum_{i<=k} lambda_L[i] - sum_{i<=k} lambda_{L+2}[i])`; a negative value
beyond tolerance falsifies the printed direction.

### EQ007: complete reduced spectrum

Eq. (20) is evaluated literally by taking the tensor product of every mode's
two probabilities.  For each declared block size the runner checks both that
the resulting `2^L` weights sum to one and that their direct von Neumann
entropy equals the independent binary-mode sum in Eq. (13).  This second path
is important: a normalized spectrum alone would not catch a wrong association
between the covariance modes and density eigenvalues.

### EQ008: noncritical scaling surface

The Fig. 1 caption proposes a scaling variable `x=L|1-a|`, but it does not
publish the function `f(x)` or a tolerance.  The reproduction therefore holds
`x` fixed over four distances from criticality and compares
`S_L-log2(L)/6`.  Only the two closest-to-critical rows enter the declared
asymptotic gate; the wider-distance corrections remain in the output instead
of being hidden by a fitted offset.

### EQ009: RG monotonicity boundary

The c-theorem paragraph states a universal interpretation but supplies no
lattice RG transformation, scale-matching rule, or entropy observable after
coarse graining.  A fixed-L Ising mass-flow sweep is useful as a counterexample
probe, but it is not the missing RG map.  T015 must therefore remain
publication-underspecified even when the proxy is monotone.

### EQ010: effective rank

"Relevant eigenvectors" is not a numerical definition.  We make it explicit
as the smallest sorted-spectrum rank retaining a weight `w` and report three
thresholds.  A gapped Ising point saturates in the finite range while the
critical rank grows.  This supports the DMRG mechanism but cannot prove the
paper's unbounded-`L` quantifier.

The output now reports three different objects instead of conflating them:

- the algebraic dimension `2^L` of the enumerated finite-block spectrum;
- the number of floating-point eigenvalues resolved above an explicit absolute
  tolerance;
- the epsilon-effective rank needed to retain a declared total weight.

Only the third is the reconstructed DMRG proxy. None is silently promoted to
the paper's undefined phrase “relevant eigenvectors.”

### EQ011: Eq. (11) fermion occupation sign

Using the paper's own definition `b=(d_0+i d_1)/2`, canonical Majorana algebra
gives `b^dagger b=(1+i d_0 d_1)/2`. Its normal-form covariance convention is
`<d_0 d_1>=i nu`, hence the labelled occupied probability is `(1-nu)/2`, not
the `(1+nu)/2` printed in Eq. (11). An independent Pauli representation
`d_0=sigma_x`, `d_1=sigma_y` reproduces the same result.

This is a label/sign discrepancy, not an entropy discrepancy: swapping the two
probabilities preserves normalization, binary entropy, and the unordered full
product spectrum. The runner therefore keeps explicit `empty` and `occupied`
labels, tests the identity, and leaves publication adjudication to fresh review.
