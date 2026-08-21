# Lessons Learned

## Reusable scientific lessons

1. A visually wrong order-parameter curve can be a method-level defect. Moving
   from `N=12` exact-spin dynamics to the paper's Majorana-Pfaffian observable at
   `N=256` fixed Main Fig. 3 bottom without reading source pixels.
2. Cluster decomposition creates a real observable-convention ambiguity:
   correlation, spin correlation and its square root must be frozen separately.
3. A paper's general claim can still receive executable evidence when its exact
   protocol is absent. The generic ramp API separates the theorem mechanism
   from explicitly reconstructed linear/smoothstep examples.
4. Formula auditing must preserve literal and corrected variants. Quietly
   correcting a sign or normalization would erase evidence needed for peer
   review.

## Harness implications

The current core model already supports these lessons: formula cards bind code,
isolated runs bind input/output hashes, and fresh review—not the reproducer—owns
paper-error classification. No new Harness special case is needed; the
Majorana, ramp and normalization implementations remain case-local physics.

## New Failure Modes

- Interpolating both a convex conjugate variable and its cumulant can create a
  false zero plateau; solve the monotone saddle equation and evaluate the
  cumulant at the solved saddle instead.
- A nonnegativity check alone cannot detect clipping. The frozen science gate
  must also require that no off-mean work density has an exact zero rate.

## Reusable Checks Or Tools

- Compare the production saddle solver against an independent bounded scalar
  maximizer on representative points.
- Record the maximum number of off-mean zero-rate grid points as a machine
  invariant; the accepted value is zero.
