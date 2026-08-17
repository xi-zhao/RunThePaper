# Paper review protocol v2 — Table II

## Current classification

`inconclusive_pending_fresh_review`; `paper_error_candidate_emitted=false`.

## Printed claim

Table II labels its second column as the exact ground-state energy for \(N=1+\epsilon\), with seven epsilon values from `0.1` to `1e-7`.

## Independent result

Riccati shooting and a separate finite-difference Hamiltonian agree closely across all seven values. The first four paper entries agree at the declared precision. The last three do not, with an increasing gap recorded in `outputs/checks/science_checks.json#table_ii_paper_discrepancies`.

## Falsification already attempted

- exact paper epsilon grid and Hamiltonian audited;
- shooting boundary 40 versus 30;
- independent finite-difference solver on a different numerical object;
- direct Eq. (11) root evaluation;
- N=2 and massive N=1 analytic limits;
- focused unit tests and isolated execution with no source/reference reads.

## What remains deliberately unresolved

The reproducer cannot serve as its own fresh reviewer. The review must start from a paper-only inventory, then receive only the restricted falsification bundle. It must attempt to reproduce the printed late values without using author code, author arrays or source-pixel digitization and must classify every target under the protocol-v2 taxonomy.
