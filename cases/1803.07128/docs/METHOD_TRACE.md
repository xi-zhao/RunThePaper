# Method Trace

## MTH_ANALYTIC — squeezing kernel

- Inputs: phase vectors and printed `c` values.
- Algorithm: evaluate Eq. (8), take the paper-prescribed absolute square, tensor over dimensions.
- Validation: independent Fock-series sum, diagonal normalization, PSD Gram matrix, monotonic width.
- Status: verified and paper-exact for T001.

## MTH_CLASSIFIERS — implicit SVC and explicit Fock perceptron

- SVC: scikit-learn SVC receives only the formula-derived callable kernel.
- Perceptron: scikit-learn Perceptron receives independently expanded real Fock coordinates.
- Missing metadata: all reconstructed dataset choices are frozen in `config/paper_exact.json` and prevent paper-exact claims.
- Status: scientific behavior verified, parameters reconstructed.

## MTH_VARIATIONAL — finite-Fock CV circuit

- Inputs: independent moons data and printed 4-block circuit.
- Gates: dense finite-Fock exponentials of BS, D, P and V generators.
- Optimizer: Adam, 5000 minibatches of 5, gentle L2; the paper does not identify its adaptive optimizer or coefficient.
- Output: normalized probabilities for `|2,0>` and `|0,2>`.
- Status: reduced-scale scientific reproduction.

Paper-scale extension: `variational_scale.py` evaluates the same gates with exact
fixed-total-photon beam-splitter sectors and tensor-factorized local gates. A separate
dense Kronecker implementation cross-checks the optimized path at small cutoff. The
21-condition cutoff/seed campaign checkpoints every 50 steps and never interprets a
mismatch as a paper error while the author's training contract is missing.

## MTH_RENDER — post-freeze comparison

The renderer reads frozen NPZ files. Only after their SHA-256 manifest exists may a separate script copy the four source panels. The render contract forbids changes to physical parameters, arrays, labels, seeds, author code or source coordinates.
