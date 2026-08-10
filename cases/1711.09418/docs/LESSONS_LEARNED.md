# Lessons Learned

## Case Summary

- Paper: *Symmetry-Resolved Entanglement in Many-Body Systems*.
- PaperID: `1711.09418`.
- Current state: `review_pending` after complete numerical reproduction.
- Reproduced targets: Main Figs. 2 and 3.
- Blocker: fresh-context independent scientific review only.

## What Worked

- One free-fermion correlation spectrum supported both numerical figures.
- Exact charge-polynomial recurrences avoided Fourier-grid error in Fig. 2.
- Complete vectorized `2^24` enumeration avoided sampling uncertainty in Fig. 3.
- The isolated runner proved that source figures did not feed the numerics.
- Rendering after hash freeze achieved high scientific-region pixel similarity
  without changing parameters or arrays.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| A paper figure can appear to disagree with its own equations | Blind visual imitation can conceal a scientific ambiguity | Resolve series identity from formulas and invariants before RenderContract work, then keep the discrepancy inconclusive until independent review. |
| Legends must not enter the primary science score | An annotation conflict can make a formula-derived output look visually worse | Predeclare curve-only regions and report label discrepancies separately. |
| Exact combinatorics can beat stochastic simulation at modest mode count | It removes sampling noise and simplifies verification | Estimate state-count first; enumerate when `2^m` is tractable. |
| One authoritative numerical core should feed all targets | Shared physics becomes testable once | Build target-specific views over shared domain objects. |

## Pitfalls And Detection

| Pitfall | Appearance in this case | Detection |
| --- | --- | --- |
| Treating printed legend values as ground truth | Initial v1 used sectors 0,1,2,3,5,6 | Compare predicted charge onsets from Eq. (9) with every displayed branch. |
| Using all 10,000 correlation modes directly | Dense full diagonalization would be wasteful | Verify saturation and retain only central nontrivial modes. |
| Optimizing pixels before freezing data | Could leak source geometry into numerics | Require isolated run attestation and frozen output hashes first. |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Printed legend and formula-derived branch sequence disagree | Main Fig. 3 prints final labels 5 and 6 while formula-derived onsets support sectors 4 and 5 | Cross-check every series identity, preserve both claims, and require protocol-v2 review before assigning fault. |
| Pixel optimization rewards copying a disputed annotation | Matching the source legend would increase text-pixel agreement | Exclude annotations from the primary scientific region and record label conflicts as inconclusive findings. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Destination |
| --- | --- | --- |
| Series-identity audit | Detects legend/curve mismatches | case-local now; future Harness backlog candidate |
| Frozen-data RenderContract | Separates scientific and presentation optimization | existing Harness policy |
| Charge normalization and entropy-sum invariants | Strong independent falsification checks | case-local physics tests |

## Harness Backlog Item

Add a generic rule requiring explicit reconciliation when figure labels,
captions, equations, and independent curve identities disagree. Such a conflict
must never be silently resolved in favor of higher pixel similarity.
