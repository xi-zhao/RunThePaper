# Formula Verification

Machine-readable gate: `outputs/checks/formula_verification.json` (`passed`, 9/9 numeric gates open).

| Formula | Role | Gate | Independent check / limitation |
| --- | --- | --- | --- |
| QS001 | XY single-excitation reduction | open, verified | Hermitian exchange term restores the obvious typo in main Eq. (1). |
| QS002 | Zig-zag onsite/coupling spectrum | open, verified | Spectrum and Supplement elimination require high onsite energy on even sites; main Eq. (8) has a parity typo. |
| QS003 | Three-site closed-form population | open, verified | Direct exponentiation agreement `1.67e-16`. |
| QS004 | Isospectral fractional transfer | open, verified | Spectrum preservation and endpoint split checked; Bell sign is a local gauge. |
| QS005 | 2D Kronecker-sum extension | open, reconstructed | Separability fixes the public theory lane; main Fig. 4 does not report `m`. |
| QS006 | Independent Lindblad channels | open, verified | Trace, positivity and fidelity checks pass. |
| QS007 | Static Gaussian disorder | open, source-only | Sample counts are public; seeds and exact scan arrays are not. |
| QS008 | Large-`m` Schur elimination | open, verified | Direct even-site suppression agrees with the final Supplement formula. |
| QS009 | Effective flattop pulse | open, reconstructed | Hardware-to-effective-Hamiltonian transfer functions are not public. |

An open numeric gate means the formula is sufficiently explicit for an auditable calculation. It does not make an unreported parameter paper-exact; QS005, QS007 and QS009 remain explicitly capped in downstream scoring.
