# Paper review protocol v2 — Table II

## Current classification

T004 has a strong paper-error hypothesis, but the authoritative classification
for the new atomic scope is review-pending. It is not a confirmed erratum. The
29-target whole-paper package requires a fresh inventory-first review before
lifecycle closure.

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

The prior reviewer independently reproduced the late-value discrepancy and
rejected a reproduction-code explanation. However, the authors' original
numerical implementation is not public, so the result remains a candidate
rather than a confirmed journal error. The prior review also showed that broad
figure-oriented targets were too coarse. The repaired package now maps all 26
numeric paper items to 29 atomic targets and must be reviewed again from a new
paper-only inventory; prior classifications cannot be transplanted.
