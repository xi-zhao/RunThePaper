# Formula verification

The machine-readable result is
[`../outputs/checks/formula_verification.json`](../outputs/checks/formula_verification.json).

| Formula | Role | Status | Evidence |
| --- | --- | --- | --- |
| `o = 1 + 2m + r` | Figure 8 overhead and analytic band | verified | Integer pass/ride/merge audit and 67-circuit numerical residual |
| `g = abs(o_conv-o_full)/o_full` | Figure 9 transfer metric | verified | Direct implementation of the caption metric and both thresholds |

The exact identity is also covered by the tiny-network dynamic-programming
oracle in `code/tests/test_clean_room_core.py`.
