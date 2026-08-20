# Lessons learned

## Scientific lesson

For Floquet systems, a band Chern number alone cannot identify anomalous edge
transport.  The full time evolution and its gap winding must be implemented as
a first-class observable and cross-checked against edge spectra.

## Reproduction lesson

The paper's sublattice-potential symbol admits two factor-two readings.  A
clean reproduction must preserve both branches until evidence resolves them;
silently choosing one creates a hidden parameter fit.  Post-freeze image
comparison can discriminate source conventions, but it cannot by itself prove
which scientific interpretation is correct.

## Harness lesson

A successful paper-scale run and passing invariants do not automatically close
a target. T003 and T006 were presentation defects and closed through a
post-freeze RenderContract repair. T007-T008 needed a second independent strip
construction before code fault could be ruled out; once both matrices agreed
to roundoff, the remaining lack of exact finite-strip metadata became a
terminal publication boundary rather than an endless repair loop.

The available A100 is not automatically the right backend.  This campaign's
small dense matrix workload completed on CPU in about two minutes; independent
boundary implementations and review provide more evidence value than moving
the same calculation to a GPU.

## New Failure Modes

- A symbol can be internally consistent within each equation yet inconsistent
  between its prose definition and matrix coefficient.  Parameter provenance
  must therefore record semantic meaning, not only the printed scalar.
- Passing topology invariants can coexist with a wrong finite strip
  termination. A target-level shape mismatch keeps code fault open until an
  independent construction agrees, after which unpublished source metadata can
  be named as the actual boundary.
- Switching a small dense workload to a GPU can create backend uncertainty
  without testing the actual blocker.

## Reusable Checks Or Tools

- Preserve competing source conventions as named configuration branches and
  run both before any render comparison.
- Pair a bulk invariant with an explicit open-boundary observable so a shared
  interpretation is not accepted from one method alone.
- Require every low-scoring target to state direct cause, root cause and code
  fault status; only unresolved code hypotheses stay in the repair loop.
  Publication underspecification becomes terminal only after independent
  construction and convergence checks rule out a reproduction defect.
