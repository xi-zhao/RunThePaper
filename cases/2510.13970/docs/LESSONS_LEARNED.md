# Lessons learned

## New Failure Modes

- An effective Hamiltonian can be mislabeled by convention: van Vleck and a phase-fixed principal logarithm are different objects.
- A rubric may state one nested-commutator formula while grading an expression containing impossible operator families.
- A single large-frequency point can look like a finite asymptotic constant when the chosen rescaling actually diverges.
- A printed source equation is provenance evidence, not proof of algebraic correctness.

## Reusable Checks Or Tools

- Hilbert–Schmidt projection closes operator-basis claims exactly.
- Compare both `omega^2 ||Delta||` and `omega^3 ||Delta||`; convergence of the former exposes divergence of the latter.
- Verify time ordering twice: adaptive ODE plus explicit product refinement.
- Preserve generator convention and drive phase in the domain model instead of hiding them in a helper name.

`copied_to_backlog`: recommend a harness check requiring every Floquet effective Hamiltonian to declare convention and time origin.
