# Formula Verification

The machine-readable result is
`outputs/checks/formula_verification.json`. The derivation-first gate is
allowed to open only when every card has both a source trace and an
independent symbolic, normalization, limiting-case, or numerical sanity
check.

| Formula | What it controls | Independent check | Gate |
| --- | --- | --- | --- |
| `EQC001` | GKSL matrix and vectorization | trace preservation; analytic amplitude damping | open |
| `EQC002` | Choi reshuffling and normalization | identity-channel Choi and program-state trace | open |
| `EQC003` | SWAP-dephasing factorization | commutation, idempotence, endpoints | open |
| `EQC004` | exact Fig. 2 overlap | Bell-basis derivation and limits | open |
| `EQC005` | fixed HPTP SWAP processor | Hermiticity, trace, exact programmed action | open |
| `EQC006` | signed CPTP sampling | trace-weight identity and estimator expectation | open |
| `EQC007` | \(\gamma_\epsilon\) versus \(2^{\gamma_\epsilon}\) | axis label and disclosed script objective | open |
| `EQC008` | finite-grid cost SDP | trace constraints and epsilon LMI reduction | open |
| `EQC009` | program-state Choi contraction | matrix-index expansion and TP inheritance | open |
| `EQC010` | HP diamond norm | Watrous block symmetry and identity norm | open |
| `EQC011` | Fig. 3 models and grids | analytic channel, Choi trace, loop audit | open |

## Source issues that do not close the gate

Two source-level inconsistencies are isolated rather than propagated:

1. the Supplemental Liouville display places transposes on the loss terms
   inconsistently with its own identity
   \(\operatorname{vec}(ABC)=(A\otimes C^T)\operatorname{vec}(B)\);
2. the Fig. 3 scripts allocate the \(t=10\) endpoint but loop over only the
   first 1000 of 1001 values.

The first is resolved by direct algebra and does not affect the paper's real
diagonal \(L^\dagger L\). The second is preserved in the source-matching run
and tested separately. Neither is hidden by fitting the figures.

## Command

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2512.08279 --write
```
