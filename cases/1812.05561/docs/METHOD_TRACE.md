# Method Trace

## MTH001 — constrained basis and sparse Hamiltonian

Enumerate blockade-allowed bit strings directly.  For every flippable site,
assemble the main Eqs. (1)-(3) matrix element from independently evaluated
z-spins.  Shared sparsity allows different coupling families without rebuilding
connectivity.  Checks: basis constraint, Hermiticity, small-chain tests.

## MTH002 — dynamics and entanglement

Use Krylov `expm_multiply` on the sparse Hamiltonian.  Fidelity comes from the
Néel component.  Half-chain Schmidt values come from an explicitly assembled
coefficient matrix; no tensor-network or author data is used.

The paper-scale path processes bounded time chunks, hashes its config, and
checkpoints the current state plus completed observables.  Long-time scaling
uses a refined local-maximum search around each revival rather than assuming
the analytic period is the numerical maximum.

## MTH003 — symmetry-resolved spectra

Construct translation-orbit vectors at momentum 0/pi and project bond-centred
inversion parity.  At paper scale, retain the projected operator sparsely until
a declared high-memory preflight permits the full real dense eigensystem.
Compute spectral overlaps, unfolded spacings and adjacent-gap ratios inside a
single sector.  For the two central scars only, use residual-checked
shift-invert rather than an unnecessary full spectrum.

## MTH004 — forward-scattering diagnostics

Orient allowed flips by Hamming distance from the Néel state to obtain H+.
Recursively normalize H+|k>, evaluate beta, and apply
H-z=[H+,H-] to measure means and variances.

The N=32 implementation keeps one Hamming layer in memory.  Because different
FSA layers have disjoint Hamming distance, this is algebraically equivalent to
the reduced dense layer matrix and is verified against it in tests.

## MTH005 — supplementary optimization and scaling

Optimize the four printed cost functions independently with checkpointed
Nelder-Mead.  For N=60, compile the open-chain Pauli strings into a compressed
finite-state MPO and use two-site DMRG; the first excited state is isolated with
a projector penalty and orthogonality acceptance.  Long-time rates and turning
points are derived from generated locally maximized fidelities at the paper's
two fit windows.

## MTH006 — toy-model Pauli expansion

Draw a new disclosed Gaussian coupling tensor.  Expand Eq. (7) into Pauli
strings sparsely, diagonalize the generated Hermitian matrix, and compute
overlaps, Loschmidt echo and half-chain entropies in chunks.  The paper-scale
lane repeats N=14 for three disclosed seeds and accepts invariant statements,
not author-realization point coordinates.

## MTH007 — execution, recovery and attribution

The paper-scale campaign has 59 deterministic work units.  Completed units are
reused only under the same full-config digest; iterative states are checkpointed
inside T001/T003/T004/T005/T006/T009.  The unsharded resume call merges units
and evaluates all target acceptance.  Stable differences enter the ordered
four-way audit and are never attributed to the paper/source by default.
