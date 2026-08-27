# Method Trace

## Method Summary

The paper's method starts from a quantum circuit tensor network. A final bitstring `s` is split into two parts:

```text
s = (s1, s2)
```

- `s1`: closed bits. These are fixed.
- `s2`: open bits. These are enumerated as a batch.

The tensor network is partitioned into a head network and a tail network:

```text
G_head -- bottleneck C -- G_tail
```

After contraction, the expensive part produces a reusable vector:

```text
v_head(s1)
```

For each open bitstring, the tail gives:

```text
v_tail(s2)
```

The amplitude is the final inner product:

```text
psi(s1, s2) = v_head(s1) dot v_tail(s2)
```

The key saving is that `v_head(s1)` is computed once, then reused for all `2^n2` open bitstrings.

## Implementation Used In This Case

The local implementation in `src/big_batch_feature_sim.py` uses a small random quantum circuit rather than the original 53-qubit Sycamore circuit.

It keeps the same mathematical structure:

1. Build a circuit statevector.
2. Split final qubits into closed and open groups.
3. Fix one representative closed bitstring.
4. Enumerate all open bitstrings in one batch.
5. Compute probabilities, scaled probabilities `Np`, XEB, and conditional probabilities.
6. Check that direct amplitude lookup and batch extraction agree exactly.

This gives a faithful local test of the paper's probability logic, even though it does not reproduce the original multi-GPU contraction workload.

## Algorithm Steps

```text
Input:
  n qubits
  circuit depth
  closed qubits
  open qubits

Procedure:
  1. Generate a random layered circuit.
  2. Simulate the statevector.
  3. Choose a closed bitstring whose marginal probability is close to its expected value.
  4. Slice the state tensor at the closed bitstring.
  5. Flatten the remaining open axes to obtain all open-bitstring amplitudes.
  6. Convert amplitudes to probabilities.
  7. Generate histograms, post-selection curves, conditional distributions, and check files.

Output:
  probabilities for all open bitstrings
  post-selection XEB curve
  conditional probabilities
  feature checks
```

## Scale Difference

| Item | Paper | Local case |
| --- | --- | --- |
| Circuit | Sycamore 53 qubits | Random 18-qubit circuit |
| Open bitstrings | `2^21` or `2^19` | `2^12 = 4096` |
| Backend | Tensor-network contraction on GPUs | Dense statevector simulation on CPU |
| Goal | Exact large-scale contraction | Feature-level reproduction and formula validation |

The local case is intentionally smaller. It is meant to verify the derivation and numerical behavior before attempting a hardware-scale contraction.

## Superseding author baseline: v6 exact-public-circuit and formal-PRL closure

The author closure now freezes the official Dryad v11 seed-0 ABCDCDAB QSIM
files for 20 and 14 cycles.  A strict independent parser implements public
qsim gate conventions, verifies representative gate unitarity, builds both
53-qubit tensor networks, and performs value-preserving ADCRS simplification.
The fixed-output networks contain 381 and 246 tensors respectively, matching
the printed structural counts without using author code or arrays.

For each fixed-subspace batch the runner performs a bounded cotengra path
search and symbolic slicing to the declared `2^30` element target.  It never
starts a contraction whose measured path estimate exceeds the local budget.
The same isolated run executes a three-size official-gate complex64/complex128
sweep, a four-amplitude shared-head check, exact marginal/XEB and memory-unit
rederivations, paper-value arithmetic, a local complex64 GEMM benchmark, and
all 17 target evidence writers. T014-T017 reuse one generic reduced official-
circuit path that streams every generated amplitude through a per-batch ledger
and rolling hash, checks normalization, builds a fixed Porter-Thomas histogram
and KS statistic, evaluates a seeded sample-correlation/XEB diagnostic, and
emits 43/50-qubit resource contracts. Paper scale is guarded rather than
pretended: 43 qubits imply 16,384 batches and a 64-TiB logical stream; 50
qubits imply 4,194,304 batches and an 8-PiB logical stream.

The runner reads public QSIM circuit
definitions, never author code, author result arrays, or source pixels. The
attestation is
`outputs/runs/2103.03074-scientific-closure-v6-20260825/run_attestation.json`.
