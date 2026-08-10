# Numerical Methods

## Independent exact chain

The local basis is `n=0,...,2s`; periodic words with adjacent nonzero entries
are rejected. For every allowed site, the sparse Hamiltonian applies

\[
\langle n+1|S^x|n\rangle=\tfrac12\sqrt{(2s-n)(n+1)}.
\]

Two-site-translation orbits are normalized and used for quench dynamics. The
momentum-zero, inversion-even block is built from dihedral orbits for the gap
ratio. Sparse Krylov propagation produces state vectors; magnetization is a
diagonal orbit observable. Entropy is evaluated only after expanding orbit
amplitudes and tracing equal environment configurations.

## Paper-scale Fig. 2 finite-MPS/tDMRG path

Pairing sites gives the exact local basis `|00>,|01>,|10>`. If `X_L/X_R`
flip the left/right spin only within this basis and `P_L/P_R` project the
corresponding physical spin to zero, the two-block term is

\[
h_{j,j+1}=X_{R,j}P_{L,j+1}+P_{R,j}X_{L,j+1}.
\]

The periodic sum contains every projected physical spin flip once. Restricted
to the invariant globally constrained subspace, the 15-block operator is
exactly the paper's L=30 ring. A symmetric product formula over disjoint
periodic bond colours evolves an open-storage MPS; the
ring-closing gate is applied by controlled swaps and the physical order is
restored after every gate. Checkpoints contain the full MPS, observable prefix,
config digest, norm history, energy diagnostics, and the total probability of
forbidden adjacent excitations. The latter detects constrained-subspace
leakage from generic MPS truncation even when the norm remains close to one.

Six deterministic lanes cover the all-zero and Z2 states at primary
`chi=512, dt=0.025`, halved-time-step, and enlarged-bond `chi=768` settings.
The paper does not report these numerical controls, so the two refinements are
part of acceptance rather than claims about the author calculation. The
paper-scale campaign has not been run; only L=8 smoke and small dense
equivalence tests have been executed.

## Independent TDVP/MPS residual

For every constrained product configuration, the bond-dimension-two MPS
amplitude and both collective derivatives are evaluated analytically. The
finite-ring state is normalized explicitly. The residual

\[
\gamma=L^{-1/2}\|iH\psi+\dot\theta_e\partial_e\psi+
\dot\theta_o\partial_o\psi\|
\]

is therefore calculated from a matrix Hamiltonian and state vectors, not from
the paper heat-map colours. Ring lengths `L=12,8,6` for `s=1/2,1,2` reproduce
the printed orbit leakages `0.17,0.32,0.41` as
`0.17464,0.31830,0.41232`.

For the deformed model, the matrix Hamiltonian is projected back to the two
MPS tangents as an independent check. Its velocities agree with the printed
supplemental flow within `3.9e-4` at `L=12`. Fig. S2 residuals then converge
from rings `L=10,12,14` within `1.4e-7`.

## Generated scale

| Observable | Paper | Generated | Match |
| --- | --- | --- | --- |
| Fig. 1(b) dynamics | L=30,32 | L=18,20 | reduced_scale |
| Fig. 2(a) sector spectra | undisclosed size list, d up to about 2e4 | s=1/2 L=14..20; s=1 L=10..16; s=2 L=8..12 | reduced_scale |
| Fig. 2(b,c) entropy | periodic L=30, t<=100/120 | L=18 executed; L=30 tDMRG code-ready but not run | reduced_scale evidence / paper-scale implementation ready |
| Fig. 4(b) spin-1 dynamics | L=20,22 | L=12,14 | reduced_scale |
| Fig. 4(d) spin-2 dynamics | L=14,16 | L=10,12 | reduced_scale |
| TDVP flow parameters | printed spins/h values | same | paper formula exact; residual finite-ring |
| Fig. S2 h grid | 0..0.08 | same plus printed 0.045 point | grid exact; residual procedure `unknown` |

All runs are deterministic; no random seed is used.

## Protocol-v2 paper-review attribution

Every stable numerical difference is first assigned to one of:

1. `reproduction_defect`;
2. `parameter_ambiguity`;
3. `insufficient_compute`;
4. `inconclusive`.

`paper_error_candidate` is a separate escalation that requires all of
`paper_exact`, convergence, at least two independent cross-checks, source
pinpoint, and fresh independent review. The omitted Fig. 2 tensor-network
controls and the Supplement Fig. S2 residual procedure therefore remain
parameter/compute boundaries, not automatic evidence of an error in the paper.
