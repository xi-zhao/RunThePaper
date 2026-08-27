# Paper Map

## Identity

- Paper ID: `2607.15070`
- Title: *Casimir effect for a massive scalar field confined between parallel plates with a spatially varying effective mass*
- Authors: R. L. Araújo Xavier, M. H. B. Chaves, E. R. Bezerra de Mello, Herondy Mota
- Frozen version: arXiv:2607.15070v1
- Local PDF: `raw/paper.pdf`
- Local source: `paper-source.tar.gz`
- Trial extraction: `references/source_bundle/`

## Reproduction Goal

Reproduce every numerical curve in the paper from the displayed renormalized
proper-time integrals:

1. paper Fig. 2(a), the dimensionless Landau-like contribution;
2. paper Fig. 2(b), the dimensionless additional contribution;
3. paper Fig. 3, the ratio of total to Landau-like energy.

The four paper masses, plotted ranges, signs, limiting behavior, and relative
ordering are covered. Figure 1 is a geometric schematic and is explicitly
classified as non-numerical. There are no paper tables.

The case distinguishes two questions:

- the paper's plotted integral objects are independently evaluated and
  reproduced;
- the preceding field-theory derivation contains formula inconsistencies, so
  reproducing the plots does not validate the claimed spectrum as the spectrum
  of the action in Eq. (1).

## Paper Structure

| Section | Role | Notes |
| --- | --- | --- |
| I. Introduction | Physical motivation | Defines \(m_{\rm eff}^2=m^2+\alpha^2\rho^2\). |
| II. Klein-Gordon equation | Spectrum derivation | Eqs. (4)-(11); independent radial-operator check finds a factor-two discrepancy in Eq. (11). |
| III.A. Vacuum energy per area | Numerical object | Eqs. (25), (27), and (28) define the plotted dimensionless integrals. |
| III.A. Asymptotics | Scientific checks | Eqs. (31), (35), and (36); Eqs. (31) and (36) require corrected asymptotics. |
| IV. Conclusions | Claim summary | Suppression at strong coupling and Landau-sector dominance. |

## Equation/Method Inventory

| ID | Source location | Role | Status |
| --- | --- | --- | --- |
| EQC001 | Eqs. (6)-(11) | Correct radial oscillator eigenvalue and diagnose the paper factor-two discrepancy | verified |
| EQC002 | Eq. (25) | Dimensionless Landau-like energy used for Fig. 2(a) | verified conditional numerical object |
| EQC003 | Eq. (27) | Dimensionless additional energy used for Fig. 2(b) | verified conditional numerical object |
| EQC004 | Independent transform of Eqs. (25), (27) | Positive Bessel-series cross-check | verified |
| EQC005 | Eqs. (35), (36) | Correct small-\(\alpha_0\) limits | verified; Eq. (36) corrected |
| EQC006 | Eq. (31) | Correct strong-\(\alpha_0\) asymptotic | verified; printed exponent corrected |
| EQC007 | Eq. (28) and Fig. 3 definition | Energy ratio | verified |
| MTH001 | Numerical reconstruction | Log-proper-time quadrature with Poisson-resummed plate sum | verified |

## Figure/Table Inventory

| Item | Caption summary | Class | Decision |
| --- | --- | --- | --- |
| FIG001 (paper Fig. 1) | Two parallel plates of area \(A\), separation \(L\) | `schematic_context` | excluded from numerical targets |
| FIG002A (paper Fig. 2 left) | \(8\pi^2L^3E_L^{\rm ren}/A\) vs. \(\alpha_0\), four \(m_0\) values | `numeric_reproduction` | target T001 |
| FIG002B (paper Fig. 2 right) | \(8\pi^2L^3E_c^{\rm ren}/A\) vs. \(\alpha_0\), four \(m_0\) values | `numeric_reproduction` | target T001 |
| FIG003 (paper Fig. 3) | \(E_0^{\rm ren}/E_L^{\rm ren}\) vs. \(\alpha_0\), four \(m_0\) values | `numeric_reproduction` | target T002 |
| Tables | None | not applicable | no table targets |

## Paper-Exact Parameters

- \(m_0=mL\in\{0,0.5,1,1.5\}\).
- Fig. 2(a): \(\alpha_0=\alpha L^2\) axis from 0 to 30.
- Fig. 2(b): \(\alpha_0\) axis from 0 to 12; the singular endpoint is
  approached from positive \(\alpha_0\).
- Fig. 3: \(\alpha_0\) axis from 0 to 25; the singular endpoint is approached
  from positive \(\alpha_0\).
- The vector source figures are reference-only and are never used to generate
  numerical values.

## Assumptions And Scientific Boundary

- Natural units \(\hbar=c=1\) are used.
- The numerical target is the boundary-induced term remaining after the
  paper's stated subtraction prescription.
- The plotted integrals are evaluated as definitions conditional on that
  prescription.
- Direct substitution of the regular radial ground state into the operator
  derived from Eqs. (4)-(6) gives \(\lambda_{0,0}=2\alpha\), while paper
  Eq. (11) gives \(\alpha\). This case does not conceal that discrepancy.
- Paper Eq. (27)'s first line contains \(\alpha\tau^2\) after the
  \(\tau\mapsto L\tau\) rescaling; dimensional consistency requires
  \(\alpha_0\tau^2\), which is what the code evaluates.
- Reference PDFs are used only for captions, axes, styles, and pixel
  comparison, never as generated data.
