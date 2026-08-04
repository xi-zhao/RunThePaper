# Lessons learned

1. A source contract can be valid while benchmark gold is deeply inconsistent; the two gates must remain separate.
2. For radial torus spectra, the relevant discrete objects are sums-of-two-squares shells, not every integer shell and not a continuum annulus.
3. The finite-(k) threshold and generalized-mapping singularity are the same denominator zero here. Their agreement is a powerful cross-check.
4. Conserved dynamics changes wavelength selection because the growth rate carries an additional (k^2) factor.
5. Literal execution of supplied code is necessary: the frozen Task 2 code and claimed output disagree by far more than tolerance.

## New Failure Modes

- A benchmark can use the correct source dispersion yet report output that its own displayed code cannot produce.
- A wrong sign in a cusp identity can propagate into both a phase-instability threshold and a thermodynamic mapping, creating apparently independent but correlated errors.
- A nonconserved wavelength-selection formula can be pasted into conserved dynamics after the correct stationary point was already derived.

## Reusable Checks Or Tools

- `rigorous_shell_bound_2d` converts a radial continuum vertex into a provably sufficient sum-of-two-squares search domain.
- The mapping-denominator/finite-k threshold identity is a case-local cross-check worth reusing for nonlocal scalar active-matter models.
- The small-s coefficient-recovery test checks Taylor signs against the exact nonlocal dispersion without symbolic software.
