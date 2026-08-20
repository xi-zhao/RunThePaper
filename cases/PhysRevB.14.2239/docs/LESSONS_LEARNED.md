# Lessons Learned

## What worked

- Treating every figure as a scientific object prevented Fig. 2 from being
  incorrectly discarded as a schematic.
- Pairing two Chambers extrema gave all q bands efficiently, while the transfer
  product provided a genuinely different cross-check.
- Freezing arrays before RenderContract work cleanly separated physics from
  presentation optimization.
- The full campaign was cheap enough to run at declared scale locally; no
  artificial A100 path was added.

## New Failure Modes

The first Fig. 5 render used the correct frozen spectrum but transposed the
alpha/energy array orientation. Its pixel score was 62.45. Comparing the axis
semantics against the already verified energy symmetry identified a renderer
coordinate defect, not a numerical-model defect. Reorienting the axes raised
the score to 81.35 without changing any scientific hash.

## Reusable Checks Or Tools

| Lesson | General value |
| --- | --- |
| A diagram-like panel can still be numerical | Classification must follow how the object was constructed, not its visual style. |
| Cross-method physics checks catch silent spectral mistakes | Hermitian roots and transfer products fail differently. |
| Publication sampling is not a physical parameter | Preserve the exact model while labeling render density as reconstructed. |
| Pixel repair must identify its layer | Axis orientation belongs to RenderContract; changing arrays would have been an invalid repair. |
| Cheap complete runs should not be wrapped in HPC machinery | Compute architecture should match the actual bottleneck. |

## Harness backlog

- Add an axis-semantics preflight for raster targets that compares declared
  array dimensions with plotting extents before pixel scoring.
- Keep the existing causal diagnosis distinction between publication omission,
  code fault and insufficient compute; this case demonstrates all three are not
  interchangeable.
