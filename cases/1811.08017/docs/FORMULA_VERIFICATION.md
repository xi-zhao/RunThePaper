# Formula Verification

| Formula | Gate | Independent check |
| --- | --- | --- |
| EQ001 | open | All three parameter tuples are printed in both numerical figures. |
| EQ002 | open | 60-digit Decimal evaluation proves the chosen qDRIFT `N` passes and `N-1` fails, without the large-N approximation. |
| EQ003 | open | 60-digit Decimal evaluation proves the chosen first-order `r` passes and `r-1` fails. |
| EQ004 | open | Orders 2,4,6,8 are independently boundary-refined before selecting the minimum. |
| EQ005 | open | qDRIFT phase cost has exact `P_f^-3` scaling. |
| EQ006 | open | Trotter phase cost has exact `P_f^-2` scaling and all three printed ratios match. |

No curve coordinates or author numerical arrays are used.

`open` here means the formula gate is open for numerical execution. It does not
mean a fresh scientific reviewer has independently endorsed the paper or the
current discrepancy interpretation.
