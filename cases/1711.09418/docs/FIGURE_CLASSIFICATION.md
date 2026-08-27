# Figure Classification

| Paper item | Class | Reproduce? | Reason |
| --- | --- | --- | --- |
| Main Fig. 1 | `schematic_context` | No | It explains the replica/flux construction and contains no numerical observable. |
| Main Fig. 2 | `numeric_reproduction` | Yes, T001 | Both numerical marker series and both analytic continuous curves over all 11 displayed charges are formula-derived. |
| Main Fig. 3 | `numeric_reproduction` | Yes, T002 | The all-sector curve and every displayed charge sector (`0` through `5`) are computed both numerically and analytically. |

The machine-readable coverage contract is `figure_coverage.json`. There are no hidden supplement figures or numerical tables in the frozen source bundle.

The full TeX source embeds the Supplemental Material after the bibliography;
its two sections contain derivations only. The phrase “verified numerically”
for the unplotted critical-Ising parity formula is separately audited in
`DIGITAL_CLAIM_AUDIT.md`; because it has no disclosed author setup or numerical
artifact, it is not misrepresented as a third paper-exact figure target.
