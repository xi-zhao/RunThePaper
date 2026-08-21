# Formula Verification

All 12 equation cards have a source pointer, a numerical code pointer and a
focused check. EQ001-EQ007 are direct paper formulas. EQ008 and EQ012 contain
standard reconstruction steps whose finite protocols are absent from the paper.
EQ009-EQ011 deliberately preserve both literal and normalization-consistent
forms.

```bash
python PRAgent-workflow/scripts/check_formula_gate.py case/1206.2505 --write
```

The machine record is `outputs/checks/formula_verification.json`. An open
question does not authorize changing the paper; it identifies exactly what a
fresh scientific reviewer must attempt to disprove.
