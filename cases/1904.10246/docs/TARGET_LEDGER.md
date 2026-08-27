# Target Ledger

| Target ID | Paper item | Type | Formula dependencies | Method dependencies | Gate | Status | Planned evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `T_FIG2` | Fig. 2, panels A-F | finite_size_scaling | EQ001-EQ005 | MTH001-MTH002 | verified | reproduced | CSV, 7/7 slope/CR checks, six-panel figure, comparison board, passing pixel evidence |
| `T_TABLE1` | Table 1 | table_reproduction | EQ003-EQ006 | — | verified | reproduced | CSV, 6/6 exact entries, exponent checks, rendered table, passing pixel evidence |
| `T_TABLE2` | Table 2 | table_reproduction | EQ008 | MTH004 | verified | reproduced | CSV, 38/38 exact cells, block-sum cross-check, rendered table, passing pixel evidence |
| `T_FIGA` | Fig. A | scatter_or_marker_plot | EQ001, EQ002, EQ004, EQ007 | MTH001, MTH003 | verified | reproduced | CSV, 6/6 percentile/comparator checks, comparison board, passing pixel evidence |

## Authorization Boundary

Every execution uses:

```bash
python PRAgent-workflow/scripts/run_target.py \
  case/1904.10246 <TARGET> --stage final_reproduction -- \
  python scripts/reproduce.py --target <TARGET>
```

The case runner requires `--target`, verifies it equals
`PRAGENT_GUARDED_TARGET_ID`, and writes only that target's outputs. Reference
images are never written under generated-data paths.

## Final Parameter Contract

All four targets are `paper_exact`:

- Fig. 2: six paper amplitudes, \(N_{\rm shot}=100\), 1000 repetitions,
  paper LIS/EIS/classical rules, \(10^2\)-\(10^5\) query range.
- Table 1: the paper's asymptotic likelihood-search model.
- Table 2: \(n=2\), \(b_{\max}=\pi/4\), all-to-all, Qiskit 0.7 convention,
  \(2^0\)-\(2^8\).
- Fig. A: \(a=1/48\), \(N_{\rm shot}=30,100\), 1000 repetitions,
  \(100(8/\pi^2)\) percentile and the paper's conventional comparator.

## Completion

- Scientific score: `93.75`, `complete_reproduction`
- Final-reproduction figures eligible: `4 / 4`
- Pixel contracts passed: `4 / 4`
- Open target blockers: `0`
