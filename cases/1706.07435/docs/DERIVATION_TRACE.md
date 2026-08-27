# Derivation Trace

Use this file for formula-heavy papers. Every implemented equation should map
back to a source equation or an explicit derivation step.

## Formula Lane Rule

Every formula used by numerical code must have:

- a card in `EQUATION_CARDS.json`;
- a human-readable derivation in this file;
- a formula gate result in `outputs/checks/formula_verification.json`;
- a code pointer, or a note that it is not used in code.

Do not open a numerical target until every dependency is independently checked.
`source_only` proves transcription, not understanding, and never authorizes a
numerical command. After generating `DERIVATION.md`, run the target through:

```bash
python PRAgent-workflow/scripts/run_target.py \
  case/<paper-id> <target-id> --stage exploratory -- python scripts/<runner>.py
```

## Core derivations

### EQC001 — why the four Chern numbers agree

On an overlap of two momentum-space patches, normalize the right state in two
gauges by `|R_II> = r exp(i f)|R_I>` and enforce `<L|R>=1`, which gives
`|L_II> = exp(i f)|L_I>/r`. The RR and LR Berry connections therefore differ
between patches by the same gauge gradient `i grad f`; LR has one additional
`grad log r`, whose closed-loop integral vanishes because `r` is single-valued.
Stokes' theorem makes both Chern integrals equal. Repeating the argument for
LL/RL and using the LR/RL conjugation relation proves
`N_LL=N_LR=N_RL=N_RR`. This is a derivation target, not a copied numerical plot.

### EQC002 — generalized Dirac spectrum and EP locations

Write `H=d·sigma` with
`d=(kx+i kappa_x, ky+i kappa_y, m+i delta)`. Pauli algebra gives
`H²=(d·d)I`, hence `E_±=±sqrt(d·d)`. Separating real and imaginary parts of
`d·d=0` produces a circle and a line in momentum space. Resolving the line into
components parallel and perpendicular to `n=kappa/|kappa|` yields the two
closed-form EP positions printed in the paper. The perpendicular component is
real only for `|m|<|kappa|`, which is the inseparable phase.

### EQC003 — domain-wall matching

For each constant-parameter half-space, substitute `psi∝exp(x/lambda)` into
the one-dimensional Dirac equation. The determinant condition gives Supp.
Eq. (10); equality of the two spinor component ratios gives Eq. (11). The
physical root pair must additionally satisfy `Re(1/lambda_+)>0` and
`Re(1/lambda_-)<0`.

The numerical solver does not need source pixels or an underdetermined visual
fit. Define, on side `i`,

```text
K_i = k_y + i kappa_{i,y},   M_i = m_i + i delta_i,
p_i = lambda_i^{-1} - kappa_{i,x}.
```

A common spinor on the two sides requires the difference of their two ansatz
Hamiltonians to be singular. Therefore

```text
(p_1-p_2)^2 = (K_1-K_2)^2 + (M_1-M_2)^2.
```

The two characteristic equations share the same energy,
`E^2=M_i^2+K_i^2-p_i^2`. Subtracting them gives

```text
p_1+p_2 = [(M_1-M_2)(M_1+M_2)
           +(K_1-K_2)(K_1+K_2)] / (p_1-p_2).
```

These sum-and-difference equations determine both inverse localization lengths;
the physical square-root branch is selected solely by their real-part signs.
The shared eigenvalue follows from the common one-dimensional null space, and
is checked against both characteristic polynomials and the original spinor
matching equation.

For Supplement Fig. 2, `m_1=-m_2=-m`, `delta_i=kappa_{i,x}=k_y=0`, so the
same algebra reduces to

```text
E = i m (kappa_{1,y}+kappa_{2,y})
    / sqrt[(2m)^2-(kappa_{1,y}-kappa_{2,y})^2].
```

It vanishes exactly on `kappa_{1,y}+kappa_{2,y}=0`, explaining the plotted
zero plane. Representative grid points also pass an independent nonlinear
root solve. The source edge curve and surface are never sampled.

### EQC004 — EP square-root dispersion and half winding

With the paper convention `sigma_+=sigma_x+i sigma_y`, the Fig. 2 Hamiltonian
has `E²=kx²+ky²+2kx+2i ky`. On the caption loop `k=(cos theta,sin theta)`,
the radicand is `1+2 exp(i theta)`, which winds once around zero. Its continuous
square root accumulates phase `pi`, so the two sheets exchange and the
energy-difference vorticity has magnitude `1/2`. The sign reverses with loop
orientation. At the origin the Hamiltonian is nonzero nilpotent, hence rank one
with only one eigenvector: the degeneracy is defective.

### EQC005 — square-lattice cylinder

Replace `sin kx` and `cos kx` by nearest-neighbour spinor hoppings along the
open direction, while retaining `ky` as a parameter. The onsite block is
`(sin ky+i kappa_y)sigma_y+(cos ky+m+i delta)sigma_z+i kappa_x sigma_x`;
the `x→x+1` block is `sigma_z/2 + sigma_x/(2i)` and the reverse block is
`sigma_z/2 - sigma_x/(2i)`. Fourier transforming an infinite chain recovers
Supp. Eq. (13), which fixes the sign convention before diagonalization.

### EQC006 — hybrid-point anisotropy

At `m=delta=1`, Supp. Eq. (20) gives
`E²=kx²+ky²+2i kx`. Along `ky=0`, the linear imaginary term makes
`|E|∝|kx|^(1/2)` close to the origin; along `kx=0`, `E=±|ky|` is linear.
The two distinct fitted exponents are the scientific feature behind Supp.
Fig. 4, independent of its 3D camera.

### EQC007 — codimension and defectiveness

For `H=aI+(b0+i b1)·sigma`, degeneracy requires both the real and imaginary
parts of `(b0+i b1)²` to vanish: `b0²=b1²` and `b0·b1=0`. These are two real
conditions. At a generic solution a rotation gives `H-aI=b sigma_+`, a nonzero
nilpotent rank-one matrix, so the algebraic multiplicity is two and geometric
multiplicity one.

## Formula lane status

All seven cards have source anchors and an independent algebraic or limiting
check. `outputs/checks/formula_verification.json` is the machine gate. All six
numerical targets now execute only after their formula and method gates pass.
