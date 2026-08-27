# Paper Map

## Paper

- PaperID: `2103.03074`
- Title: *Simulating the Sycamore quantum supremacy circuits*
- Authors: Feng Pan, Pan Zhang
- Source: arXiv v1, submitted 2021-03-04
- Formal publication: *Simulation of Quantum Circuits Using the Big-Batch Tensor Network Method*, Phys. Rev. Lett. 128, 030501 (2022)
- Publication DOI: `10.1103/PhysRevLett.128.030501`

## Raw Materials

- `raw/paper.pdf`: arXiv PDF used as the canonical paper for this case.
- `paper-source/source.tar`: arXiv TeX source.
- `paper-source/extracted/main.tex`: source used for figure and formula extraction.
- `raw/prl-final-paper.pdf`: final PRL PDF supplied by the user, kept for cross-checking.

## Main Idea

The paper studies how to compute many correlated output bitstring probabilities of a quantum circuit in one run. It fixes part of the final bitstring, enumerates the remaining part, and reuses the expensive "head" contraction across the whole batch. This gives a large set of probabilities from the same subspace.

The core numerical claims are:

- a batch of `2^21` correlated bitstrings for a 53-qubit, 20-cycle Sycamore circuit;
- a Porter-Thomas-like distribution of scaled probabilities `Np`;
- post-selection of high-probability bitstrings increases XEB;
- conditional probabilities inside the fixed subspace also follow Porter-Thomas behavior;
- the head contraction dominates the total computational cost.

## Section Map

| Section | Role in reproduction |
| --- | --- |
| Introduction | Defines the simulation problem, XEB motivation, and comparison with full statevector and tensor-network methods. |
| Big-head simulation of quantum circuits | Defines the split into closed bits `s1`, open bits `s2`, head/tail networks, bottleneck, and amplitude reuse. |
| Simulation of the Sycamore circuits | Gives the 53-qubit experiment setup, open qubits, slicing, complexity tables, Fig. 2, and XEB post-selection curve. |
| Appendix: contraction algorithm | Gives hierarchical partitioning, bipartition complexity, dynamic slicing, and GPU efficiency. |
| Appendix: simulation details | Gives open qubit IDs for 20-cycle and 14-cycle cases, Fig. 5, and conditional probability Fig. 6. |

## Reproduction Scope

This case reproduces the numerical features of the paper on a local small-scale circuit:

- fixed closed bitstring plus enumerated open bitstrings;
- batch probability extraction;
- Porter-Thomas histogram of `Np`;
- post-selected XEB curve;
- conditional probability histogram;
- table-level complexity consistency checks.

It does not rerun the original 53-qubit, 60-GPU tensor-network contraction. That would require the original large contraction order, slicing plan, circuit files, and a multi-GPU cluster. The case records this as a scale limitation, not as a formula or implementation failure.
