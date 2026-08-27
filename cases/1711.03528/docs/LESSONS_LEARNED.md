# Lessons Learned

## Generalized Experience

| Lesson | Why it matters beyond this case | Future recommendation |
| --- | --- | --- |
| A visually plausible proxy can still fail if it uses the wrong symmetry sector. | Many physics figures are sector-specific; ignoring the sector changes the numerical object. | Record required momentum, inversion, parity, boundary condition, and unfolding protocol before scoring a figure. |
| Product-state initial conditions can become illegal on finite periodic chains. | Finite-size wrapping can invalidate a state that looks valid in the thermodynamic notation. | Check state legality against the exact finite-size Hilbert space before launching dynamics. |
| Approximation methods need explicit state matching. | FSA, variational, and reduced-basis methods can look qualitatively right while comparing the wrong eigenstate. | Match approximate and exact states by energy, symmetry, overlap, or the paper's stated selection rule. |

## Common Pitfalls And Pain Points

| Pitfall | How it appeared | How future runs should avoid it |
| --- | --- | --- |
| Symmetry-sector mismatch | Fig. 4 requires `k=0, I=+`; the local proxy used the full constrained sector. | Add a required-sector field to target specs and mark missing sector support as partial. |
| Boundary wrap-around | Some density-wave states are illegal for certain finite PBC sizes. | Validate every product state against the case basis before time evolution. |
| Reduced-basis overclaim | Near-zero FSA captures oscillatory structure but not the exact projection amplitude. | Score ground-state and mid-spectrum FSA panels separately when possible. |

## Recommended Practices

| Practice | When to use it | Evidence from this case |
| --- | --- | --- |
| Use constrained Hilbert space directly. | Rydberg blockade or other constrained models. | `L=16` feature run finishes quickly and avoids full `2^L` basis. |
| Separate data generation from plotting. | Every numerical figure. | Outputs are reusable across checks, scorecards, and case intro. |
| Treat large-system claims as planned reruns when sector support is missing. | ED, tensor network, Monte Carlo, or disorder-averaged papers. | Fig. 4 remains partial until sector and unfolding are implemented. |

## New Failure Modes

- Symmetry-sector mismatch can make a visually plausible level-statistics plot fail scientifically. Fig. 4 needs the same sector and unfolding protocol as the paper.
- Finite periodic chains can make a density-wave product state illegal after wrapping around the boundary. The case code now chooses a legal translation for `Z3/Z4` states.
- FSA comparison needs explicit eigenstate matching, not just selecting a middle index by hand.

## Reusable Checks Or Tools

- Add a generic `required_symmetry_sector` field to figure targets when the paper states sector-specific results.
- Add a product-state legality check before dynamics starts.
- Record whether a figure is a full target or a local proxy target.

## copied_to_backlog

- Added backlog item H021 for symmetry-sector and boundary-condition requirements.
- Added the generalized lessons to `PRAgent-workflow/REPRODUCTION_EXPERIENCE.md`.
