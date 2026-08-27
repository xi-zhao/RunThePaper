# Formula Verification

Machine-readable result:

```text
outputs/checks/formula_verification.json
```

Run:

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/2608.03987 --write
```

## Gate Summary

| Formula | Role | Gate | Reason |
| --- | --- | --- | --- |
| EQ001 | Figure 8 overhead and band | open | Source trace and symbolic volume-weighted identity both pass. |
| EQ002 | Figure 9 relative pipeline gap | open | The metric and both thresholds are stated directly in the caption. |

## Closed Or Unclear Formulas

None for the current Figure 8/9 scope.
