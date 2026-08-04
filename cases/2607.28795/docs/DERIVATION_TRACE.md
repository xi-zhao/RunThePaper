# Derivation Trace

## Input and independence lane

The only paper-specific inputs are the PDF, the SmallGroup IDs and zero-based
element indices printed in Tables VII/XIII, and scalar parameters printed in
the equations/tables. GAP 4.16.0 with SmallGrp 1.5.4, the exact versions cited
by the paper, supplies the standard finite-group multiplication law. It is not
an author implementation. The numerical runner receives a frozen
multiplication-table JSON and cannot read the PDF or author repository.

## Q001: from group algebra to CSS checks

For a finite group `G`, use the paper's conventions

`L(g)|h> = |g h>`, and `R(g)|h> = |h g^{-1}>`.

A ring element is a binary sum, so `L(g1+g2+g3)` is the XOR of the three
permutation matrices. The involution sends every support element to its group
inverse and therefore

`L(a*) = L(a)^T`, `R(a*) = R(a)^T`.

For the mitten `1 x 2` base matrices, Eq. (2) expands to two `|G|`-row check
blocks and five `|G|`-column data blocks for each Pauli type. Multiplying
`H_X H_Z^T` produces each left-right product twice. Left and right regular
actions commute, so those two copies are identical and cancel over `F_2`.
This yields an exact CSS commutation check rather than a visual structural
match.

## Q002-Q003: canonical logicals, dimension, and rate

The pivot entries `a1` and `b1` are required to be invertible. For every group
basis vector `e_g`, solve

`R(b1) u_g = R(b0) e_g`,

`L(a1) v_g = L(a0) e_g`.

The minus signs from moving a term across the equation disappear in `F_2`.
Then

`X_g = (e_g, u_g, 0, 0, 0)`,

`Z_g = (e_g, 0, v_g, 0, 0)`.

Substitution places `X_g` in `ker H_Z` and `Z_g` in `ker H_X`. Their only
shared data block is `D1`, so `X_g dot Z_h = delta_g,h`. These `|G|` conjugate
pairs prove at least `|G|` logical qubits. Independently computing the binary
ranks closes the count:

`n=5|G|`, `k=n-rank(H_X)-rank(H_Z)=|G|`, `k/n=1/5`.

All logicals in one basis are group translates, so their weights are uniform.
The independently computed weights `1+wt(u_e)` and `1+wt(v_e)` are compared
to Tables I/VI only after generation.

## Q004: parallel magic-state injection counts

Appendix E decomposes the qubits into the surface-code stack, Bridge I, magic
port, Bridge II, and the mitten code. Collecting the terms in Eq. (E15) gives

`n = (2 d_rep^2 + 2 d_rep + 5)|G|`,

`N_X = N_Z = (d_rep^2 + d_rep + 2)|G|`.

The identity `n-N_X-N_Z=|G|` is both an algebraic check and the expected
number of injected logical qubits. Evaluating the formulas for all eight group
orders and `d_rep in {5,7,9,11}` reproduces Table V without importing its
printed cells as data.

## Q005-Q006: bounded sQetch implementation

For one Pauli sector, build a basis `N` of the relevant check-matrix null
space. Each trial samples `kappa` basis rows with replacement, permutes the
`n` columns, reduces the sampled matrix to RREF, undoes the permutation on
each nonzero row, rejects stabilizer rows through the opposite null-space
basis, and retains the minimum Hamming weight.

Row reduction changes a basis but not the sampled span. Column permutation is
only an information-set randomization and is explicitly undone before the
logical test. A Steane `[[7,1,3]]` test supplies a known exact answer. The
paper's Fig. 8 workload uses about `10^12` trials and unspecified benchmark
matrices/hardware details; this case instead records a bounded measured
runtime and labels its output `reduced_scale`.

The probability that all `j*` basis rows needed for a fixed minimum logical
appear in `kappa` draws is the inclusion-exclusion expression in Eq. (H9).
Eqs. (H11)-(H13) add a generic-pivot approximation. We verify probability
bounds and monotonic trends but do not treat the approximation as an exact
property of every code.

## Q007: real-time arithmetic

At `T_cyc=1 ms`, a dedicated stage keeps up when

`rho_i = f_i t_i / T_cyc < 1`.

The mean reaction time is `t_bar=sum_i f_i t_i`, using the mean `S4` solve
time, while the separate worst `S4` row tests a conservative utilization.
Table X prints rounded fractions and times, so reconstructed values are tested
against the displayed `rho` and `t_bar` with an explicit rounding tolerance.
This target validates the paper's latency arithmetic, not the upstream
billion-shot estimates of the fractions `f_i`.

## Missing inputs and non-claims

- Exact hook-error-free schedules, optimized atom layouts, gadget graphs,
  merged codes, and HAL routing results are not present in the PDF.
- Fig. 2/9 and Table IX require enormous Monte Carlo workloads and additional
  circuit/decoder details.
- Fig. 8 does not state exact candidate matrices, all sketch sizes, random
  seeds, or the CPU model.
- Literal zero-based `Elements(SmallGroup(...))` interpretation at the cited
  GAP/SmallGrp versions makes both pivot blocks of the `(60,11)` row singular,
  contradicting Definition 4. It also produces canonical weights that differ
  from Table VI for some other rows. This is retained as a potential paper
  construction-data inconsistency, not repaired by inferring hidden parameters
  from the reported outputs.

None of these gaps authorizes reading the published author repository. They
remain visible blockers rather than being replaced with copied pixels or
printed result arrays.
