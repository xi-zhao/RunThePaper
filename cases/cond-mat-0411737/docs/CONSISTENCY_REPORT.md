# Consistency Report

## Scientific result

The authored map has 50 items, including 46 numerical claims. Forty-three
numerical items map to 13 executable targets and three are explicitly blocked
by external source inputs. All 40 v11 machine assertions pass. EQ017 is now an
explicit reconstructed proxy plus an active minimal-path falsification rather
than a uniform-field formula. The v8-v11 repair
closes the six v7 defects at the implementation/contract level. The independent
v18 review now validates that repaired evidence with complete whole-paper scope.

| Class | Targets | Meaning |
| --- | --- | --- |
| paper-exact formula/parameter checks | T002,T006-T009,T012-T013 | printed dimensionless formulas and values are directly tested |
| paper-subset or mixed | T001,T003-T005 | core claim is tested; finite grids, a physical operator or a mechanism are publication-underspecified |
| not paper-exact material constants | T010,T011 | formula and scale pass, but one numerical material constant is absent from the paper |

The v7 atomic review remains historical evidence rather than a verdict copied
forward. The current v18 review independently inventoried 120 paper objects and
adjudicated 114 numerical claims: 104 supported, ten inconclusive, zero
reproduction defects and zero paper-error candidates. Six target projections
are fully supported and seven are conservatively inconclusive because each
contains at least one publication- or external-input-limited claim.

T001's predeclared scientific-region pixel score is 90.3679 (`high_fidelity`).
The full-canvas score 89.3059 is diagnostic only because the paper includes a
non-numerical lattice inset.  Pixels never enter the numerical runner.

## Proxy and external-input boundaries

The finite-Rashba full-BZ Kubo sweep uses the conventional symmetrized spin
current because the target paper does not print the conserved-current operator
delegated to its citation.  It is a useful falsification path but remains
inconclusive for the exact cited observable.  Mobility, graphite splitting and
substrate-specific Rashba claims require external data/models absent from the
paper and are recorded as `missing_source_input`, not code or compute failures.

The finite-Rashba boundary claim is separate from that Kubo limitation. It is
now tested by full-Brillouin-zone edge-localized spectral flow for both boundary
orientations, three widths and all subcritical couplings; all 30 combinations
pass nested-grid convergence without a TRIM or zero-energy selector.

## Parallel-field mechanism boundary

The printed parallel-field paragraph states that symmetry-allowed terms form a
continuously gapped QSH-to-trivial path but does not identify those terms. The
uniform edge Zeeman gap is directly supported. The old intervalley bridge is
kept only as a translation-breaking symmetry-class proxy. A second,
primitive-translation-preserving candidate built from the printed lattice
Rashba term, uniform in-plane Zeeman field and staggered sublattice mass is not
gapped: a continuous optimizer finds a direct closing of
`9.7e-17 t` in the mass-rotation segment. This is a successful falsification of
our candidate and an honest publication-underspecified boundary; it is neither
a reproduction-code defect nor sufficient evidence that the paper is wrong.

## Material-constant boundary

The first-star calculation gives 2.203 K using `a=2.46 angstrom`; the paper says
approximately 2.4 K but does not print the value of `a` used.  The electric-field
calculation gives 0.623 mK using `vF=1e6 m/s`; the paper says approximately
0.5 mK but does not print `vF`.  These are not code failures and are not promoted
to paper-exact claims.

## Manuscript cross-reference audit

Three references point to the next equation number: strip prose and the Fig. 1
caption say Eq. (7) where Eq. (6) is required, and the microscopic-SO paragraph
says Eq. (8) where Eq. (7) is required.  Their local formulas are unambiguous.
The v18 reviewer resolved the equation-number slips from their local formulas;
the separate `hbar`/`q` notation remains inconclusive. None meets the strict
paper-error-candidate gate.

## Execution and remaining lifecycle boundary

The v11 isolated run completed in 243.246548 s, produced 19 hash-frozen outputs,
recorded 666 file events and had zero denied/forbidden accesses. The v18 review
verified that the falsification bundle contains only the three v11 attestation
files and reconciled every reviewer/authored scope item. The case remains below
literal lifecycle completion because some claims cannot be paper-exact without
omitted publication parameters, external cited data/operators, or a specified
substrate/device model; this is an evidence boundary, not a failed run.
