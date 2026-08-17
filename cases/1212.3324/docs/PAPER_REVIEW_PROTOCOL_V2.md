# Protocol-v2 paper assessment

## Verdict boundary

This document is the reproducer's falsification audit, not a fresh independent
review.  It emits no `paper_error_candidate`.  The present paper assessment is
`inconclusive`: the numerical results support the paper's topological claims,
but the sublattice-potential notation has a probable factor-two paper-claim
discrepancy and the required inventory-first reviewer has not adjudicated it.

The full declared paper-scale campaign ran in the isolated execution
`1212.3324-paper-scale-v5`. It completed in 122.019522 s with 19/19 science
checks passing and zero forbidden file accesses.  Consequently, insufficient
local compute is not the direct cause of any remaining target gap.

## Complete review inventory

The manuscript and appendices contain eight numerical figure panels plus one
family of quantitative topological claims:

| Target | Claim tested | Self-audit result |
| --- | --- | --- |
| T001 | Fig. 2(c), ideal anomalous edge branches | supported by the bulk identity and explicit open-edge branches |
| T002 | Fig. 3(a), trivial strip spectrum | topology supported; render accepted |
| T003 | Fig. 3(b), Chern strip spectrum | topology supported; render accepted after post-freeze line-only repair |
| T004 | Fig. 3(c), anomalous strip spectrum | topology supported; render accepted |
| T005 | Fig. 3(d), phase sequence and invariants | sequence supported; notation discrepancy remains inconclusive |
| T006 | Fig. 6(a), weak-drive resonance surface | resonance/static Chern supported; render accepted after camera/axes-only repair |
| T007 | Fig. 6(b), static cylinder spectrum | Hermiticity, Chern and independent strip-matrix parity supported; pixel below threshold because finite metadata are unavailable |
| T008 | Fig. 6(c), truncated Floquet spectrum | Hermiticity, driven Chern, time convergence and strip-matrix parity supported; pixel below threshold because finite metadata are unavailable |
| T009 | winding/Chern/edge-count identities | supported by two distinct topology calculations; fresh review missing |

Fig. 1, Fig. 2(a,b), Fig. 4 and Fig. 5 are schematic and are not numerical
targets.  There is no separate supplement or numerical table.

## Active falsification: sublattice-potential convention

The manuscript first defines
`delta_AB = epsilon_A - epsilon_B` (accepted-source TeX line 399), but the
displayed two-level Hamiltonian uses `+ delta_AB sigma_z` (line 408).  With the
standard `sigma_z = diag(1,-1)`, that matrix term creates an onsite difference
of `2 delta_AB`.  The Fig. 3 caption then prints `delta_AB = 0.5 pi/T`
(lines 679-681).

The implementation therefore freezes and executes both readings:

- onsite-difference reading: matrix coefficient `delta_AB/2`, giving gap
  closings near `J/pi = 1.21` and `2.06`;
- literal displayed-equation reading: matrix coefficient `delta_AB`, giving
  gap closings near `J/pi = 1.08` and `1.99`.

The visible phase anchors are approximately `1.3` and `2.1`, while post-freeze
comparison of the strip spectra favors the literal displayed equation. Exact
Pauli eigenvalue algebra, converged scans and independent topology calculations
exclude a numerical factor-two artifact. This is a probable source-level
paper-claim discrepancy, but it is not yet a paper-error candidate because a
fresh protocol-v2 reviewer has not attempted to falsify it.

## Direct causes, root causes and code-fault status

| Scope | Direct cause | Root cause | Code fault assessment |
| --- | --- | --- | --- |
| T001, T002, T003, T004, T006 | exact original finite-grid values are unavailable | publication omits strip/grid/render metadata | no fault found; pixels accepted after permitted style-only repair where needed |
| T007, T008 | scientific-region pixel score remains below 80 | exact finite-strip/boundary/display metadata are unpublished | **ruled out after checks**; two independent strip constructions agree to roundoff |
| T005 | printed definition and displayed matrix coefficient conflict | probable source-level paper-claim discrepancy | **ruled out after checks** for a numerical factor-two artifact; fresh review still gates paper-error classification |
| T009 | independent review evidence is missing | review-process gap | no fault found by the two topology methods, but lifecycle promotion is blocked |

The two remaining low-render targets are not small-parameter, compute or open
code-repair failures: the full declared paper-scale configuration ran and the
second strip construction agrees to roundoff. Their next discriminating input
is the authors' original finite-strip metadata. No physical parameter or
numerical array may be adjusted from paper pixels.

## Promotion gate

`paper_supported` requires a validator-accepted fresh-context review.
`paper_error_candidate` additionally requires two distinct strong checks,
explicit falsification of alternative interpretations, quantified tolerance,
and exclusion of reproduction and compute ambiguity.  None is self-issued in
this case.
