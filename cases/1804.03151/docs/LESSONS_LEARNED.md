# Lessons Learned

## Case summary

- Paper: *Hubbard model physics in transition metal dichalcogenide moire bands*
- Paper ID: `1804.03151`
- State: partial; twelve formula-derived targets pass, one DFT target is blocked
- Primary blocker: under-specified Quantum ESPRESSO inputs, not insufficient compute

## What worked

- One small continuum core generated twelve distinct scientific observables.
- Complete hexagonal reciprocal shells preserved symmetry and converged rapidly.
- A linear triangular-shell fit avoided unstable nonlinear optimization.
- FFT projection made the Bloch-Wannier Coulomb sweep practical on CPU.
- Numerical isolation and post-freeze rendering enforced the source-access boundary.

## Generalized lessons

| Lesson | Why it matters | Future rule |
| --- | --- | --- |
| Classify at subpanel granularity | Mixed figures otherwise hide schematics or blockers | inventory every numerical subpanel before running |
| Separate missing metadata from compute limits | More hardware cannot repair an under-specified DFT calculation | use `missing_benchmark_metadata`, not `insufficient_compute` |
| Preserve lattice symmetry in truncation | rectangular cutoffs can create false anisotropy | use complete symmetry shells |
| Freeze arrays before visual tuning | allows pixel optimization without contaminating science | hash data, then open source figures |
| Report foreground and canvas metrics separately | sparse curves make literal foreground metrics harsh | foreground is primary; canvas is layout-only |

## New Failure Modes

| Pitfall | Manifestation | Prevention |
| --- | --- | --- |
| Treating fitted potential as DFT reproduction | Fig. 1(d) could incorrectly cover Fig. 1(c) | keep D001 separate and blocked |
| Replacing Wannier projection with a Gaussian | interaction curves may look plausible but lose the paper's Bloch content | use the independently computed Bloch density for target arrays |
| Letting source images influence numerics | pixel fitting could silently change physics | isolated runner forbids raw/reference paths |
| Reading high full-canvas scores as science | white background dominates | make scientific foreground the primary score |

## Reusable Checks Or Tools

| Candidate | Value | Destination |
| --- | --- | --- |
| complete hexagonal shell enumeration | reusable for triangular/moire plane-wave models | future case-local utility first; promote after a second independent use |
| frozen-manifest render guard | prevents post-hoc numerical edits | already represented by harness isolation/render contracts |

No new harness patch is proposed from this case. The existing isolation, coverage,
formula, pixel and fresh-review gates were sufficient once the case evidence was wired
to them correctly.
