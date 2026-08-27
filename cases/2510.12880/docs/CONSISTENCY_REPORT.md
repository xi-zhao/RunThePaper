# Consistency Report

## Summary

| State | Count | Targets |
| --- | ---: | --- |
| covered analytic/numeric item | 4 | V001, V002, T001, T002 |
| uncovered method/implementation item | 5 | V003-V007 |
| excluded non-numeric display item | 11 | schematics and tensor diagrams |

Whole-paper coverage is `4/9 = 44.44%`. Covered-item fidelity is
`92.03/100`; reproduction degree is `40.90/100`.

## Covered Evidence

| Target | Consistency | Evidence | Residual limitation |
| --- | --- | --- | --- |
| V001 | exact at accepted sizes | `outputs/checks/v001_paper_target_run.json` | N=8,10,12 not in accepted run |
| V002 | exact periodic controls | `outputs/checks/v002_paper_target_run.json` | fresh independent review pending |
| T001 | feature match | `outputs/checks/t001_paper_target_run.json` | one of 25 points differs by `0.00363848` |
| T002 | exact within digitization tolerance | `outputs/checks/t002_paper_target_run.json` | author solver metadata unavailable |

## Uncovered Evidence

V003-V007 are not labeled as failed physics. They are `uncovered` because no
claim-specific implementation and accepted artifact exists. The direct cause
for all five is therefore `implementation_not_ready`; the confirmed root cause
is a previous reproduction-method/scope gap. Code faults remain `not_excluded`
until the discriminating tests in `TARGET_LEDGER.md` are implemented.

## Provenance Boundary

Generated CSVs come from independent diagonalization. Digitized source markers
are comparison-only evidence and never enter the scientific runner. No numeric
array, physical parameter, or existing score was changed during this inventory
audit.
