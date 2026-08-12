# Formula Verification

All eight equation cards have open numerical gates.

| Card | Check | Result |
| --- | --- | --- |
| EQC001 | B_DM impurity-density reconstruction | below 1e-12 |
| EQC002 | B_GF orthogonality | below 1e-12 |
| EQC003 | natural-orbital occupation and orthogonality | passed |
| EQC004 | Eq. (2) Hartree-Fock subtraction round trip | 1.4e-17 |
| EQC005 | self-energy rotation covariance | below 1e-11 |
| EQC006 | GW replacement limiting case | exact |
| EQC007 | noninteracting and spectral sum-rule checks | passed |
| EQC008 | local-block projection and Fourier round trip | exact within 1e-12 |

An open formula gate means the implemented mathematics is internally
consistent. It does not mean the paper-scale material result was executed.
