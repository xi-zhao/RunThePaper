# Lessons Learned

Use this file after each reproduction pass. The goal is to extract reusable
lessons from one paper and turn them into better Agent and harness behavior for
the next paper.

## Case Summary

- Paper: Plaquette hardware-aware FTQC design platform
- PaperID: `2607.08767`
- Final status: partial proxy; feature not accepted
- Main reproduced targets: Eq. (9), Eq. (10), Fig. 5(a) Clifford value and gap direction
- Main blockers: unpublished circuit-location, frame, and decoder conventions

## What Worked

- Formula-first reconstruction isolated the Pauli branch cleanly.
- Fixed paper shot counts and a fixed seed made the smoke result auditable.
- Refusing to tune the proxy preserved the missing-method signal.

## What Was Difficult

- The phrase "at the start of each round" does not uniquely determine which
  Plaquette circuit locations receive the channel.
- Matching the stochastic branch does not prove that the coherent circuit is equivalent.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Treat generated-circuit semantics as an input artifact | Hardware-aware papers may publish channels but omit their circuit binding | Require a circuit-location contract before exact claims |
| Compare approximation branches separately | One branch can match while the central branch fails | Store per-backend verdicts instead of one batch score |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Tuning a proxy to a plotted number | The coherent result differed by 0.5182 | Freeze paper parameters and attribute the first mismatch before changing assumptions |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Run the cheapest branch pair first | Proprietary software or missing data | 1.3 seconds isolated the blocker without a large simulation |

## New Failure Modes

| Failure mode | Where it appeared | How future runs should detect it |
| --- | --- | --- |
| Approximation branch matches while exact branch fails | Fig. 5(a) | Require per-branch checks and a shared circuit-location manifest |
| Generic state adapter routes into a domain-specific stage | Agent loop after F5A verdict | Validate stage-domain compatibility before confirming an auto-runnable stage |

## Reusable Checks Or Tools

| Candidate | Why it is reusable | Suggested destination |
| --- | --- | --- |
| circuit-location contract checker | Separates channel formulas from where channels act | future harness backlog after a second case confirms reuse |

## Efficient Reproduction Implementations

| Implementation | Efficiency evidence | Keep case-local or promote generic helper |
| --- | --- | --- |
| Qiskit Aer repetition-memory proxy | 205,000 total shots in about 1.3 seconds | keep case-local |

## Harness Backlog Items

Abstract cross-paper lessons should be copied to
`private validation harness/REPRODUCTION_EXPERIENCE.md`.

Concrete tool, checker, template, field, or workflow changes should be copied to
`private validation harness/HARNESS_BACKLOG.md`.

| Priority | Improvement | Evidence from this case | Status |
| --- | --- | --- | --- |
| P1 | Add a circuit-location manifest field to method cards | public formula reproduced one backend but not coherent semantics | candidate, not promoted yet |
| P0 | Add a stage-domain compatibility guard | QEC adapter was routed to a 2604 distance-specific failure-attribution handler | required before confirming this case's stage |

## Prompt Or Workflow Changes

- Before opening an expensive target, require an explicit statement of which
  circuit locations receive every physical channel.
