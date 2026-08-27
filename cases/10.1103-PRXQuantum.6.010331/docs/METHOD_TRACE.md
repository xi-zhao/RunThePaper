# Method Trace

This is a formula-driven physics case. `EQUATION_CARDS.json`, `DERIVATION.md`,
and `DERIVATION_TRACE.md` are authoritative. The orchestration method is:

1. evaluate the four Appendix-L universal response functions (`T001`);
2. apply the exact scaling laws in Eqs. (15)-(16) (`T002`);
3. evaluate every formula-closed application target (`T003`, `T004`, `T006`,
   `T007`, `T008`) with unavailable amplitudes left explicit;
4. propagate public CZ protocols in the 8D Hamiltonian (`T005`);
5. propagate the disclosed seven-site reconstruction and tangent equations
   (`T009`);
6. validate formula traces, limiting cases, closure, norm/convergence, and
   generated-data provenance;
7. read source images only inside the post-computation comparison function.

Entrypoints: `scripts/run_reproduction.py`,
`scripts/run_formula_theory_targets.py`, and
`scripts/audit_computational_provenance.py`.
