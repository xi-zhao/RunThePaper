# Lessons Learned

## Main lesson

High pixel agreement can be scientifically circular. In this case, a source-derived -5 ns shift raised the S20 matrix match from 79.35% to 99.53%. Because the shift was inferred from the target image and changed scientific snapshot selection, it cannot support an independent reproduction.

## What remains valid

- Fixed-particle-number bases reduce the exact problem to dimensions 11, 78, and 66.
- One Hamiltonian model produces all density, entropy, concurrence, correlation, and occupancy observables.
- Conservation laws, analytic limits, clean-disorder equivalence, fidelity bounds, and Lindblad invariants provide cross-target checks.
- S9-S10 are inexpensive 50-realization simulations fully specified up to a source-independent representative seed.
- S11 can be reconstructed at method level, but exact point matching is blocked by unpublished realization details.

## General rules

| Rule | Reason |
| --- | --- |
| Inventory every panel before scoring | Combined targets hide missing subplots and inflate apparent coverage |
| Freeze arrays before reading source pixels | Prevents visual comparison from changing the physics |
| Treat coordinate/time fitting as a hypothesis | A global fit may diagnose publication metadata, but cannot become an input without independent textual support |
| Keep experimental measurements outside the theory denominator | They require hardware or author records, not a numerical runner |
| Separate coverage, fidelity, evidence level, and pixel state | Each answers a different question and prevents overclaiming |
| Diagnose direct cause, root cause, and code responsibility separately | “Not complete” is not an actionable explanation |

## Open scientific question

Twelve S20 source matrices are jointly consistent with a common -5 ns offset, but the article does not state that offset. Current root cause is `unresolved`, not “paper error.” A fresh-context reviewer must independently re-derive the time convention and attempt to falsify both publication-underspecification and implementation-defect hypotheses.

## New Failure Modes

- Circular image evidence: a source-derived coordinate transform changes the scientific array being evaluated.
- Combined-target masking: one score hides weak or missing subpanels.
- Historical backend evidence drift: a valid old parity run is incorrectly treated as attestation for current outputs.

## Reusable Checks Or Tools

- Panel-level coverage validator and one-item/one-target contract.
- Raw/reference-denying isolated numerical runner with access log and hashes.
- Post-run source-alignment diagnostic with an explicit `used_to_select_scientific_times=false` invariant.
- Direct/root-cause and code-responsibility schema with a falsifying next test.
