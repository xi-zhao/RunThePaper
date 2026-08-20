# Lessons Learned

## Case Summary

- Paper: *Squeezed Spin States*
- PaperID: `PhysRevA.47.5138`
- Scientific result: seven figure panels and ten non-figure quantitative claims reproduced
- Lifecycle state: awaiting fresh-context review

## What Worked

- Treating Husimi-Q arrays as the scientific artifact and the sphere projection
  as a separate presentation artifact kept the physics/render boundary clean.
- Exact finite-spin matrices are cheaper and more reliable here than a generic
  many-body package.
- Printed Qmax values provide strong scalar anchors for every distribution panel.

## Code Defect Found and Repaired

| Direct cause | Root cause | Detection | Repair |
| --- | --- | --- | --- |
| JSON could not serialize `numpy.bool_` | scalar normalization was absent at the artifact boundary | full runner smoke test | convert NumPy scalars only during JSON encoding; rerun all gates |
| Ten quantitative claims were absent from authored scope | the coverage model treated figures as the only scientific units | fresh inventory-first review | add first-class quantitative-claim coverage and executable gates |

The defect affected artifact emission, not the physics arrays or scientific
interpretation. This is exactly why the loop must execute the whole production
entrypoint instead of relying only on unit-level formula tests.

## Generalized Experience

| Lesson | Why it generalizes | Future recommendation |
| --- | --- | --- |
| Separate spherical data from camera projection | camera choice is presentation, not physics | freeze theta/phi/Q first, then start RenderContract work |
| Compare printed scalar landmarks before pixels | an attractive image can hide a wrong unitary convention | gate every density panel on normalization and extrema |
| Reuse Hermitian eigensystems in scalar searches | repeated exponentials waste time and add numerical variation | diagonalize once per S and vary only phases |

## New Failure Modes

| Failure mode | Where it appeared | Future check |
| --- | --- | --- |
| NumPy scalar serialization failure | final run-summary emission | exercise the full CLI in smoke and formal runs |
| sphere size dominates pixel score | first Fig. 3 render | align camera/canvas only after frozen data hashes are verified |
| figure-only scope can hide scientific omissions | independent full-paper inventory | require a canonical ledger of figures plus quantitative claims |

## Reusable Checks Or Tools

| Check or tool | Reusable contract |
| --- | --- |
| full-entrypoint JSON boundary smoke | execute the production CLI and require every emitted summary to serialize after normalizing NumPy scalar types |
| sphere RenderContract | hash-lock the spherical data arrays before allowing camera, canvas and font optimization |

The JSON boundary smoke is proposed for Harness promotion because the defect is
independent of this paper's physics. The sphere renderer remains case-local
until another Bloch-sphere reproduction needs the same contract.
