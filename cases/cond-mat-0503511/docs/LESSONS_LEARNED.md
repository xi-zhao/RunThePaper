# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: *Dynamics of a Quantum Phase Transition*
- PaperID: cond-mat-0503511
- Final status: science passed; render 4/5 accepted; independent review pending
- Main reproduced targets: Main Figs. 1--3, five numerical targets including all
  insets and series
- Main blockers: T002 publication-capped render fidelity and fresh-context
  scientific review

## What Worked

- The Majorana-covariance representation made the open-chain paper-scale sweep
  practical while preserving exact Gaussian dynamics.
- A direct spin-Hilbert-space test and an independent periodic-mode solver gave
  two qualitatively different checks on the primary implementation.
- Freezing CSV hashes before RenderContract tuning kept visual optimization from
  changing the scientific result.

## What Was Difficult

- The paper mixes `tau_Q W/hbar` with `tau_Q/tau_0`; an early implementation
  plotted the former on an axis labeled as the latter. The render comparison
  exposed the factor-of-two defect, and v4 records a zero conversion error.
- Dense many-body spectra are unusually sensitive to visible-level selection,
  vector strokes, and rasterization even when the underlying gaps are correct.
- A low scientific-region pixel score was useful scientific evidence here: it
  led to the discovery that v4 had included all 1140 three-particle odd curves
  in addition to the declared 0/1/2-particle reconstruction. V5 fixes that
  internal scope and asserts its 191-even/20-odd counts, while retaining an
  explicit cap because the publication never enumerates its plotted level set.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Treat printed axis units as a scientific contract. | A correct array in the wrong normalized unit is still a wrong reproduction. | Add explicit unit-conversion invariants before rendering. |
| Separate dense-spectrum science from dense-spectrum rendering. | Pixel mismatch can otherwise be misdiagnosed as a Hamiltonian error. | Validate eigenvalue/gap invariants first, then compare branch masks and rasterizers. |
| Freeze arrays before visual tuning. | It prevents style work from becoming implicit curve fitting. | Record config, implementation, data, and figure hashes in every RenderContract. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Dimensionless-unit ambiguity | Fig. 2(b) initially used `tau_Q W/hbar` under a `tau_Q/tau_0` label. | Derive every plotted unit in the formula cards and assert conversions numerically. |
| Pixel score interpreted as physics score | T002 physics passed while render remained 78.76, but the earlier visual discrepancy still exposed a real selection defect. | Treat pixel mismatch as a diagnostic trigger, then distinguish code, science, publication metadata, and rendering with independent checks. |
| Unbounded low-spectrum enumeration | V4 included a complete three-particle sector outside the declared reconstruction. | Declare and test particle-sector/curve-count scope before rendering dense spectra, and do not call it paper exact unless the publication enumerates it. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Direct small-system Hilbert-space parity | Gaussian/free-fermion solvers | Unit tests agree with direct spin evolution. |
| Independent asymptotic solver | Thermodynamic scaling claims | Periodic momentum modes reproduce the open-chain kink trend. |
| Scientific-region pixel contract | Multi-panel figures | Four regions pass; T002 is isolated rather than averaged away. |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Axis-normalization defect | T003, pre-v4 | Assert both raw and plotted dimensionless units. |
| Dense-branch target-scope defect | T002, pre-v5 | Assert exact sector identities and expected combinatorial curve counts. |
| Residual dense-branch render mismatch | T002, v5 | Compare axis box and line density over frozen data, then classify an unpublished curve-selection rule as a publication boundary rather than copying source geometry. |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| Unit-conversion gate | Catches scientifically wrong labels even when trends look right. | Formula/target contract checker. |
| Frozen-data RenderContract hash check | Enforces the no-pixel-theft boundary. | Harness render acceptance. |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Majorana covariance evolution | 186 final v5 paper-scale jobs completed in 612.87 s locally. | Keep model case-local; promote checkpoint and isolation pattern. |
| Periodic mode cross-check | Independent thermodynamic observable at low cost. | Promote as a reference pattern for integrable-chain cases. |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`PRAgent-workflow/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P1 | Require explicit plotted-unit assertions. | v3-to-v4 factor-of-two correction in T003. | candidate |
| P1 | Require explicit low-spectrum sector/curve-count contracts. | T002 v4 contained 1140 unintended three-particle branches; v5's declared 191/20 check prevents recurrence. | candidate |
| P2 | Separate plot sampling from unpublished branch selection. | T002 matches the axis box and EPS sampling density, but the caption never enumerates the level subset/cutoff. | candidate |

## Prompt Or Workflow Changes

- Before any render comparison, require a table mapping each CSV column to the
  exact axis label and dimensionless normalization printed in the paper.
- A low pixel score must trigger separate scientific-code checks and render
  ablation; it must never be repaired by changing physical arrays.
