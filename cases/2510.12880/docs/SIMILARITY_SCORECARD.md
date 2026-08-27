# Similarity Scorecard

## Two Different Questions

| Metric | Value | Meaning |
| --- | ---: | --- |
| historical similarity score | `95/100` | quality of the two already-generated Main Fig. 5 panels |
| whole-paper coverage | `44.44%` | 4 of 9 independently adjudicable scientific items are covered |
| covered-item fidelity | `92.03/100` | mean scientific fidelity of V001, V002, T001, and T002 |
| reproduction degree | `40.90/100` | mean item fidelity with each uncovered item contributing zero |

The historical score is preserved for backward compatibility and is not a
whole-paper completion claim.

## Covered Items

| Target | Feature + numeric basis | Limiting evidence cap | Item fidelity |
| --- | --- | ---: | ---: |
| V001 | exact projector and `2^N+1` periodic nullity at N=4,6 | 89, paper subset | 89 |
| V002 | periodic product energies, multiplicities, and mirror symmetry | 90, analytic reference | 90 |
| T001 | all Fig. 5(a) branches; 24/25 strict marker matches | 95, digitized curve | 94.12 |
| T002 | all Fig. 5(b) branches and N-fold one-flip degeneracy | 95, digitized curve | 95 |

## Uncovered Items

V003-V007 each receive item fidelity zero because no independently generated
or analytic-reference artifact currently exists. They are excluded from the
legacy two-panel weighted score, but not from whole-paper coverage or degree.
The exact items and diagnoses are in `TARGET_LEDGER.md`.

## Visual Boundary

Pixel or digitized-curve evidence is diagnostic of presentation fidelity. It
does not create scientific coverage, and source pixels never enter the
Hamiltonian, MPS, parameter arrays, or generated data.

Machine-readable records:

- `outputs/checks/similarity_scorecard.json`
- `outputs/checks/authoritative_reproduction_state.json`
