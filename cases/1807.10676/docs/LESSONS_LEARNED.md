# Lessons Learned

## Case summary

- Paper: *All "Magic Angles" Are "Stable" Topological*
- Executed: 12 composite targets / 42 numerical subpanels
- Code-ready but externally deferred: 12 paper-scale DFT entries
- Lifecycle state: artifact-valid local theory results; attested DFT execution and fresh independent review remain open

## Reusable lessons

| Lesson | Why it matters | Next-paper rule |
| --- | --- | --- |
| Complete reciprocal shells are a scientific invariant | Rectangular/incomplete cutoffs can break C3 and fake splittings | Record basis shape and compare `N` with `N+1` |
| Sparse Ritz selection needs a safety window | Close central bands can swap if exactly the requested count is used | Solve extra eigenpairs, then select the physical subspace |
| Wilson loops require embedding and polar transport | Raw overlaps accumulate nonunitarity and wrong boundary phases | Unitarize each overlap and close with the reciprocal embedding |
| Compact site notation can hide a gauge transformation | The second `2c` trial orbital needs the symmetry-related conjugation order | Validate gauge interpretation against an independent paper invariant such as `det S` |
| Node dots must be derived, not copied | Their position and sign are numerical observables | Find gap zeros and compute local Jacobian vorticity |
| GPU availability is not universal acceleration | Sparse CPU and licensed high-memory DFT have different bottlenecks | Select hardware from the workload, and state why |
| Pixel optimization must follow data freeze | Otherwise presentation tuning can silently alter physics | Hash arrays first; render in a separate contract |

## Source issues found

- The TB4 nearest-vector sentence repeats `delta_2`; C3 closure fixes the missing third vector.
- Supplement Fig. 6 prints `1.039°` for one parameter set while the stated formula gives `1.029°`.

Both are recorded rather than silently copied.

## New Failure Modes

| Failure mode | Detection | Prevention |
| --- | --- | --- |
| Run contract points to a stale template selector | Isolated runner rejects a selector absent from the actual JSON | Freeze and compare the complete configuration object when it contains several parameter namespaces |
| Central Ritz vectors swap near close levels | Wilson branches jump or violate symmetry | Request an extra eigenspace safety window before selecting the target subspace |
| Site-symmetry gauge is interpreted identically on both `2c` sites | Projected overlap becomes singular or misses the paper's invariant | Apply the symmetry-related coefficient ordering and test `det S(k)` |

## Reusable Checks Or Tools

| Check | Reuse |
| --- | --- |
| Complete-shell `N -> N+1` convergence | Continuum models on reciprocal lattices |
| Wilson-loop reciprocal-embedding and C2 symmetry residual | Multiband topology cases |
| Full-config equality in isolated run contracts | Cases with separate physical and numerical config sections |
| Post-freeze hash check around rendering | Every reference-aware pixel optimization lane |
