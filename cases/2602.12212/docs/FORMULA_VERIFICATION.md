# Formula Verification

Machine-readable gate:
`outputs/checks/formula_verification.json`.

## Gate design

| Card | Numerical role | Policy | Current evidence |
| --- | --- | --- | --- |
| EQ001 | QFI/minimum-variance acceptance identity | source only | Eq. (2) and its QFI footnote |
| EQ002 | construct \(H_\rho\) | source + symbolic | matrix-element derivation and commuting limit |
| EQ003 | construct the optimal ensemble | source + symbolic | normalization, reconstruction, representative energy |
| EQ004 | leaf-canonical curves | source + symbolic | Gibbs-weight expansion and trace normalization |
| EQ005 | typicality curves | source + symbolic | representative-ratio identity and count bounds |
| EQ006 | spin-chain Hamiltonians | source only | Main Eq. (9), Supplemental Eq. (S1), captions |
| EQ007 | dynamics representative | source only | Main Fig. 2 caption and dimensional check |
| EQ008 | independent QFI evaluation | source + symbolic | SLD spectral solution and commuting limit |
| EQ009 | spectral compression | source + symbolic | probability normalization and entropy bounds |

The formula gate concerns mathematical traceability. It does not erase omitted
paper metadata. Boundary condition, shell integer/edge handling, site averaging,
and confidence-band convention remain parameter-match questions in
`TARGET_LEDGER.md`.

After the core module exists, the executable sanity checks listed in
`DERIVATION_TRACE.md` section 9 must be run and recorded separately before any
target is promoted from exploratory to final reproduction.
