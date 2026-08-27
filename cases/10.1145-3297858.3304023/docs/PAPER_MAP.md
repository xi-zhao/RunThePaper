# Paper Map

## Paper

- Title: Tackling the Qubit Mapping Problem for NISQ-Era Quantum Devices
- Authors: Gushu Li, Yufei Ding, Yuan Xie
- Formal publication: ASPLOS '19, pp. 1001–1014
- Publication DOI: `10.1145/3297858.3304023`
- Public source used for reproduction: arXiv `1809.02573`

The ACM PDF endpoint returned a 403 response in this environment, so the pilot
uses the arXiv PDF and TeX source. The GitHub implementation is intentionally
not used.

## Reproduction Scope

This is an algorithm/systems paper rather than a formula-to-plot physics paper.
The reproducible object is SABRE:

```text
input circuit + coupling graph
-> logical-to-physical initial mapping
-> inserted SWAP sequence
-> hardware-compliant circuit
-> additional-gate count, depth, runtime, trade-off curves
```

The core algorithm must be reconstructed from the paper text:

- DAG/front-layer construction;
- candidate SWAP generation from front-layer qubits;
- nearest-neighbor cost;
- look-ahead extended set;
- reverse traversal for initial mapping;
- decay penalty for gate-count/depth trade-off.

## Key Paper Artifacts

- Main TeX: `paper-source/Partition.tex`
- PDF: `raw/paper.pdf`
- Main algorithm pseudocode: Algorithm 1 in Section IV-B
- Main result table: Table II
- Main numerical plot: Fig. 8, trade-off between normalized gate count and
  normalized depth

## First-Pass Reproduction Strategy

Full reproduction of Table II requires the exact benchmark suite and baseline
BKA setup. This first pass does not use any GitHub code and starts with
rebuilding SABRE from the paper, then validating the core claims on:

- the paper's 4-qubit SWAP example;
- synthetic Ising-style nearest-neighbor circuits;
- QFT circuits generated locally from Qiskit and decomposed only to extract
  two-qubit dependencies;
- decay sweeps to verify the gate-count/depth trade-off.
