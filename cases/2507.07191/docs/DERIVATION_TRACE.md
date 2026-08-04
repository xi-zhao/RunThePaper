# Derivation Trace

This trace covers the complete formula path from the paper to PRL-Bench idx 91.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until its formula dependencies are traceable and
the formula gate is not closed.

## Core object

The numerical object is a probability vector `p_i = |alpha_i|^2` on six
ordered energies. It minimizes expected energy subject to normalization and the
paper's stable-Schmidt-rank relaxation. The entire optimization reduces to one
strictly concave scalar dual function, so the result can be checked without a
large optimizer or GPU.

## Equation Cards

### EQ001 — stable-Schmidt-rank superposition constraint

- Source: `source publication material/main.tex:137-178`, Proposition 1 and Eq. `coefs_lower_bound`.
- Latex: `sum_i |alpha_i|/sqrt(M_i) >= 1/sqrt(m)`.
- Role: Defines the compression-feasible probability set after `p_i=|alpha_i|^2`.
- Steps: normalized states have `||Gamma||_F=1`; the spectral-norm triangle
  inequality and `chi(psi_i)>=M_i` give the stated lower bound.
- Numerical form: `sum_i sqrt(p_i/M_i) >= 1/sqrt(m)`.
- Code pointer: `code/src/compressed_spectrum.py::compression_value`.
- Status: verified from source.

### EQ002 — feasibility and the ground-only exclusion

- Source: Cauchy-Schwarz applied to EQ001; benchmark Task 1.
- Latex: `(sum_i sqrt(p_i/M_i))^2 <= sum_i 1/M_i`.
- Steps: the maximum compression value over the simplex is
  `sqrt(sum_i 1/M_i)` and occurs at `p_i proportional 1/M_i`. Feasibility is
  therefore equivalent to `sum_i 1/M_i >= 1/m`.
- Ground-only check: `p_1=1` gives `1/sqrt(M_1)=1/2 < 1/sqrt(2)`, so the optimum
  is strictly above `E_1=0`.
- Code pointer: `code/src/compressed_spectrum.py::feasibility_status`.
- Status: verified by exact rational arithmetic.

### EQ003 — scalar dual and stationarity equation

- Source: `source publication material/main.tex:205-239`, Proposition 2, Eqs. `dual` and
  `dual_optimum_condition`.
- Latex: `h(nu)=nu+[m sum_i 1/(M_i(E_i-nu))]^{-1}` for `nu<E_1`, with
  `S_2(nu)/m=S_1(nu)^2` at the optimum.
- Steps: convex duality eliminates the simplex variables; differentiating `h`
  gives `h'=1-S_2/(m S_1^2)`.
- Numerical form: bracket the unique sign change of `h'` and bisect at high
  precision.
- Code pointer: `code/src/compressed_spectrum.py::solve_dual_root`.
- Status: verified from source and differentiation.

### EQ004 — inverse-square optimum

- Source: Proposition 2, Eq. `inv_square`.
- Latex: `p_i proportional [M_i(E_i-nu*)^2]^{-1}`.
- Steps: compute positive weights `w_i`, normalize them, and verify both active
  constraints. All six weights are positive because `nu*<E_1<=E_i`.
- Code pointer: `code/src/compressed_spectrum.py::solve_spectrum`.
- Status: verified from source; direct constrained optimization is the
  independent numerical check.

### EQ005 — uniqueness and concavity

- Source: `source publication material/main.tex:610-655`, appendix proof of Proposition 2.
- Latex: `h''=-2(S_1 S_3-S_2^2)/(m S_1^3)<0`.
- Steps: Cauchy-Schwarz gives `S_2^2<S_1 S_3` when not all energies are equal;
  the nontriviality inequalities make `h'` positive at `-infinity` and negative
  at `E_1^-`. Hence exactly one root exists.
- Code pointer: `code/src/compressed_spectrum.py::dual_derivative`.
- Status: verified from source.

### EQ006 — energy and active residuals

- Source: Proposition 2 and benchmark Tasks 3-4.
- Latex: `E_min=sum_i p_i E_i=h(nu*)`.
- Checks: primal-dual equality, `sum_i p_i=1`, and
  `sum_i sqrt(p_i/M_i)=1/sqrt(m)`.
- Code pointer: `code/src/compressed_spectrum.py::solve_spectrum`.
- Status: verified derivation.

### EQ007 — support and non-exponential tail

- Source: Proposition 1 Eq. `refined_no_terms_lower_bound`; benchmark Tasks 5-6.
- Latex: `|supp(p)| >= ceil(H(M)/m)` and an exact exponential would require
  every adjacent `-(Delta log p)/(Delta E)` to equal the same positive `b`.
- Steps: EQ004 makes all six probabilities positive. The harmonic-mean bound is
  `ceil(6/(m sum_i 1/M_i))=6`; unequal log slopes exclude a single exponential.
- Code pointer: `code/src/compressed_spectrum.py::support_metrics` and
  `effective_log_slopes`.
- Status: verified by exact positivity and high-precision slopes.

### EQ008 — two-level coarse graining

- Source: `source publication material/main.tex:662-695`, appendix Eqs. `pmin` and `Emin`;
  benchmark Task 7 supplies the two groups.
- Latex: `m=(a1+mu a2)/(a1(a1+a2))` and
  `p=(a1+sqrt(mu)a2)^2/[(a1+a2)(a1+mu a2)]`.
- Steps: use exact `a1=13/36` and `a2=26581/176400`, solve the first equation
  algebraically for `mu`, then evaluate `p` at high precision.
- Code pointer: `code/src/compressed_spectrum.py::coarse_grained_solution`.
- Status: verified from source and exact rational aggregation.
