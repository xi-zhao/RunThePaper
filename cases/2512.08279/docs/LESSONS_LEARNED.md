# Lessons Learned

## Case Summary

- Paper: *Programmable Open Quantum Systems*
- Paper ID: `2512.08279`
- Final status: complete reproduction
- Reproduced targets: Main Figs. 2 and 3
- Blockers: none

## What Worked

- Deriving the commuting SWAP-dephasing semigroup exposed an exact observable
  before any sampling code was written.
- Independently constructing the HPTP processor avoided dependence on the
  author repository's stored Choi matrices.
- Separating scientific comparison from pixel comparison kept source pixels
  out of the generator.
- Active-set optimization plus full-grid certification reduced a large convex
  model without weakening the paper-scale claim.

## What Was Difficult

- Choi index order, vectorization order, and output partial traces must agree
  globally; one silent transpose would invalidate both examples.
- The Fig. 3 caption, mathematical definition, and plotting script use
  \(\gamma_\epsilon\) and \(\kappa_\epsilon\) in different roles.
- The script's allocated time array and executed loop differ by one endpoint.
- Floating-point grid labels such as `0.17500000000000002` are unsafe as raw
  dictionary keys in comparison code.

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| Audit executed loop bounds, not only declared arrays | source scripts can silently omit endpoints | record nominal, allocated, and actually iterated grids separately |
| Distinguish mathematical cost from plotted transform | axes may show an operational transform of the defined monotone | trace definition, script objective, and axis label as separate formula evidence |
| Optimize a subset only with a full-domain certificate | coarse grids can miss worst-case channel error | require a matching upper-bound feasibility certificate before calling the result final |
| Quantize declared parameter grids at I/O boundaries | binary floats break exact joins | use integer grid indices or canonical decimal strings |

## Common Pitfalls

| Pitfall | Appearance here | Prevention |
| --- | --- | --- |
| copying source matrices | author repository contains ready-made Choi matrices | exclude them from generated evidence and derive the processor |
| trusting a displayed superoperator | Supplemental transpose placement is inconsistent | verify from the stated vec identity and trace preservation |
| treating visual agreement as proof | Fig. 3 curves are easy to imitate | store SDP residuals and certify all 1000 times |
| confusing random mismatch with physics mismatch | Fig. 2 seed is undisclosed | compare within recorded uncertainty and against the exact line |

## Reusable Checks Or Tools

| Candidate | Why reusable | Destination |
| --- | --- | --- |
| canonical decimal-grid join helper | prevents `0.175` key failures | future harness utility after a second case |
| active-set plus omitted-domain certificate record | makes reduced optimization auditable | future generic target-run schema |
| executed-loop grid audit | catches allocated-versus-used endpoints | source-ingest checklist |

## New Failure Modes

| Failure mode | Where it appeared | Detection rule |
| --- | --- | --- |
| declared grid differs from executed loop | Fig. 3 source allocates 1001 times but iterates 1000 | compare allocated length, loop bounds, and last consumed coordinate |
| transformed quantity mislabeled as the defined cost | \(\gamma_\epsilon\) is defined while \(2^{\gamma_\epsilon}\) is plotted | trace definition, axis expression, and script objective separately |
| raw binary float breaks a grid join | `0.17500000000000002` failed lookup against `0.175` | index sweeps by integer position or canonical decimal key |
| subset optimum mistaken for full-grid optimum | 101 active constraints represent a 1000-time family | require explicit feasibility certificates for every omitted point |

## Harness Backlog Items

| Priority | Improvement | Evidence | Status |
| --- | --- | --- | --- |
| medium | represent parameter sweeps by integer index plus decimal value | comparison initially failed at epsilon 0.175 due to raw float identity | proposed |
| medium | add a standard full-domain certification field for constraint-generation runs | Fig. 3 needed 101 active and 1000 certified points | proposed |

## Prompt Or Workflow Changes

Keep the derivation gate before numerical readiness. For optimization papers,
the gate should also state whether a reduced constraint set will be merely
exploratory or can become final through an explicit full-domain certificate.
