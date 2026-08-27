# Formula Verification Gate

Formula verification is a required gate before numerical reproduction.

## Gate Levels

1. `source_verified`: the formula card maps back to the paper source by TeX
   label, extracted equation ID, or exact text anchor.
2. `symbolic_verified`: derived identities pass symbolic checks where a check is
   defined.
3. `numeric_gate`: the formula is allowed to feed numerical code only if its
   policy passes:
   - `source_only`: source verification is enough because the paper directly
     states the working formula.
   - `source_and_symbolic`: both source and symbolic checks must pass.
   - `blocked_pending_derivation`: never allowed until the derivation is
     completed.

## Current Status

The canonical machine-readable formula cards are now `EQUATION_CARDS.json`.
The older source map `formula_source_map.json` is retained as provenance for
the first formula gate pass.

The verification output is `outputs/checks/formula_verification.json`.

Latest verification result:

- Overall source traceability: `passed`
- Numeric gate open: 10/10 cards
- Numeric gate closed: none
- Open-chain gate note: `EQC003` is now source-verified against the paper's
  real-space equations and machine-verified by checking
  `open_chain_hamiltonian` matrix entries in the `(A1, B1, A2, B2, ...)`
  basis.
- Open-boundary spectrum note: `EQC008` is now source-verified against Eq.
  `spectra` and machine-verified by checking that `non_bloch_ab` on
  `beta = r exp(ik)` matches the paper's signed open-boundary spectrum formula.
- Nonzero-`t3` gate note: `EQC010` is now source-verified against Eq. `t3E`
  and symbolically verified by expanding the quartic beta equation.

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/1803.01876 --write
```

Current intended gates:

| Formula card | Purpose | Gate policy |
| --- | --- | --- |
| EQC001 | Bloch Hamiltonian | `source_and_symbolic` |
| EQC002 | Bloch eigenvalues and exceptional points | `source_and_symbolic` |
| EQC003 | Open-chain real-space equations | `source_and_symbolic` |
| EQC004 | Similarity transform shortcut | `source_only` |
| EQC005 | Open-boundary transition | `source_and_symbolic` |
| EQC006 | Beta ansatz and bulk equation | `source_and_symbolic` |
| EQC007 | Generalized Brillouin zone for `t3=0` | `source_and_symbolic` |
| EQC008 | Open-boundary bulk spectrum | `source_and_symbolic` |
| EQC009 | Non-Bloch Hamiltonian and winding number | `source_and_symbolic` |
| EQC010 | Nonzero `t3` beta equation | `source_and_symbolic` |

## Numerical Rule

No numerical target may use a formula card whose `numeric_gate` is closed.
