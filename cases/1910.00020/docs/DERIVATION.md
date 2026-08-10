# Derivation

## 1. Why a phase-free stabilizer tableau is sufficient

Each trajectory contains Clifford gates and projective Z measurements. A pure stabilizer state is represented by n independent commuting Pauli generators in a binary matrix

$$
G=[X\mid Z]\in\mathbb{F}_2^{n\times 2n}.
$$

Pauli signs determine which measurement outcome occurred but do not change generator support. All observables in this paper are entropies or mutual informations, which depend only on that support. Therefore phases can be omitted exactly; this is not an approximation to the reported observables.

A uniformly random two-qubit Clifford is sampled by enumerating all 720 elements of `Sp(4,2)`, the Clifford group modulo Pauli phases. H, S, and both CNOT directions generate this group. Applying one element is a four-column GF(2) matrix multiplication on `[x_a,x_b,z_a,z_b]`.

## 2. Measurement update

A Z measurement anticommutes with every generator whose `x_q=1`. If none exists, the outcome is already fixed and the support is unchanged. Otherwise choose one anticommuting pivot, multiply it into all other anticommuting rows, and replace the pivot by `Z_q`. This leaves n independent commuting generators for the conditional post-measurement pure state.

## 3. Entropy and mutual information

For subsystem A of a pure n-qubit stabilizer state,

$$
S(A)=\operatorname{rank}_{\mathbb F_2}(G_A)-|A|.
$$

For a single reference this is exactly 0 or 1 bit per trajectory, so the circuit average is a survival probability. For two references,

$$
I(R_1:R_2)=S(R_1)+S(R_2)-S(R_1R_2).
$$

The implementation checks a Bell pair (`S(R)=1`) and its purification after measuring the system partner (`S(R)=0`). It also verifies tableau rank and commutation after a random circuit.

## 4. Circuit protocols

- T001 creates a Bell pair, encodes for `2L` layers at p=0, then evolves for `2L` layers at rate p.
- T002 inserts one local Bell reference into a product state and records the exact entropy decrease caused by every subsequent measurement event.
- T004 inserts the reference at the initial-time surface and measures survival at `t=2L`.
- T005/T006 insert two references at the printed sites, use periodic/open boundaries, and evaluate their mutual information versus `(t-t0)/L`.
- T007 first prepares the two volume-law initial states for `t0=4L`, locally resets one system site, and inserts a fresh Bell reference.
- T008 inserts one or four Bell references over a contiguous region and evaluates their total reference entropy at `p=0.1596`.

## 5. Scaling relations

T001 uses the paper's `p_c=0.1598` and `nu=1.30` to form the scaling coordinate

$$
u=(p-p_c)L^{1/\nu}.
$$

T004 independently fits the largest reduced system to `S_Q ~ (p_c-p)^beta_s`. T005/T006 multiply the raw mutual information by the printed powers of L. T008 fits the early-time slope of `S ~ t^(-eta_parallel/2)` before the finite-size turnover.

## 6. Exact incomplete-record channel for Fig. 2(b)

The paper fixes the physical circuit and changes only which measurement outcomes are retained. Therefore a measurement outside the retained spatial window must still occur; only its outcome is marginalized. For an unrecorded Z measurement this is the dephasing channel

$$
\mathcal D_Z(\rho)=\frac{\rho+Z\rho Z}{2}.
$$

In a mixed stabilizer representation, a recorded measurement conditions the state and replaces or adds the measured stabilizer. An unrecorded measurement removes one anticommuting generator instead. For a rank-$r$ stabilizer group with binary generator matrix $G$, the reference entropy is

$$
S(R\mid M_A)=|R|-\dim S_R,
\qquad
\dim S_R=r-\operatorname{rank}_{\mathbb F_2}(G_Q),
$$

where $S_R$ is the subgroup supported only on the reference and $G_Q$ is the restriction to system qubits. A Bell-pair test distinguishes the two channels exactly: an unrecorded system measurement leaves `S(R)=1`, while a recorded outcome gives `S(R)=0`. The full-record mixed implementation also agrees trajectory-by-trajectory with the pure stabilizer implementation.

The previous implementation omitted out-of-window measurements and therefore simulated a different physical circuit. That was a reproduction defect, not evidence against the paper. T003 now uses the exact conditional channel; its remaining limitation is reduced size and unpublished Monte Carlo sampling metadata.
