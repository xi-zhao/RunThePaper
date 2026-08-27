# Formula Verification

## Gate Summary

Machine-readable evidence:
`outputs/checks/formula_verification.json`.

- Status: `passed`
- Cards: 8
- Trusted/open for numerics: 8
- Closed or blocked: 0
- Policy: source trace plus independent symbolic/limiting verification

| Formula card | Role | Source gate | Independent checks | Numeric gate |
| --- | --- | --- | --- | --- |
| `EQC001` | finite double-slit support | verified | exact interval decomposition and support normalization | open |
| `EQC002` | Fresnel field and baseline response | verified | symmetry, zero-aberration, and normalization limits | open |
| `EQC003` | weighted moments and local derivatives | verified | analytic field derivatives versus central finite differences | open |
| `EQC004` | noise weight and full Fisher matrix | verified | positivity, symmetry, and direct quadrature construction | open |
| `EQC005` | matched filters and nuisance-orthogonal codes | verified | zero mean, unit norm, and Gram--Schmidt orthogonality | open |
| `EQC006` | coded Fisher matrix and retention | verified | basis invariance and eigenvalue bounds in \([0,1]\) | open |
| `EQC007` | Gaussian toy-code basis | verified | parity structure, zero mean, unit norm, orthogonality | open |
| `EQC008` | finite-width defocus visibility | verified | point-slit suppression and independent five-width scan | open |

## Dependency Coverage

- Fig. 1(a): `EQC001`, `EQC002`
- Fig. 1(b): `EQC001`--`EQC003`
- Fig. 1(c): `EQC002`--`EQC005`, `EQC007`
- Fig. 1(d): `EQC003`--`EQC007`
- Fig. S1: `EQC001`--`EQC004`, `EQC008`

Every final target therefore has only trusted formula dependencies. Full
source locations, assumptions, derivations, units, and code references remain
in `EQUATION_CARDS.json` and `DERIVATION_TRACE.md`; `DERIVATION.md` is the
harness-generated readable projection.

## Closed Or Unclear Formulas

None.
