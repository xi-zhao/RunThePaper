# Formula Verification

Gate record: `outputs/checks/formula_verification.json`. Numerical invariant record: `outputs/checks/scientific_formula_checks.json`.

| Formula | Role | Gate | Evidence |
| --- | --- | --- | --- |
| EQ001 | moire geometry | verified | reciprocal/direct duality and 16.58 nm period |
| EQ002-EQ003 | potential/tunneling harmonics | verified | mirror/C3 structure and high-symmetry values |
| EQ004 | continuum Hamiltonian | verified | Hermiticity, corner degeneracy, cutoff 4→5 convergence |
| EQ005 | pseudospin topology | verified | `N_w=-0.9969` |
| EQ006 | Berry/Chern/gaps/DOS | verified | `C=(-0.9778,+0.9760)`, angle transitions |
| EQ007 | Kane-Mele model | verified | printed hopping values and explicit lattice structure factors |
| EQ008 | remote conduction model | verified | Hermiticity and `0.00732` small parameter |
| EQ009 | remote spin model | verified | Hermiticity and spectral continuity |

No formula remains closed for T001-T011. The DFT panels are blocked by computation/metadata, not by an attempt to replace them with continuum equations.
