# Derivation Trace

| Card | Paper source | Numerical role | Code | Gate |
| --- | --- | --- | --- | --- |
| EQC001 | computational method | Wannier Hamiltonian | `qe.py` | open |
| EQC002 | DFT+DMFT method | lattice Dyson equation | `lattice.py` | open |
| EQC003 | one impurity per inequivalent Ni | local projection/Weiss field | `lattice.py`, `dmft.py` | open |
| EQC004 | density-density U=10 eV, J=1 eV, CT-HYB | impurity interaction/solver | `cthyb.py` | open |
| EQC005 | fully localized limit | double counting | `dmft.py` | open |
| EQC006 | full charge self-consistency | joint fixed point | paper-scale runner | open, production adapter missing |
| EQC007 | Figs. 1,2,4,5,S1,S2 | spectra | `observables.py` | open |
| EQC008 | Figs. 3,6 | spin correlation | `cthyb.py`, `dmft.py` | open |
| EQC009 | surface-energy text | surface energy | `observables.py` | open |

All numerical code is independently written. The source archive was used for
equations, parameter statements, captions, and comparison only; it contains
no author code or numeric arrays.
