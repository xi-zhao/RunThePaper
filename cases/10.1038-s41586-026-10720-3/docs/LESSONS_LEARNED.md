# Lessons learned

This case demonstrates why coverage, execution, scientific fidelity, and
rendering must be separate dimensions.

| Lesson | General rule |
| --- | --- |
| Mixed panels hide the denominator | split theoretical curves from experimental markers before scoring |
| A formula can be exact while its parameters are missing | track formula gate and parameter match separately |
| A successful run can still use the wrong scientific normalization | require limiting tests and explicit code-fault exclusion |
| Source-derived fits inflate visual scores | keep all source curves/markers out of the scientific runner |
| A100 cannot manufacture missing inputs | schedule compute only when it can discriminate a scientific hypothesis |
| Internal convergence is not a paper result | exclude auxiliary checks from paper coverage |
| Pixel comparison is useful after data freeze | RenderContract may alter presentation, never physics or arrays |

## New Failure Modes

- A surrogate can preserve qualitative root ordering while its ultraviolet
  continuation remains insufficiently tested.
- A numerically stable UPPE can still use an underived field normalization.
- Mixed experimental/theory panels can silently inflate the reproducible-item
  denominator unless each series is classified separately.

## Reusable Checks Or Tools

The reusable core is small: atomic item inventory, target contract, isolated
run attestation, causal diagnosis, post-freeze render evidence, and
fresh-context review. `project inspect` derives lifecycle state from these
artifacts.
